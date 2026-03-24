# CS 498 Homework 3

This project contains the required files for Homework 3:

- `app.py`: Flask API using PyMongo read preferences and write concerns.
- `load_data.py`: Batch CSV loader for the EV dataset.
- `benchmark.py`: Simple latency benchmark for `/insert-fast` and `/insert-safe`.
- `Design.pdf`: Design write-up for Part 1 and Part 4.
- `Team.txt`: Replace with your NetID.
- `HW3.txt`: Replace with your VM external IP and port.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `MONGODB_URI` in `.env` to your MongoDB Atlas connection string.

## Load the dataset

```bash
python3 load_data.py --csv-file Electric_Vehicle_Population_Data.csv --drop
```

## Run the API

```bash
python3 app.py
```

## Benchmark writes

```bash
python3 benchmark.py --base-url http://YOUR_VM_IP:5000
```

Paste the reported averages into `Design.md`, then regenerate `Design.pdf` if you edit the document.
