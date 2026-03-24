import os
from typing import Any

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern


load_dotenv()

app = Flask(__name__)


def get_client() -> MongoClient:
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise RuntimeError("MONGODB_URI is not set.")
    return MongoClient(mongodb_uri)


def get_collection():
    client = get_client()
    db_name = os.getenv("MONGODB_DB", "ev_db")
    collection_name = os.getenv("MONGODB_COLLECTION", "vehicles")
    return client[db_name][collection_name]


def normalize_document(data: dict[str, Any]) -> dict[str, Any]:
    document = {}
    for key, value in data.items():
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                value = None
        document[key] = value
    return document


def make_json_safe(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {key: make_json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    return value


@app.get("/healthz")
def healthcheck():
    return jsonify({"status": "ok"})


@app.post("/insert-fast")
def insert_fast():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    document = normalize_document(payload)

    try:
        collection = get_collection().with_options(write_concern=WriteConcern(w=1))
        result = collection.insert_one(document)
        return jsonify({"inserted_id": str(result.inserted_id)}), 201
    except (PyMongoError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/insert-safe")
def insert_safe():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    document = normalize_document(payload)

    try:
        collection = get_collection().with_options(
            write_concern=WriteConcern(w="majority")
        )
        result = collection.insert_one(document)
        return jsonify({"inserted_id": str(result.inserted_id)}), 201
    except (PyMongoError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/count-tesla-primary")
def count_tesla_primary():
    try:
        collection = get_collection().with_options(
            read_preference=ReadPreference.PRIMARY
        )
        total_count = collection.count_documents({"Make": "TESLA"})
        return jsonify({"count": total_count})
    except (PyMongoError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/count-bmw-secondary")
def count_bmw_secondary():
    try:
        collection = get_collection().with_options(
            read_preference=ReadPreference.SECONDARY
        )
        total_count = collection.count_documents({"Make": "BMW"})
        return jsonify({"count": total_count})
    except (PyMongoError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/sample")
def sample_document():
    try:
        collection = get_collection()
        document = collection.find_one()
        if not document:
            return jsonify({"document": None})
        return jsonify({"document": make_json_safe(document)})
    except (PyMongoError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
