#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from typing import List
from datetime import datetime

import click
import duneapi.api
from dotenv import load_dotenv
from dune_client.client import DuneClient
from dune_client.models import ResultsResponse
from dune_client.query import Query
from dune_client.types import QueryParameter
import pandas as pd
from tqdm import tqdm


@click.command()
@click.option("--query", "-q", multiple=True)
@click.option("--start-date", "-s", type=click.DateTime(formats=["%Y-%m-%d"]))
def main(query: List[str], start_date: datetime):
    monthly_reporting(query, start_date)
    return 0


def store_results(results: List[ResultsResponse], start_date: datetime):
    writer = pd.ExcelWriter(
        f'out/{"_".join([str(x.query_id) for x in results])}_{start_date.strftime("%Y-%m-%d")}.xlsx',
        engine="xlsxwriter",
    )
    for result in results:
        pd.DataFrame(pd.DataFrame(result.result.rows)).to_excel(
            writer, sheet_name=f"{result.query_id}", index=False
        )
    writer.close()


def fetch_results(queries: List[str], start_date: datetime) -> List[ResultsResponse]:
    dune_client: DuneClient = DuneClient(os.environ["DUNE_API_KEY"])
    results: List[ResultsResponse] = []
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
    results = fetch_results(queries, start_date)
    store_results(results, start_date)


if __name__ == "__main__":
    load_dotenv()
    main()
