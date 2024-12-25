from flask import Flask, request, jsonify
from queue import Queue
from services.webhook import send_webhook
import threading
import uuid
import os
import time
from version import BUILD_NUMBER  # Import the BUILD_NUMBER
from minio import Minio
from minio.error import S3Error
import io
from dotenv import load_dotenv
load_dotenv()  # Charger les variables d'environnement du fichier .env

MAX_QUEUE_LENGTH = int(os.environ.get('MAX_QUEUE_LENGTH', 0))

# Configuration MinIO
minio_client = Minio(
    os.environ.get('MINIO_ENDPOINT', 'localhost:9000'),
    access_key=os.environ.get('MINIO_ACCESS_KEY', 'minioadmin'),
    secret_key=os.environ.get('MINIO_SECRET_KEY', 'minioadmin'),
    secure=False
)

def upload_to_minio(file, bucket_name='default', object_name=None):
    """
    Téléverse un fichier vers MinIO
    
    :param file: Fichier à téléverser
    :param bucket_name: Nom du bucket MinIO
    :param object_name: Nom de l'objet dans MinIO (optionnel)
    :return: URL de l'objet téléversé ou None en cas d'erreur
    """
    try:
        # Créer le bucket s'il n'existe pas
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Générer un nom d'objet si non fourni
        if object_name is None:
            object_name = f"{uuid.uuid4()}_{file.filename}"

        # Téléverser le fichier
        minio_client.put_object(
            bucket_name, 
            object_name, 
            file.stream, 
            file.content_length
        )

        # Retourner l'URL de l'objet
        return f"/{bucket_name}/{object_name}"

    except S3Error as e:
        print(f"Erreur lors du téléversement vers MinIO : {e}")
        return None

def create_app():
    app = Flask(__name__)

    # Create a queue to hold tasks
    task_queue = Queue()
    queue_id = id(task_queue)  # Generate a single queue_id for this worker

    # Function to process tasks from the queue
    def process_queue():
        while True:
            job_id, data, task_func, queue_start_time = task_queue.get()
            queue_time = time.time() - queue_start_time
            run_start_time = time.time()
            pid = os.getpid()  # Get the PID of the actual processing thread
            response = task_func()
            run_time = time.time() - run_start_time
            total_time = time.time() - queue_start_time

            response_data = {
                "endpoint": response[1],
                "code": response[2],
                "id": data.get("id"),
                "job_id": job_id,
                "response": response[0] if response[2] == 200 else None,
                "message": "success" if response[2] == 200 else response[0],
                "pid": pid,
                "queue_id": queue_id,
                "run_time": round(run_time, 3),
                "queue_time": round(queue_time, 3),
                "total_time": round(total_time, 3),
                "queue_length": task_queue.qsize(),
                "build_number": BUILD_NUMBER  # Add build number to response
            }

            send_webhook(data.get("webhook_url"), response_data)

            task_queue.task_done()

    # Start the queue processing in a separate thread
    threading.Thread(target=process_queue, daemon=True).start()

    # Decorator to add tasks to the queue or bypass it
    def queue_task(bypass_queue=False):
        def decorator(f):
            def wrapper(*args, **kwargs):
                job_id = str(uuid.uuid4())
                data = request.json if request.is_json else {}
                pid = os.getpid()  # Get PID for non-queued tasks
                start_time = time.time()
                
                if bypass_queue or 'webhook_url' not in data:
                    
                    response = f(job_id=job_id, data=data, *args, **kwargs)
                    run_time = time.time() - start_time
                    return {
                        "code": response[2],
                        "id": data.get("id"),
                        "job_id": job_id,
                        "response": response[0] if response[2] == 200 else None,
                        "message": "success" if response[2] == 200 else response[0],
                        "run_time": round(run_time, 3),
                        "queue_time": 0,
                        "total_time": round(run_time, 3),
                        "pid": pid,
                        "queue_id": queue_id,
                        "queue_length": task_queue.qsize(),
                        "build_number": BUILD_NUMBER  # Add build number to response
                    }, response[2]
                else:
                    if MAX_QUEUE_LENGTH > 0 and task_queue.qsize() >= MAX_QUEUE_LENGTH:
                        return {
                            "code": 429,
                            "id": data.get("id"),
                            "job_id": job_id,
                            "message": f"MAX_QUEUE_LENGTH ({MAX_QUEUE_LENGTH}) reached",
                            "pid": pid,
                            "queue_id": queue_id,
                            "queue_length": task_queue.qsize(),
                            "build_number": BUILD_NUMBER  # Add build number to response
                        }, 429
                    
                    task_queue.put((job_id, data, lambda: f(job_id=job_id, data=data, *args, **kwargs), start_time))
                    
                    return {
                        "code": 202,
                        "id": data.get("id"),
                        "job_id": job_id,
                        "message": "processing",
                        "pid": pid,
                        "queue_id": queue_id,
                        "max_queue_length": MAX_QUEUE_LENGTH if MAX_QUEUE_LENGTH > 0 else "unlimited",
                        "queue_length": task_queue.qsize(),
                        "build_number": BUILD_NUMBER  # Add build number to response
                    }, 202
            return wrapper
        return decorator

    app.queue_task = queue_task

    # Import blueprints
    from routes.media_to_mp3 import convert_bp
    from routes.transcribe_media import transcribe_bp
    from routes.combine_videos import combine_bp
    from routes.audio_mixing import audio_mixing_bp
    from routes.gdrive_upload import gdrive_upload_bp
    from routes.authenticate import auth_bp
    from routes.caption_video import caption_bp 
    from routes.extract_keyframes import extract_keyframes_bp
    from routes.image_to_video import image_to_video_bp
    

    # Register blueprints
    app.register_blueprint(convert_bp)
    app.register_blueprint(transcribe_bp)
    app.register_blueprint(combine_bp)
    app.register_blueprint(audio_mixing_bp)
    app.register_blueprint(gdrive_upload_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(caption_bp)
    app.register_blueprint(extract_keyframes_bp)
    app.register_blueprint(image_to_video_bp)
    
    

    # version 1.0
    from routes.v1.ffmpeg.ffmpeg_compose import v1_ffmpeg_compose_bp
    from routes.v1.media.media_transcribe import v1_media_transcribe_bp
    from routes.v1.media.transform.media_to_mp3 import v1_media_transform_mp3_bp
    from routes.v1.video.concatenate import v1_video_concatenate_bp
    from routes.v1.video.caption_video import v1_video_caption_bp
    from routes.v1.image.transform.image_to_video import v1_image_transform_video_bp
    from routes.v1.toolkit.test import v1_toolkit_test_bp
    from routes.v1.toolkit.authenticate import v1_toolkit_auth_bp
    from routes.v1.code.execute.execute_python import v1_code_execute_bp

    app.register_blueprint(v1_ffmpeg_compose_bp)
    app.register_blueprint(v1_media_transcribe_bp)
    app.register_blueprint(v1_media_transform_mp3_bp)
    app.register_blueprint(v1_video_concatenate_bp)
    app.register_blueprint(v1_video_caption_bp)
    app.register_blueprint(v1_image_transform_video_bp)
    app.register_blueprint(v1_toolkit_test_bp)
    app.register_blueprint(v1_toolkit_auth_bp)
    app.register_blueprint(v1_code_execute_bp)

    @app.route('/upload', methods=['POST'])
    def upload_file():
        """
        Route pour téléverser un fichier vers MinIO
        """
        if 'file' not in request.files:
            return jsonify({"error": "Aucun fichier n'a été téléversé"}), 400
        
        file = request.files['file']
        bucket_name = request.form.get('bucket', 'default')
        
        if file.filename == '':
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        
        file_url = upload_to_minio(file, bucket_name)
        
        if file_url:
            return jsonify({"message": "Fichier téléversé avec succès", "url": file_url}), 200
        else:
            return jsonify({"error": "Échec du téléversement"}), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)