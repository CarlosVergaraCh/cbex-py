#!/usr/bin/env - python

from datetime import timedelta

# needed for any cluster connection
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions

import settings

# Settings
bucket_name = settings.BUCKET_NAME
node = settings.CLUSTER_NODES[0]
admin_user = settings.ADMIN_USER
admin_password = settings.ADMIN_PASS
timeout = settings.TIMEOUT

if __name__ == "__main__":
    # Connect options - authentication
    auth = PasswordAuthenticator(
        admin_user,
        admin_password,
    )
    # Get a reference to our cluster
    # NOTE: For TLS/SSL connection use 'couchbases://<your-ip-address>' instead
    cluster = Cluster(f"couchbase://{node}", ClusterOptions(auth))

    # Wait until the cluster is ready for use.
    cluster.wait_until_ready(timedelta(seconds=5))

    print("Cleaning up bucket {0}...".format(bucket_name))

    cluster.buckets().drop_bucket(bucket_name)

    print("Clean up finished!")
