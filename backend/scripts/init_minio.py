"""Ensure Pixora's MinIO buckets exist. Idempotent."""
from __future__ import annotations

import os
import sys
import time

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError


BUCKETS = [
    os.environ.get("S3_BUCKET_UPLOADS", "pixora-uploads"),
    os.environ.get("S3_BUCKET_THUMBS", "pixora-thumbs"),
    os.environ.get("S3_BUCKET_RESULTS", "pixora-results"),
    os.environ.get("S3_BUCKET_MASKS", "pixora-masks"),
]


def client():
    endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    use_ssl = os.environ.get("MINIO_USE_SSL", "false").lower() == "true"
    return boto3.client(
        "s3",
        endpoint_url=f"http{'s' if use_ssl else ''}://{endpoint}",
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name="us-east-1",
    )


def main() -> int:
    deadline = time.time() + 60
    s3 = client()

    while time.time() < deadline:
        try:
            s3.list_buckets()
            break
        except (EndpointConnectionError, ClientError) as exc:
            print(f"waiting for minio: {exc}")
            time.sleep(2)
    else:
        print("MinIO not reachable after 60s", file=sys.stderr)
        return 1

    for bucket in BUCKETS:
        try:
            s3.head_bucket(Bucket=bucket)
            print(f"bucket exists: {bucket}")
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchBucket", "NotFound"):
                s3.create_bucket(Bucket=bucket)
                print(f"bucket created: {bucket}")
            else:
                print(f"error checking {bucket}: {exc}", file=sys.stderr)
                return 1

    print("MinIO ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
