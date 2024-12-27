import os

# Retrieve the API key from environment variables
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set")

# GCP environment variables
GCP_SA_CREDENTIALS = os.environ.get('GCP_SA_CREDENTIALS', '')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME', '')

# S3 (DigitalOcean Spaces) environment variables
S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL', '')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', '')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', '')

# MinIO environment variables
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'minio-jo0w0sg0o0gocc4wo4g8cwcg.156.67.31.20.sslip.io')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'xysDRrnFVvtJg07rynR5')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'trVjKEZPAnDsMizus6zHrClRJl22Qy1yMV7mIVOO')
MINIO_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME', 'bucket-no-code-tools')

def validate_env_vars(provider):
    """ Validate the necessary environment variables for the selected storage provider """
    required_vars = {
        'GCP': ['GCP_BUCKET_NAME', 'GCP_SA_CREDENTIALS'],
        'S3': ['S3_ENDPOINT_URL', 'S3_ACCESS_KEY', 'S3_SECRET_KEY'],
        'MINIO': ['MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY']
    }
    
    missing_vars = [var for var in required_vars[provider] if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing environment variables for {provider} storage: {', '.join(missing_vars)}")

class CloudStorageProvider:
    """ Abstract CloudStorageProvider class to define the upload_file method """
    def upload_file(self, file_path: str) -> str:
        raise NotImplementedError("upload_file must be implemented by subclasses")

class GCPStorageProvider(CloudStorageProvider):
    """ GCP-specific cloud storage provider """
    def __init__(self):
        self.bucket_name = os.getenv('GCP_BUCKET_NAME')

    def upload_file(self, file_path: str) -> str:
        from services.gcp_toolkit import upload_to_gcs
        return upload_to_gcs(file_path, self.bucket_name)

class S3CompatibleProvider(CloudStorageProvider):
    """ S3-compatible storage provider (e.g., DigitalOcean Spaces, MinIO) """
    def __init__(self):
        self.endpoint_url = os.getenv('S3_ENDPOINT_URL') or MINIO_ENDPOINT
        self.access_key = os.getenv('S3_ACCESS_KEY') or MINIO_ACCESS_KEY
        self.secret_key = os.getenv('S3_SECRET_KEY') or MINIO_SECRET_KEY
        self.bucket_name = os.getenv('S3_BUCKET_NAME') or MINIO_BUCKET_NAME

    def upload_file(self, file_path: str) -> str:
        from services.s3_toolkit import upload_to_s3
        return upload_to_s3(file_path, self.endpoint_url, self.access_key, self.secret_key, self.bucket_name)

def get_storage_provider() -> CloudStorageProvider:
    """ Get the appropriate storage provider based on the available environment variables """
    try:
        validate_env_vars('GCP')
        return GCPStorageProvider()
    except ValueError:
        try:
            validate_env_vars('S3')
            return S3CompatibleProvider()
        except ValueError:
            try:
                validate_env_vars('MINIO')
                return S3CompatibleProvider()
            except ValueError:
                raise ValueError("No valid cloud storage configuration found. Please set GCP, S3, or MinIO environment variables.")
