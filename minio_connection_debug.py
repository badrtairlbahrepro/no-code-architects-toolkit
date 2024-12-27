import os
from minio import Minio
from minio.error import S3Error

def debug_minio_connection():
    # Configuration MinIO
    MINIO_ENDPOINT = "minio-jo0w0sg0o0gocc4wo4g8cwcg.156.67.31.20.sslip.io"
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'xysDRrnFVvtJg07rynR5')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'trVjKEZPAnDsMizus6zHrClRJl22Qy1yMV7mIVOO')
    MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'bucket-no-code-tools')
    MINIO_SECURE = True

    print("MinIO Connection Debug Script")
    print("=" * 40)
    print(f"Endpoint: {MINIO_ENDPOINT}")
    print(f"Access Key: {MINIO_ACCESS_KEY}")
    print(f"Bucket Name: {MINIO_BUCKET_NAME}")
    print(f"Secure Connection: {MINIO_SECURE}")
    print("=" * 40)

    try:
        # Créer un client MinIO
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )

        # Vérifier si le bucket existe
        bucket_exists = client.bucket_exists(MINIO_BUCKET_NAME)
        print(f"Bucket '{MINIO_BUCKET_NAME}' exists: {bucket_exists}")

        # Si le bucket n'existe pas, le créer
        if not bucket_exists:
            print(f"Creating bucket '{MINIO_BUCKET_NAME}'...")
            client.make_bucket(MINIO_BUCKET_NAME)
            print(f"Bucket '{MINIO_BUCKET_NAME}' created successfully.")

        # Tester l'upload d'un fichier
        test_file_path = "/tmp/minio_debug_test.txt"
        with open(test_file_path, 'w') as f:
            f.write("MinIO connection debug test")

        # Uploader le fichier de test
        client.fput_object(
            MINIO_BUCKET_NAME, 
            "debug_test_file.txt", 
            test_file_path
        )
        print("Test file uploaded successfully!")

        # Vérifier les permissions
        try:
            objects = client.list_objects(MINIO_BUCKET_NAME)
            print("Objects in bucket:")
            for obj in objects:
                print(f" - {obj.object_name}")
        except Exception as list_error:
            print(f"Error listing objects: {list_error}")

    except Exception as e:
        print(f"Error connecting to MinIO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_minio_connection()
