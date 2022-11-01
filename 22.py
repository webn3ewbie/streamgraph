import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from datetime import datetime
from subgrounds.subgrounds import Subgrounds
from metrics import MetricsDailySnapshots
from streamlit_echarts import st_pyecharts
from utils import *
from config import *

from CustomCharts import CustomLineChart, CustomBarChart, CustomPieChart


class MetricsDailySnapshots:
    def __init__(self, subgraph, subground, initial_timestamp):
        self.subgraph = subgraph
        self.subground = subground
        self.timestamp = initial_timestamp

        self.dataframe = self.query()

    def query(self):
        metrics_daily_snapshot = self.subgraph.Query.usageMetricsDailySnapshots(
            first=1000,
            where=[self.subgraph.UsageMetricsDailySnapshot.timestamp > self.timestamp],
        )

        dataframe = self.subground.query_df([metrics_daily_snapshot])

        return dataframe

    def transactions_count_chart(self):
        chart = CustomBarChart(
            chart_title="Transactions",
            xaxis_name="UTC",
            yaxis_name="Count Of Transactions",
            logo_position=130
        )

        xaxis_data = format_xaxis(self.dataframe.usageMetricsDailySnapshots_id)

        chart.add_xaxis_bar_chart(xaxis_data=xaxis_data)
        chart.add_xaxis_line_chart(xaxis_data=xaxis_data)

        chart.add_yaxis_bar_chart(
            series_name="Daily Deposit Count",
            color="#5a66f9",
            yaxis_data=self.dataframe.usageMetricsDailySnapshots_dailyDepositCount.round(
                1
            ).to_list(),
        )
        chart.add_yaxis_bar_chart(
            series_name="Daily Withdraw Count",
            color="#6ac5c8",
            yaxis_data=self.dataframe.usageMetricsDailySnapshots_dailyWithdrawCount.round(
                1
            ).to_list(),
        )
        chart.add_yaxis_bar_chart(
            series_name="Daily Swap Count",
            color="#F2AA4CFF",
            yaxis_data=self.dataframe.usageMetricsDailySnapshots_dailySwapCount.round(
                1
            ).to_list(),
        )

        chart.extend_axis(name="Total Daily Transactions")

        chart.add_yaxis_line_chart(
            series_name="Daily Total Transactions",
            color="#fc03f8",
            yaxis_data=self.dataframe.usageMetricsDailySnapshots_dailyTransactionCount.round(
                1
            ).to_list(),
        )

        return chart.BAR_CHART.overlap(chart.LINE_CHART)

    def active_users_chart(self):
        chart = CustomLineChart(
            chart_title="Active Users",
            xaxis_name="UTC",
            yaxis_name="Count Of Users",
            logo_position=135
        )

        # x_axis --> timestamp
        chart.add_xaxis(format_xaxis(self.dataframe.usageMetricsDailySnapshots_id))

        # y_axis -->
        chart.add_yaxis(
            color="#12b8ff",
            series_name="Daily Active Users",
            yaxis_data=self.dataframe.usageMetricsDailySnapshots_dailyActiveUsers.round(
                1
            ).to_list(),
        )

        return chart.LINE_CHART
# Refresh every 10 seconds
REFRESH_INTERVAL_SEC = 0

sg = Subgrounds()
subgraphs = {
    "balancer-v2-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/dorgtech/balancer-v2-polygon"
    ),
    "uniswap-v3-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/steegecs/uniswap-v3-polygon"
    ),
    "quick-swap-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/quickswap-polygon"
    ),
    "sushi-swap-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-polygon"
    ),
}


def fetch_data(subgraph, amount_in_usd_gte):
    print(subgraph)
    latest_swaps = subgraph.Query.swaps(
        where=[subgraph.Swap.amountInUSD >= amount_in_usd_gte],
        orderBy=subgraph.Swap.timestamp,
        orderDirection="desc",
        first=10,
    )
    df = sg.query_df(
        [
            latest_swaps.hash,
            latest_swaps.protocol.name,
            latest_swaps.protocol.network,
            latest_swaps.timestamp,
            latest_swaps.tokenIn.symbol,
            latest_swaps.amountInUSD,
            latest_swaps.tokenOut.symbol,
            latest_swaps.amountOutUSD,
        ]
    )
    df = df.rename(columns=lambda x: x[len("swaps_") :])
    df["time"] = df["timestamp"].apply(
        lambda x: datetime.fromtimestamp(x).strftime("%H:%M:%S")
    )
    df["dex"] = df["protocol_name"]
    df["network"] = df["protocol_network"]

    df["amountInUSD"] = df["amountInUSD"].map("{:,.2f}".format)
    df["amountOutUSD"] = df["amountOutUSD"].map("{:,.2f}".format)
    df["swap"] = df.apply(
        lambda x: f"""\${x["amountInUSD"]} {x["tokenIn_symbol"]} 💸 \${x["amountOutUSD"]} {x["tokenOut_symbol"]}""",
        axis=1,
    )
    df["txn"] = df.apply(
        lambda x: f"""[🔗](https://polygonscan.com/tx/{x["hash"]})""",
        axis=1,
    )
    return df[["time", "dex", "network", "swap", "txn"]]


st.set_page_config(page_icon="📈")
ticker = st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="ticker")
st.title("📈 PolyGraph")
st.header("Your one-stop shop to get insights into your Defi user data")

networks = st.selectbox(
    "Select networks",
    ["balancer-v2-polygon", "uniswap-v3-polygon", "sushi-swap-polygon", "quick-swap-polygon"]
)

MetricsSnapshot = MetricsDailySnapshots(subgraphs.get(networks), sg, initial_timestamp=1601322741)

with st.container():
    st_pyecharts(
        chart=MetricsSnapshot.transactions_count_chart(),
        height="450px",
        key="TransactionChart",
    )

with st.container():
    st_pyecharts(
        chart=MetricsSnapshot.active_users_chart(),
        height="450px",
        key="ActiveUsersChart",
    )

amount_in_usd_gte = st.select_slider(
    "Only display swaps with amount >=",
    value=100,
    options=[100, 1000, 10000, 100000],
    key="amount_in_usd_gte",
)

data_loading = st.text(f"[Every {REFRESH_INTERVAL_SEC} seconds] Loading data...")
df = fetch_data(subgraphs[networks], amount_in_usd_gte)
df = df.sort_values(by=["time"], ascending=False)
data_loading.text(f"[Every {REFRESH_INTERVAL_SEC} seconds] Loading data... done!")
st.markdown(df.to_markdown())
