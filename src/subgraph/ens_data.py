import json
from collections import defaultdict
from typing import Optional

from src.subgraph.fetch import execute_subgraph_query
from src.utils import partition_array

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"


def resolve_query(
    wallet_list: list[str], skip: int, block: Optional[int] = None
) -> str:
    """
    Constructs and query to fetch ens names for a list of ethereum addresses
    """
    assert all(w == w.lower() for w in wallet_list), "Addresses must be lower case!"
    block_constraint = f"block: {{number: {block}}}" if block else ""
    return f"""
    {{
      domains(
        where: {{
            resolvedAddress_in: {json.dumps(wallet_list)}
        }},
        skip: {skip},
        {block_constraint}
      ) {{
        name
        id
        resolvedAddress {{
          id
        }}
        resolver {{
            texts
        }}
      }}
    }}
    """


WalletNameMap = dict[str, list[str]]


def get_names_for_wallets(
    wallet_set: set[str], block: Optional[int] = None
) -> WalletNameMap:
    results: WalletNameMap = {}
    partition = partition_array(list(wallet_set), 1000)
    for part in partition:
        results.update(get_names_for_wallets_small(set(part), block))
    return results


def get_result_page(wallets, skip, block: Optional[int] = None):
    result_json = execute_subgraph_query(
        subgraph_url="https://api.thegraph.com/subgraphs/name/ensdomains/ens",
        query=resolve_query(list(wallets), skip, block),
    )
    return result_json["data"]["domains"]


RELEVANT_FIELDS = {
    "email",
    "url",
    "com.discord",
    "com.github",
    "com.reddit",
    "com.twitter",
    "org.telegram",
}


def get_names_for_wallets_small(
    wallet_set: set[str], block: Optional[int] = None
) -> WalletNameMap:
    wallets = list(wallet_set)
    results = defaultdict(list)
    skip = 0
    result_dict = get_result_page(wallets, skip, block)
    while len(result_dict) > 0:
        for rec in result_dict:
            wallet, name = rec["resolvedAddress"]["id"], rec["name"]
            texts, ens_id = rec["resolver"]["texts"], rec["id"]
            if texts and not set(texts).isdisjoint(RELEVANT_FIELDS):
                # print(f"wallet {wallet} with name {name} has fields {texts}")
                results[wallet].append({name: {"id": ens_id, "texts": texts}})
        skip += 100
        result_dict = get_result_page(wallets, skip)
    return results
