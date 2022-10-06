import argparse
import datetime
from enum import Enum

from dotenv import load_dotenv
from duneapi.api import DuneAPI
from duneapi.types import DuneQuery, Network, QueryParameter
from duneapi.util import open_query

from src.subgraph.ens_data import get_names_for_wallets
from src.utils import write_to_json, valid_date

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ensdomains/ens"


class RetentionCategory(Enum):
    """Various user types by retention category"""

    LOST = "lost"
    HYBRID = "hybrid"
    GONE = "gone"
    RETAINED = "retained"

    def __str__(self) -> str:
        return str(self.value)


def fetch_retained_users(
    dune: DuneAPI, category: RetentionCategory, day: datetime, cache: set[str]
):
    """
    Fetches ETH spent on CIP-9 Fee subsidies
    https://snapshot.org/#/cow.eth/proposal/0x4bb9b614bdc4354856c4d0002ad0845b73b5290e5799013192cbc6491e6eea0e
    """
    print(f"Fetching wallets for {category} users on {day.date()}...")
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
    wallets = set(rec["trader"].lower() for rec in dune.fetch(query))
    new_wallets = wallets - cache
    print(f"Got {len(wallets)} results - {len(new_wallets)} of which were new")
    ens_map = get_names_for_wallets(new_wallets)
    print(f"Matched {len(ens_map)} wallets to names")
    # for matched_wallet, names in ens_map.items():
    #     print(matched_wallet, names)

    return ens_map


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--start",
        help="The Start Date - format YYYY-MM-DD",
        required=True,
        type=valid_date,
    )
    parser.add_argument(
        "-c",
        "--category",
        type=RetentionCategory,
        choices=list(RetentionCategory),
        help=f"Retention category to query from. Can be any of {list(RetentionCategory)}",
    )
    args = parser.parse_args()

    start = args.start
    category = args.category

    end = start + datetime.timedelta(days=7)
    cur_day = start
    results = {}
    while cur_day < end:
        results.update(
            fetch_retained_users(
                dune=DuneAPI.new_from_environment(),
                day=cur_day,
                category=category,
                cache=set(results.keys()),
            )
        )
        cur_day += datetime.timedelta(days=1)

    write_to_json(
        results, path="./out", filename=f"{category}-week-{start.date()}.json"
    )
