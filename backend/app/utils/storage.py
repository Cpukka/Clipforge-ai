import boto3
from botocore.exceptions import ClientError
from app.config import settings
import aiofiles

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

async def upload_to_s3(file_content: bytes, key: str, content_type: str) -> str:
    try:
        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ContentType=content_type
        )
        url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        return url
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        raise

async def delete_from_s3(key: str):
    try:
        s3_client.delete_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=key
        )
    except ClientError as e:
        print(f"Error deleting from S3: {e}")
        raise

def download_from_s3(key: str, local_path: str):
    try:
        s3_client.download_file(settings.AWS_BUCKET_NAME, key, local_path)
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        raise