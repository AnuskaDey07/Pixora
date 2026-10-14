"""MinIO storage wrapper.

Two clients: internal (docker hostname) for backend I/O, public (localhost)
for presigned URLs the browser will fetch.
"""
from __future__ import annotations

import io
import uuid
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import get_settings


_client = None
_public_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    scheme = "https" if settings.minio_use_ssl else "http"
    _client = boto3.client(
        "s3",
        endpoint_url=f"{scheme}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name="us-east-1",
    )
    return _client


def _get_public_client():
    global _public_client
    if _public_client is not None:
        return _public_client
    settings = get_settings()
    scheme = "https" if settings.minio_use_ssl else "http"
    _public_client = boto3.client(
        "s3",
        endpoint_url=f"{scheme}://{settings.minio_public_endpoint}",
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name="us-east-1",
    )
    return _public_client


def _bucket(name: str) -> str:
    settings = get_settings()
    mapping = {
        "uploads": settings.s3_bucket_uploads,
        "thumbs": settings.s3_bucket_thumbs,
        "results": settings.s3_bucket_results,
        "masks": settings.s3_bucket_masks,
    }
    if name not in mapping:
        raise ValueError(f"unknown bucket alias: {name}")
    return mapping[name]


def make_key(prefix: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"{prefix}/{uuid.uuid4().hex}.{ext}"


def upload_bytes(bucket_alias: str, key: str, data: bytes, content_type: str) -> None:
    _get_client().put_object(
        Bucket=_bucket(bucket_alias),
        Key=key,
        Body=io.BytesIO(data),
        ContentType=content_type,
    )


def upload_fileobj(bucket_alias: str, key: str, fileobj: BinaryIO, content_type: str) -> None:
    _get_client().upload_fileobj(
        fileobj,
        _bucket(bucket_alias),
        key,
        ExtraArgs={"ContentType": content_type},
    )


def download_bytes(bucket_alias: str, key: str) -> bytes:
    resp = _get_client().get_object(Bucket=_bucket(bucket_alias), Key=key)
    return resp["Body"].read()


def delete_object(bucket_alias: str, key: str) -> None:
    try:
        _get_client().delete_object(Bucket=_bucket(bucket_alias), Key=key)
    except ClientError:
        pass


def presigned_url(bucket_alias: str, key: str, expires_seconds: int = 3600) -> str:
    """Generate a URL signed against the *public* endpoint so browsers can fetch it."""
    return _get_public_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket(bucket_alias), "Key": key},
        ExpiresIn=expires_seconds,
    )
