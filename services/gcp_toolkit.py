import os
import json
import logging
from minio import Minio
from minio.error import S3Error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MinIO environment variables
MINIO_ENDPOINT = "minio-jo0w0sg0o0gocc4wo4g8cwcg.156.67.31.20.sslip.io"
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'XmF3n33euDkufzDA')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'NIbo1lSyRmzDGnpc0wNyxW52ZojsOQF1')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'bucket-no-code-tools')
STORAGE_PATH = "/tmp/"

# MinIO client
minio_client = None

def initialize_minio_client():
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=True
        )
        
        # Check if bucket exists, create if not
        if not client.bucket_exists(MINIO_BUCKET_NAME):
            client.make_bucket(MINIO_BUCKET_NAME)
        
        logger.info(f"MinIO client initialized for bucket: {MINIO_BUCKET_NAME}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize MinIO client: {e}")
        return None

# Initialize the MinIO client
minio_client = initialize_minio_client()

def upload_to_storage(file_path, bucket_name=MINIO_BUCKET_NAME):
    """
    Upload a file to MinIO storage
    
    :param file_path: Path to the file to upload
    :param bucket_name: Bucket to upload to (defaults to MINIO_BUCKET_NAME)
    :return: URL or path of the uploaded file
    """
    if not minio_client:
        raise ValueError("MinIO client is not initialized. Skipping file upload.")

    try:
        # Generate a unique object name
        object_name = os.path.basename(file_path)
        
        logger.info(f"Uploading file to MinIO Storage: {file_path}")
        
        # Upload the file
        minio_client.fput_object(
            bucket_name, 
            object_name, 
            file_path
        )
        
        # Construct a URL-like path for the object
        file_url = f"/{bucket_name}/{object_name}"
        
        logger.info(f"File uploaded successfully to MinIO: {file_url}")
        return file_url
    except S3Error as e:
        logger.error(f"Error uploading file to MinIO: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading file to MinIO: {e}")
        raise

# Alias for backward compatibility
upload_to_gcs = upload_to_storage
