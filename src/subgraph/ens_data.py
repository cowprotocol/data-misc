import json
from collections import defaultdict

from src.subgraph.fetch import execute_subgraph_query

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"


def resolve_query(wallet_list: list[str]) -> str:
    """
    Constructs and query to fetch ens names for a list of ethereum addresses
    """
    assert all(w == w.lower() for w in wallet_list), "Addresses must be lower case!"
    return f"""
    {{
      domains(
        where: {{
            resolvedAddress_in: {json.dumps(wallet_list)}
        }}
      ) {{
        name
        resolvedAddress {{
          id
        }}
      }}
    }}
    """


WalletNameMap = dict[str, list[str]]


def get_names_for_wallets(wallet_list: list[str]) -> WalletNameMap:
    result_json = execute_subgraph_query(
        subgraph_url="https://api.thegraph.com/subgraphs/name/ensdomains/ens",
        query=resolve_query(wallet_list)
    )
    results = defaultdict(list)
    for rec in result_json["data"]["domains"]:
        results[rec["resolvedAddress"]["id"]].append(rec["name"])
    return results

