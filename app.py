import os

from flask import Flask, jsonify, request
from pymongo import MongoClient, ReadPreference, WriteConcern
from pymongo.errors import PyMongoError

app = Flask(__name__)

mongo_uri = os.getenv(
    "MONGO_URI",
    "mongodb+srv://jackj6_db_user:dyt2Z6ctoqa2S8WT@cluster0.wcvw3dm.mongodb.net/?appName=Cluster0"
)
db_name = "ev_db"
collection_name = "vehicles"

client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
db = client[db_name]
cars = db[collection_name]


def _clean_make(payload):
    if "make" in payload and payload["make"] is not None:
        raw_make = str(payload["make"])
        payload["make"] = raw_make.strip().upper()
    return payload


@app.route("/insert-fast", methods=["POST"])
def insert_fast():
    body = request.get_json()

    if not body:
        return jsonify({"error": "Invalid JSON payload"}), 400

    body = _clean_make(body)

    fast_collection = cars.with_options(write_concern=WriteConcern(w=1))
    result = fast_collection.insert_one(body)

    return jsonify({"inserted_id": str(result.inserted_id)}), 200


@app.route("/insert-safe", methods=["POST"])
def insert_safe():
    body = request.get_json()

    if not body:
        return jsonify({"error": "Invalid JSON payload"}), 400

    body = _clean_make(body)

    safe_collection = cars.with_options(write_concern=WriteConcern(w="majority"))
    result = safe_collection.insert_one(body)

    return jsonify({"inserted_id": str(result.inserted_id)}), 200


@app.route("/count-tesla-primary", methods=["GET"])
def count_tesla_primary():
    primary_collection = cars.with_options(read_preference=ReadPreference.PRIMARY)
    total = primary_collection.count_documents({"Make": "TESLA"})
    return jsonify({"count": total}), 200


@app.route("/count-bmw-secondary", methods=["GET"])
def count_bmw_secondary():
    try:
        secondary_collection = cars.with_options(
            read_preference=ReadPreference.SECONDARY
        )
        total = secondary_collection.count_documents({"Make": "BMW"})
    except PyMongoError:
        primary_collection = cars.with_options(
            read_preference=ReadPreference.PRIMARY
        )
        total = primary_collection.count_documents({"Make": "BMW"})

    return jsonify({"count": total}), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)