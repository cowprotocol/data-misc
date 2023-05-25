import os

import pandas as pd
from dune_client.client import DuneClient
from dune_client.query import Query

from src.fetch.orderbook import OrderbookFetcher

ORDER_FILL_TIME_QUERY = Query(1905233)

if __name__ == "__main__":
    dune = DuneClient(os.environ["DUNE_API_KEY"])
    db_fetcher = OrderbookFetcher()

    creation_times = pd.DataFrame(db_fetcher.get_order_creations())
    fill_times = pd.DataFrame(dune.refresh(ORDER_FILL_TIME_QUERY).get_rows())
    result = pd.merge(fill_times, creation_times, left_on='order_uid',right_on='uid', how='inner')
    # result = pd.read_csv('data.csv', index_col=0)
    # result.to_csv('data.csv')
    result['settlement_time']= result['fill_time'] - result['creation_time']
    result['date'] = pd.to_datetime(result['fill_time'],unit='s')
    result['month'] = pd.to_datetime(result['date']).astype(str).str[:7]
    result['year'] = pd.to_datetime(result['date']).astype(str).str[:4]
    g = result.groupby(['month']).quantile(0.5)
    print("Monthly execution speeds:")
    print(g)
    h = result.groupby(['year']).quantile(0.5)
    print("yearly execution speeds:")
    print(h)
