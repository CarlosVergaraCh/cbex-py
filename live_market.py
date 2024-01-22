#!/usr/bin/env - python
import random
import time

from datetime import timedelta

# needed for any cluster connection
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
import couchbase.subdocument as SD

# needed for options -- cluster, timeout, SQL++ (N1QL) query, etc.
from couchbase.options import ClusterOptions

import settings

bucket_name = settings.BUCKET_NAME
user = settings.USERNAME
password = settings.PASSWORD
node = settings.CLUSTER_NODES[0]

# Connect options - authentication
auth = PasswordAuthenticator(
    user,
    password,
)
# Get a reference to our cluster
# NOTE: For TLS/SSL connection use 'couchbases://<your-ip-address>' instead
cluster = Cluster(f"couchbase://{node}", ClusterOptions(auth))

# Wait until the cluster is ready for use.
cluster.wait_until_ready(timedelta(seconds=15))

while True:
    try:
        print(".")
        result = cluster.query(
            "SELECT symbol,price FROM {} WHERE symbol IS NOT MISSING AND price IS NOT MISSING".format(
                bucket_name
            )
        )
        for row in result.rows():
            print(row)
            stock_key = "stock:" + (row["symbol"])
            # perturb the price and round it to 2 decimal places
            price_multiplier = random.normalvariate(1, 0.025)
            if row["symbol"] == "CBSE" and price_multiplier < 1:
                price_multiplier = 1
            new_price = float(row["price"]) * price_multiplier
            new_price = round(new_price, 2)
            print(stock_key)
            res = (
                cluster.bucket(bucket_name)
                .default_collection()
                .mutate_in(stock_key, [SD.upsert("price", new_price)])
            )
    except Exception as e:
        print(e)
        pass

    time.sleep(8)
