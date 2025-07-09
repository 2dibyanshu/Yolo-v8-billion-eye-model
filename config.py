import os

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
INPUT_QUEUE = os.getenv("INPUT_QUEUE", "image_queue")
OUTPUT_QUEUE = os.getenv("OUTPUT_QUEUE", "detected_objects_queue")

# YOLO Configuration
YOLO_WEIGHTS_PATH = os.getenv("YOLO_WEIGHTS_PATH", "./best (2).pt")
# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000").strip()
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = os.getenv("BUCKET_NAME", "billion-eyes-images")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "BillionEyes_V1")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "Incident")
