import argparse
import json
import time
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark /insert-fast and /insert-safe with 50 requests each."
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL such as http://34.123.45.67:5000",
    )
    parser.add_argument(
        "--payload-file",
        default=None,
        help="Optional JSON file used as the insert payload template.",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=50,
        help="Number of requests per endpoint.",
    )
    return parser.parse_args()


def load_payload(payload_file: str | None) -> dict:
    if payload_file:
        return json.loads(Path(payload_file).read_text(encoding="utf-8"))
    return {
        "VIN (1-10)": "BENCHMARK01",
        "County": "Cook",
        "City": "Chicago",
        "State": "IL",
        "Postal Code": "60601",
        "Model Year": 2026,
        "Make": "TESLA",
        "Model": "Model 3",
        "Electric Vehicle Type": "Battery Electric Vehicle (BEV)",
        "CAFV Eligibility": "Clean Alternative Fuel Vehicle Eligible",
        "Electric Range": 333,
        "Base MSRP": 42000,
    }


def post_json(url: str, payload: dict) -> float:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as response:
        response.read()
    end = time.perf_counter()
    return end - start


def benchmark_endpoint(base_url: str, endpoint: str, payload: dict, count: int) -> float:
    durations = []
    for i in range(count):
        request_payload = dict(payload)
        request_payload["benchmark_request_id"] = f"{endpoint}-{i}-{time.time_ns()}"
        durations.append(post_json(f"{base_url}{endpoint}", request_payload))
    return sum(durations) / len(durations)


def main() -> None:
    args = parse_args()
    payload = load_payload(args.payload_file)

    fast_avg = benchmark_endpoint(args.base_url, "/insert-fast", payload, args.requests)
    safe_avg = benchmark_endpoint(args.base_url, "/insert-safe", payload, args.requests)

    print(f"Average /insert-fast latency: {fast_avg * 1000:.2f} ms")
    print(f"Average /insert-safe latency: {safe_avg * 1000:.2f} ms")


if __name__ == "__main__":
    main()
