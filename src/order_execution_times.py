import os

import pandas as pd
from dune_client.client import DuneClient
from dune_client.query import Query

from src.fetch.orderbook import OrderbookFetcher

ORDER_FILL_TIME_QUERY = Query(1905233)

if __name__ == "__main__":
    dune = DuneClient(os.environ["DUNE_API_KEY"])
    db_fetcher = OrderbookFetcher()

    creation_times = db_fetcher.get_order_creations()
    print(f"Creation Time Records, {len(creation_times)}")

    fill_times = pd.DataFrame(dune.refresh(ORDER_FILL_TIME_QUERY).get_rows())
    print(f"Fill Time Records, {len(fill_times)}")
