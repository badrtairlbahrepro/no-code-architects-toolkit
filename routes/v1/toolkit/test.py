import os
import logging
from flask import Blueprint
from services.authentication import authenticate
from services.cloud_storage import upload_file
from app_utils import queue_task_wrapper
from services.gcp_toolkit import minio_client  # Ajout pour vérifier le client MinIO

v1_toolkit_test_bp = Blueprint('v1_toolkit_test', __name__)
logger = logging.getLogger(__name__)

STORAGE_PATH = "/tmp/"
BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'bucket-no-code-tools')

@v1_toolkit_test_bp.route('/v1/toolkit/test', methods=['GET'])
@authenticate
@queue_task_wrapper(bypass_queue=False)
def test_api(job_id, data):
    logger.info(f"Job {job_id}: Testing NCA Toolkit API setup")
    
    try:
        # Vérifier l'existence du bucket
        if not minio_client.bucket_exists(BUCKET_NAME):
            logger.warning(f"Bucket {BUCKET_NAME} does not exist. Creating...")
            minio_client.make_bucket(BUCKET_NAME)
        
        # Create test file
        test_filename = os.path.join(STORAGE_PATH, "success.txt")
        with open(test_filename, 'w') as f:
            f.write("You have successfully installed the NCA Toolkit API, great job!")
        
        # Upload file to cloud storage
        upload_url = upload_file(test_filename)
        
        # Clean up local file
        os.remove(test_filename)
        
        return upload_url, "/v1/toolkit/test", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error testing API setup - {str(e)}")
        return str(e), "/v1/toolkit/test", 500