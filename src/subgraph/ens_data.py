import json
from collections import defaultdict

from src.subgraph.fetch import execute_subgraph_query
from src.utils import partition_array

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"


def resolve_query(wallet_list: list[str], skip: int) -> str:
    """
    Constructs and query to fetch ens names for a list of ethereum addresses
    """
    assert all(w == w.lower() for w in wallet_list), "Addresses must be lower case!"
    return f"""
    {{
      domains(
        where: {{
            resolvedAddress_in: {json.dumps(wallet_list)}
        }},
        skip: {skip}
      ) {{
        name
        resolvedAddress {{
          id
        }}
      }}
    }}
    """


WalletNameMap = dict[str, list[str]]


def get_names_for_wallets(wallet_set: set[str]) -> WalletNameMap:
    results: WalletNameMap = {}
    partition = partition_array(list(wallet_set), 1000)
    for part in partition:
        results.update(get_names_for_wallets_small(set(part)))
    return results


def get_result_page(wallets, skip):
    result_json = execute_subgraph_query(
        subgraph_url="https://api.thegraph.com/subgraphs/name/ensdomains/ens",
        query=resolve_query(list(wallets), skip),
    )
    return result_json["data"]["domains"]


def get_names_for_wallets_small(wallet_set: set[str]) -> WalletNameMap:
    wallets = list(wallet_set)
    results = defaultdict(list)
    skip = 0
    result_dict = get_result_page(wallets, skip)
    while len(result_dict) > 0:
        for rec in result_dict:
            results[rec["resolvedAddress"]["id"]].append(rec["name"])
        skip += 100
        result_dict = get_result_page(wallets, skip)
    return results
