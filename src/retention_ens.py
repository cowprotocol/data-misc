import datetime
from enum import Enum

from duneapi.api import DuneAPI
from duneapi.types import DuneQuery, Network, QueryParameter
from duneapi.util import open_query

from src.subgraph.ens_data import get_names_for_wallets
from src.subgraph.fetch import execute_subgraph_query


SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"


class RetentionCategory(Enum):
    """Various user types by retention category"""

    LOST = "lost"
    HYBRID = "hybrid"
    GONE = "gone"
    RETAINED = "retained"

    def __str__(self) -> str:
        return str(self.value)


def fetch_retained_users(dune: DuneAPI, category: RetentionCategory, day: datetime):
    """
    Fetches ETH spent on CIP-9 Fee subsidies
    https://snapshot.org/#/cow.eth/proposal/0x4bb9b614bdc4354856c4d0002ad0845b73b5290e5799013192cbc6491e6eea0e
    """
    query = DuneQuery.from_environment(
        raw_sql=open_query("./queries/retention-on-date.sql"),
        name=f"{category} users",
        network=Network.MAINNET,
        parameters=[
            QueryParameter.date_type("DateFor", day),
            QueryParameter.enum_type(
                "TraderType", str(category), [str(c) for c in RetentionCategory]
            ),
            QueryParameter.number_type("NumDays", 30),
        ],
    )
    wallets = [rec["trader"].lower() for rec in dune.fetch(query)]
    print(f"Got {len(wallets)} results for {category} users on {day}")
    ens_map = get_names_for_wallets(wallets)
    print(f"Matched {len(ens_map)} wallets to names")
    for matched_wallet, names in ens_map.items():
        print(matched_wallet, names)


if __name__ == "__main__":

    fetch_retained_users(
        dune=DuneAPI.new_from_environment(),
        day=datetime.datetime(2022, 9, 1),
        category=RetentionCategory.HYBRID,
    )
