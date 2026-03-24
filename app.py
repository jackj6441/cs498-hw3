import os

from flask import Flask, jsonify, request
from pymongo import MongoClient, ReadPreference, WriteConcern

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://jackj6_db_user:dyt2Z6ctoqa2S8WT@cluster0.wcvw3dm.mongodb.net/?appName=Cluster0")
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

    # fast write, not being too fancy here
    quick_collection = cars.with_options(write_concern=WriteConcern(w=1))

    insert_result = quick_collection.insert_one(body)
    new_id = str(insert_result.inserted_id)

    return jsonify({"inserted_id": new_id}), 200


@app.route("/insert-safe", methods=["POST"])
def insert_safe():
    body = request.get_json()

    if not body:
        return jsonify({"error": "Invalid JSON payload"}), 400

    body = _clean_make(body)

    safer_collection = cars.with_options(
        write_concern=WriteConcern(w="majority")
    )

    saved = safer_collection.insert_one(body)
    saved_id = str(saved.inserted_id)

    return jsonify({"inserted_id": saved_id}), 200


@app.route("/count-tesla-primary", methods=["GET"])
def count_tesla_primary():
    main_reader = cars.with_options(read_preference=ReadPreference.PRIMARY)

    tesla_filter = {
    "$or": [
        {"Make": {"$regex": "^TESLA$", "$options": "i"}},
        {"make": {"$regex": "^TESLA$", "$options": "i"}},
    ]
}
    total = main_reader.count_documents(tesla_filter)

    return jsonify({"count": total}), 200


@app.route("/count-bmw-secondary", methods=["GET"])
def count_bmw_secondary():
    backup_reader = cars.with_options(read_preference=ReadPreference.SECONDARY)

    bmw_filter = {
    "$or": [
        {"Make": {"$regex": "^BMW$", "$options": "i"}},
        {"make": {"$regex": "^BMW$", "$options": "i"}},
    ]
}
    total = backup_reader.count_documents(bmw_filter)

    return jsonify({"count": total}), 200


@app.route("/", methods=["GET"])
def home():
    # basic heartbeat route
    return jsonify({"message": "API is running"}), 200


# old local test
# app.run(debug=True)

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 5000
    app.run(host=host, port=port, debug=False)