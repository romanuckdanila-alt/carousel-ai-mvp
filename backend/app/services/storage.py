from __future__ import annotations

from io import BytesIO
from urllib.parse import unquote, urlparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings


class StorageService:
    def __init__(self) -> None:
        scheme = "https" if settings.minio_secure else "http"
        self.internal_client = boto3.client(
            "s3",
            endpoint_url=f"{scheme}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.public_client = boto3.client(
            "s3",
            endpoint_url=f"{scheme}://{settings.minio_public_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def ensure_bucket(self, bucket_name: str) -> None:
        try:
            self.internal_client.head_bucket(Bucket=bucket_name)
        except ClientError:
            self.internal_client.create_bucket(Bucket=bucket_name)

    def ensure_default_buckets(self) -> None:
        self.ensure_bucket(settings.assets_bucket)
        self.ensure_bucket(settings.exports_bucket)

    def upload_bytes(self, bucket: str, key: str, content: bytes, content_type: str) -> None:
        self.internal_client.upload_fileobj(
            BytesIO(content),
            bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    def presigned_get_url(self, bucket: str, key: str, expires_seconds: int = 3600) -> str:
        return self.internal_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def public_presigned_get_url(self, bucket: str, key: str, expires_seconds: int = 3600) -> str:
        return self.public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def delete_object(self, bucket: str, key: str) -> None:
        self.internal_client.delete_object(Bucket=bucket, Key=key)

    def try_extract_object_key(self, url: str, bucket: str) -> str | None:
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path.lstrip("/"))
            bucket_prefix = f"{bucket}/"
            if path.startswith(bucket_prefix):
                return path[len(bucket_prefix):]
            return path or None
        except Exception:
            return None
