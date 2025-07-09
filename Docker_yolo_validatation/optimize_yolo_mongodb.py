import pika
import base64
import json
import cv2
import os
from io import BytesIO
from PIL import Image
from ultralytics import YOLO
from minio import Minio  # MinIO SDK
from botoFunc import push_image_to_minio
import config  # Import configuration file
import numpy as np
from pymongo import MongoClient


# MongoDB Handler Class
class MongoDBHandler:
    """Handles MongoDB operations."""
    
    def __init__(self, uri, db_name, collection_name):
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            print("✅ Connected to MongoDB successfully!")
        except Exception as e:
            raise ConnectionError(f"⚠️ Error connecting to MongoDB: {e}")

    def insert_message(self, message):
        """Insert message into MongoDB."""
        try:
            self.collection.insert_one(message)
            print(f"✅ Message saved to MongoDB collection: {config.MONGO_COLLECTION}")
        except Exception as e:
            print(f"⚠️ MongoDB Insert Error: {e}")


class ObjectDetectorYOLOv8:
    def __init__(self, weights_path):
        """Initialize YOLOv8 model"""
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"YOLO weights file not found at {weights_path}")
        try:
            self.model = YOLO(weights_path)
            print("✅ YOLOv8 model loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Error loading YOLOv8 model: {e}")

    def detect_objects(self, image_bytes):
        """Run YOLO object detection on the received image"""
        try:
            img = Image.open(BytesIO(image_bytes))  # Convert bytes to image
            results = self.model(img)
            return image_bytes  # Returning original image bytes (unchanged format)
        except Exception as e:
            print(f"⚠️ Error during object detection: {e}")
            return None
        

def get_max_confidence(results):
    """Extract the highest confidence score from YOLO results."""
    if results and hasattr(results[0], "boxes") and results[0].boxes is not None:
        confs = results[0].boxes.conf.cpu().numpy() if hasattr(results[0].boxes, "conf") else []
        return max(confs) if len(confs) > 0 else 0
    return 0


# RabbitMQ Consumer
def callback(ch, method, properties, body):
    """Process received image message"""
    print("📩 Received image message...")

    try:
        # Decode the received message
        message = json.loads(body)
        image_bytes = base64.b64decode(message["base64String"])  # Original Image
        image_url = None

        # Load the image using PIL
        image_pil = Image.open(BytesIO(image_bytes))

        # Convert to NumPy array for YOLO processing
        image_np = np.array(image_pil)
        print(image_np)

        # yolo confidance score 
        CONFIDENCE_THRESHOLD = 0.20

        # Perform YOLO detection on the original image
        results_original = detector.model(image_np,conf=CONFIDENCE_THRESHOLD)

        # Rotate the image by -90 degrees and process again
        image_rotated = image_pil.rotate(-270, expand=True)
        image_rotated_np = np.array(image_rotated)
        results_rotated = detector.model(image_rotated_np,conf=CONFIDENCE_THRESHOLD)

        # Select the detection result with the highest confidence score
        if get_max_confidence(results_original) >= get_max_confidence(results_rotated):
            final_results = results_original
            final_image = image_np
        else:
            final_results = results_rotated
            final_image = image_rotated_np

        # Store final result
        results = final_results  # 🔥 This is the final detection result to be used

        
         # Store detected objects and bounding box coordinates separately
        detected_objects = []
        bounding_boxes = []

        for result in results:
            if not hasattr(result, "boxes"):  # Ensure result has boxes attribute
                continue

            for box in result.boxes:
                if not hasattr(box, "cls") or not hasattr(box, "xyxy") or not hasattr(box, "conf"):
                    continue  # Skip if required attributes are missing
                
                confidence = float(box.conf.item())  # Extract confidence score

                # **Filter detections based on confidence score**
                if confidence < CONFIDENCE_THRESHOLD:
                    continue  # Skip detections below threshold
                
                # Get class name
                class_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
                class_name = detector.model.names.get(class_id, "unknown")
                detected_objects.append(class_name)

                # Get bounding box coordinates
                x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())

                # Ensure bounding box values are within image dimensions
                width, height = image_pil.size
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(width, x2), min(height, y2)

                bounding_boxes.append((x1, y1, x2, y2))

        # If no objects detected, use "unknown"
        if not detected_objects:
            detected_objects = ["unknown"]
            bounding_boxes = []
            # Convert image back to Base64 for storage
            #print(image_bytes)# just for testing
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            #print(image_base64)# just for testing 

            # Upload image to MinIO and get URL
            image_url ,id = push_image_to_minio(image_base64, detected_objects)
            if not image_url:
                raise Exception("MinIO upload failed, image URL is None")

                

        # If no objects detected, use "unknown"
        if  detected_objects == ["unknown"]:
            # Prepare output message For mongodb
            # Remove image before inserting into MongoDB
            message_without_image = {k: v for k, v in message.items() if k != "base64String"}

            # Add additional fields
            additional_data = {
                "id":id,
                "image_url": image_url,  # ✅ Store the MinIO image URL instead of base64
                "bounding_boxes": bounding_boxes,  # ✅ Add detected bounding boxes
                "detected_objects":detected_objects
            }
            output_message_for_mongo = {**message_without_image, **additional_data}
            # Store in MongoDB
            # Initialize MongoDB Handler
            mongo_handler = MongoDBHandler(config.MONGO_URI, config.MONGO_DB, config.MONGO_COLLECTION)
            # Inside the `callback` function, update the MongoDB insert line:
            mongo_handler.insert_message(output_message_for_mongo)
            


        # Prepare output message with MinIO URL and bounding boxes
        output_message_for_RabbitMQ = {
            **message,  # Include all original message data
            "image_url": image_url,  # ✅ Store the MinIO image URL instead of base64
            "bounding_boxes": bounding_boxes,  # ✅ Add detected bounding boxes
            "detected_objects":detected_objects
        }

        
        # Send Ditected object incident message to RabbitMQ queue
        if  detected_objects != ["unknown"]:
            metadata_json = json.dumps(output_message_for_RabbitMQ)
            channel.basic_publish(exchange='', routing_key=config.OUTPUT_QUEUE, body=metadata_json)
            print(f"✅ Processed image URL with metadata  sent to queue: {config.OUTPUT_QUEUE}")


    except Exception as e:
        print(f"⚠️ Error processing message: {e}")


if __name__ == "__main__":
    # Initialize detector
    detector = ObjectDetectorYOLOv8(config.YOLO_WEIGHTS_PATH)

    # Setup RabbitMQ connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(config.RABBITMQ_HOST, config.RABBITMQ_PORT))
    channel = connection.channel()

    # Declare queues
    channel.queue_declare(queue=config.INPUT_QUEUE)
    channel.queue_declare(queue=config.OUTPUT_QUEUE)

    # Start consuming messages
    channel.basic_consume(queue=config.INPUT_QUEUE, on_message_callback=callback, auto_ack=True)  # Change auto_ack to True later
    print("🔄 Waiting for images...")
    channel.start_consuming()
