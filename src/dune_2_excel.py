import os
from typing import List, Any
from datetime import datetime

import click
from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.models import ResultsResponse
from dune_client.query import QueryBase as Query
from dune_client.types import QueryParameter
import pandas as pd
from tqdm import tqdm

from src.constants import PROJECT_ROOT


@click.command()
@click.option("--query", "-q", "queries_", multiple=True)
@click.option("--start-date", "-s", type=click.DateTime(formats=["%Y-%m-%d"]))
def main(queries_: List[str], start_date: datetime) -> Any:
    """
    Main function of the script
    Args:
        queries_: List of queries to fetch
        start_date: start_date query parameter

    Returns:

    """
    monthly_reporting(queries_, start_date)
    return 0


def store_results(results: List[ResultsResponse], start_date: datetime) -> None:
    """
    Store results into xlsx file
    Args:
        results: results to be stored
        start_date: start_date query parameter
    """
    writer = pd.ExcelWriter(  # pylint: disable=abstract-class-instantiated
        PROJECT_ROOT / f'out/{"_".join([str(x.query_id) for x in results])}'
        f'_{start_date.strftime("%Y-%m-%d")}.xlsx',
        engine="xlsxwriter",
    )
    for result in results:
        pd.DataFrame(result.get_rows()).to_excel(
            writer, sheet_name=f"{result.query_id}", index=False
        )
    writer.close()


def fetch_results(queries: List[str], start_date: datetime) -> List[ResultsResponse]:
    """
    Fetches results from Dune
    Args:
        queries: List of queries to fetch
        start_date: start_date query parameter

    Returns:
        List[ResultsResponse]
    """
    dune_client: DuneClient = DuneClient(os.environ["DUNE_API_KEY"])
    results: List[ResultsResponse] = []
    # TODO: Make fetching of queries asynchronous #24
    for q in tqdm(queries):
        query = Query(
            name="",
            query_id=int(q),
            params=[QueryParameter.date_type("StartTime", start_date)],
        )
        result = dune_client.refresh(query)
        results.append(result)

    return results


def monthly_reporting(queries: List[str], start_date: datetime) -> None:
    """
    Fetches and stores results from list of input queries.
    Args:
        queries: List of queries to fetch
        start_date: start_date query parameter
    """
    results = fetch_results(queries, start_date)
    store_results(results, start_date)


if __name__ == "__main__":
    load_dotenv()
    main()
