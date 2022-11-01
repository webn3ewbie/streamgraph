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
