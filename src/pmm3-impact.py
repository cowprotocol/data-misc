"""
Slippage/Volume Query is here: https://dune.com/queries/1155796
Results have been manually inserted here: https://dune.com/queries/1156024
"""

from datetime import datetime, timedelta

from duneapi.api import DuneAPI
from duneapi.types import DuneRecord, QueryParameter

slippage_query = 1155796


class AccountingPeriod:
    """Class handling the date arithmetic and string conversions for date intervals"""

    def __init__(self, start: datetime, length_days: int = 7):
        self.start = start
        self.end = self.start + timedelta(days=length_days)

    def __str__(self) -> str:
        return "-to-".join(
            [self.start.strftime("%Y-%m-%d"), self.end.strftime("%Y-%m-%d")]
        )


def week_range(start: datetime, num_weeks: int) -> list[AccountingPeriod]:
    results = []
    curr = start
    for i in range(num_weeks):
        period = AccountingPeriod(curr)
        results.append(period)
        curr = period.end

    return results


def refresh(dune, query_id: int, parameters: list[QueryParameter]) -> list[DuneRecord]:
    job_id = dune.execute(query_id, parameters)
    return dune.get_results(job_id)


def generate_weekly_slippage_ratio(dune: DuneAPI, start: datetime, num_weeks: int):

    for period in week_range(start, num_weeks):
        results = refresh(
            dune,
            query_id=slippage_query,
            parameters=[
                QueryParameter.date_type("StartTime", period.start),
                QueryParameter.date_type("EndTime", period.end),
                QueryParameter.text_type(
                    "Solver", "0xb20b86c4e6deeb432a22d773a221898bbbd03036"
                ),
            ],
        )
        print(period, results)


if __name__ == "__main__":
    generate_weekly_slippage_ratio(
        dune=DuneAPI.new_from_environment(),
        start=datetime.strptime("2022-07-01", "%Y-%m-%d"),
        num_weeks=6,
    )
