import argparse
import csv
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


INT_FIELDS = {
    "Model Year",
    "Electric Range",
    "Base MSRP",
    "Legislative District",
    "2020 Census Tract",
    "DOL Vehicle ID",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the EV CSV into MongoDB Atlas in batches."
    )
    parser.add_argument("--csv-file", required=True, help="Path to the EV CSV file.")
    parser.add_argument("--uri", default=None, help="MongoDB connection string.")
    parser.add_argument("--database", default="ev_db", help="Database name.")
    parser.add_argument("--collection", default="vehicles", help="Collection name.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of rows per insert_many batch.",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop the target collection before loading data.",
    )
    return parser.parse_args()


def clean_value(field: str, value: str) -> Any:
    if value is None:
        return None

    value = value.strip()
    if value == "":
        return None

    if field in INT_FIELDS:
        try:
            return int(float(value))
        except ValueError:
            return value

    return value


def clean_row(row: dict[str, str]) -> dict[str, Any]:
    return {field: clean_value(field, value) for field, value in row.items()}


def insert_batch(collection, batch: list[dict[str, Any]]) -> int:
    if not batch:
        return 0
    result = collection.insert_many(batch, ordered=False)
    return len(result.inserted_ids)


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file does not exist: {csv_path}")

    uri = args.uri
    if not uri:
        from os import getenv

        uri = getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MongoDB URI not provided. Use --uri or set MONGODB_URI.")

    client = MongoClient(uri)
    collection = client[args.database][args.collection]

    if args.drop:
        collection.drop()

    inserted_count = 0
    batch: list[dict[str, Any]] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            batch.append(clean_row(row))
            if len(batch) >= args.batch_size:
                inserted_count += insert_batch(collection, batch)
                batch = []

    inserted_count += insert_batch(collection, batch)

    collection.create_index("Make")
    collection.create_index("City")
    collection.create_index("Model Year")

    print(f"Inserted {inserted_count} documents into {args.database}.{args.collection}")


if __name__ == "__main__":
    main()
