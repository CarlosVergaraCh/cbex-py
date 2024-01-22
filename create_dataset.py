#!/usr/bin/env - python

import json
import sys
import time

import requests
from requests.auth import HTTPBasicAuth

from datetime import timedelta

# needed for any cluster connection
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.collection import Collection

# needed for options -- cluster, timeout, SQL++ (N1QL) query, etc.
from couchbase.options import ClusterOptions

from couchbase.management.options import CreatePrimaryQueryIndexOptions
from couchbase.management.logic.buckets_logic import CreateBucketSettings
from couchbase.management.queries import QueryIndexManager

import settings


# Settings
bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD
node = settings.CLUSTER_NODES[0]
admin_user = settings.ADMIN_USER
admin_password = settings.ADMIN_PASS
timeout = settings.TIMEOUT
bucket_ram_quota = settings.BUCKET_RAM_QUOTA
fts_index_name = settings.FTS_INDEX_NAME


def admin_create_bucket(cluster: Cluster):
    try:
        print("Creating bucket {0}...".format(bucket_name))

        cluster.buckets().create_bucket(
            CreateBucketSettings(
                name=bucket_name,
                bucket_type="couchbase",
                flush_enabled=True,
                ram_quota_mb=bucket_ram_quota,
            )
        )
        print("Waiting for bucket {0} to be available...".format(bucket_name))

        cluster.wait_until_ready(timedelta(seconds=5))
    except Exception as e:
        print(e)
        print(
            "!!! Error creating the bucket {0}:\n{1}\nExecute cleanup.py and try again".format(
                bucket_name, sys.exc_info()
            )
        )


def add_indexes(index_manager: QueryIndexManager):
    try:
        print("Creating primary index on {0}...".format(bucket_name))

        index_manager.create_primary_index(
            bucket_name=bucket_name,
            options=CreatePrimaryQueryIndexOptions(ignore_if_exists=True),
        )

        print("Indexes created successfully!")
    except:
        print(
            "!!! Error creating indexes:\n{0}\nExecute cleanup.py and try again".format(
                sys.exc_info()
            )
        )


def add_stocks(default_collection: Collection):
    print("Loading dataset...")
    # https://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download
    stocks_json = open(settings.STOCKS_FILE, "r")
    stocks_dict = json.load(stocks_json)
    symbol_list = []
    stock_count = 0
    for stock_doc in stocks_dict:
        if stock_count >= settings.NUM_STOCKS:
            break
        if "priority" not in stock_doc:
            stock_doc["priority"] = 2
        stock_key = "stock:" + stock_doc["symbol"]
        symbol_list.append(stock_key)
        default_collection.upsert(stock_key, stock_doc)
        stock_count += 1
    default_collection.upsert(settings.PRODUCT_LIST, {"symbols": symbol_list})
    print("Successfully populated dataset!")


def add_fts_indexes():
    print("Creating fts index {0} on {1}...".format(fts_index_name, bucket_name))
    fts_json = open(settings.FTS_INDEX_FILE, "r")
    url = "http://{0}:8094/api/index/{1}".format(node, fts_index_name)
    payload = json.load(fts_json)
    headers = {"content-type": "appllication.json"}
    x = requests.put(
        url,
        data=json.dumps(payload),
        headers=headers,
        timeout=timeout,
        auth=HTTPBasicAuth(admin_user, admin_password),
    )
    if x.status_code == 200:
        print("Indexes created successfully!")
    else:
        print(
            "!!! Error creating indexes:\n{0}\nExecute cleanup.py and try again".format(
                x.text
            )
        )


if __name__ == "__main__":
    # Connect options - authentication
    auth = PasswordAuthenticator(
        user,
        password,
    )
    # Get a reference to our cluster
    # NOTE: For TLS/SSL connection use 'couchbases://<your-ip-address>' instead
    cluster = Cluster(f"couchbase://{node}", ClusterOptions(auth))

    # Wait until the cluster is ready for use.
    cluster.wait_until_ready(timedelta(seconds=5))

    admin_create_bucket(cluster)

    # Workaround wait_ready is not enough...
    time.sleep(timeout)

    bucket = cluster.bucket(bucket_name)
    add_stocks(bucket.default_collection())

    index_manager = cluster.query_indexes()
    add_indexes(index_manager)

    add_fts_indexes()
