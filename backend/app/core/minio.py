from minio import Minio
from app.config import settings

def get_minio_client() -> Minio:
    """
    Get MinIO client instance based on settings.
    """
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE  # Default False usually for internal
    )

def ensure_bucket_exists(client: Minio, bucket_name: str):
    """
    Ensure a bucket exists, create it if not.
    """
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

