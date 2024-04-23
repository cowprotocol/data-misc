from duneapi.api import DuneAPI
from duneapi.types import DuneQuery, Network
from duneapi.util import open_query


def fetch_eth_spent(dune: DuneAPI) -> None:
    """
    Fetches ETH spent on CIP-9 Fee subsidies
    https://snapshot.org/#/cow.eth/proposal/0x4bb9b614bdc4354856c4d0002ad0845b73b5290e5799013192cbc6491e6eea0e
    """
    query = DuneQuery.from_environment(
        raw_sql=open_query("./queries/blockwise-discount-factors.sql"),
        name="ETH Spent on Fee Discounts",
        network=Network.MAINNET,
        parameters=[],
    )
    results = dune.fetch(query)
    print(results)


if __name__ == "__main__":
    dune_conn = DuneAPI.new_from_environment()
    print("Getting ETH Spent on Fee subsidies from: https://dune.com/queries/529638")
    fetch_eth_spent(dune_conn)
