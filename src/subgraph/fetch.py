from typing import Any

import requests


def execute_subgraph_query(subgraph_url: str, query: str) -> Any:
    """
    Executes subgraph query for a given url.
    :param subgraph_url: URL of subgraph to be queried
    :param query: Graph QL Query
    :return: results of the query.
    """
    response = requests.post(url=subgraph_url, json={"query": query, "variables": None})
    return response.json()
