import argparse
import json
import os
from datetime import datetime


def partition_array(arr: list[any], size: int) -> list[list[any]]:
    return [arr[i : i + size] for i in range(0, len(arr), size)]


def write_to_json(results: dict[any, any], path: str, filename: str):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)
        print(f"Results written to {filename}")


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)
