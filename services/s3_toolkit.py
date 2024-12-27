import os
import logging
import boto3
from botocore.exceptions import ClientError
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def parse_s3_url(s3_url):
    """ 
    Parse S3 URL to extract bucket name, region, and endpoint 
    
    :param s3_url: Full S3 endpoint URL
    :return: Tuple of (bucket_name, region, endpoint_url)
    """
    try:
        parsed_url = urlparse(s3_url)
        # Extract bucket name from the host (assuming subdomain-style URL)
        bucket_name = parsed_url.netloc.split('.')[0]
        
        # Reconstruct the full endpoint URL
        endpoint_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Extract region (if possible)
        region = parsed_url.netloc.split('.')[1] if len(parsed_url.netloc.split('.')) > 1 else ''
        
        return bucket_name, region, endpoint_url
    except Exception as e:
        logger.error(f"Error parsing S3 URL: {e}")
        raise ValueError(f"Invalid S3 URL format: {s3_url}")

def upload_to_s3(file_path, s3_url, access_key, secret_key, bucket_name=None):
    """ 
    Upload a file to S3-compatible storage 
    
    :param file_path: Path to the file to upload
    :param s3_url: S3 endpoint URL
    :param access_key: Access key for authentication
    :param secret_key: Secret key for authentication
    :param bucket_name: Optional bucket name (overrides parsed bucket)
    :return: URL or path of the uploaded file
    """
    try:
        # Parse the S3 URL into bucket, region, and endpoint
        parsed_bucket_name, region, endpoint_url = parse_s3_url(s3_url)
        
        # Use provided bucket name or fallback to parsed bucket name
        bucket_name = bucket_name or parsed_bucket_name
        
        # Create S3 client
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        s3_client = session.client('s3', endpoint_url=endpoint_url)
        
        # Extract filename
        filename = os.path.basename(file_path)
        
        # Upload the file
        s3_client.upload_file(
            file_path, 
            bucket_name, 
            filename
        )
        
        # Construct a URL-like path for the object
        file_url = f"/{bucket_name}/{filename}"
        
        logger.info(f"File uploaded successfully to S3-compatible storage: {file_url}")
        return file_url
    
    except ClientError as e:
        logger.error(f"S3 client error uploading file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading file to S3-compatible storage: {e}")
        raise
