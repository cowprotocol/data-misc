import json
import os
from collections import defaultdict
from typing import Optional, Any

from dotenv import load_dotenv
from web3 import Web3

from src.constants import PUBLIC_RESOLVER_ABI
from src.subgraph.fetch import execute_subgraph_query
from src.utils import partition_array

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"

RELEVANT_FIELDS = {
    "email",
    "url",
    "com.discord",
    "com.github",
    "com.reddit",
    "com.twitter",
    "org.telegram",
}

load_dotenv()
w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{os.environ['INFURA_KEY']}"))


def read_ens_text(resolver: str, node: str, key: str) -> str:
    resolver_contract = w3.eth.contract(
        address=Web3.toChecksumAddress(resolver), abi=PUBLIC_RESOLVER_ABI
    )

    text: str = resolver_contract.caller.text(node, key)
    return text


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
            address
            texts
        }}
      }}
    }}
    """


WalletNameMap = dict[str, list[dict[str, dict[Any, Any]]]]


def get_wallet_ens_data(
    wallet_set: set[str], block: Optional[int] = None
) -> WalletNameMap:
    results: WalletNameMap = {}
    partition = partition_array(list(wallet_set), 500)
    for part in partition:
        results.update(get_names_for_wallets_small(set(part), block))
    return results


def get_result_page(wallets: list[str], skip: int, block: Optional[int] = None) -> Any:
    result_json = execute_subgraph_query(
        subgraph_url="https://api.thegraph.com/subgraphs/name/ensdomains/ens",
        query=resolve_query(list(wallets), skip, block),
    )
    return result_json["data"]["domains"]


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
            resolver = rec["resolver"]["address"]
            if texts and not set(texts).isdisjoint(RELEVANT_FIELDS):
                rich_text = {}
                for text in texts:
                    rich_text[text] = read_ens_text(resolver, ens_id, text)
                results[wallet].append({name: {"id": ens_id, "texts": rich_text}})
        skip += 100
        result_dict = get_result_page(wallets, skip)
    return results
