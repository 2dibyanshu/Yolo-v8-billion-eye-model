import boto3
import base64
import io
import re
import json
from datetime import datetime
import config  # Import configuration file

# MinIO Configuration
MINIO_URL = config.MINIO_ENDPOINT  # Example: "http://192.168.1.116:9000"
ACCESS_KEY = config.MINIO_ACCESS_KEY  
SECRET_KEY = config.MINIO_SECRET_KEY
BUCKET_NAME = config.BUCKET_NAME

# Initialize MinIO client using boto3
s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)
# def ensure_bucket_exists():
#     """
#     Checks if the bucket exists in MinIO, creates it if not, and makes it public.
#     """
#     try:
#         s3_client.create_bucket(
#         Bucket=BUCKET_NAME,
#         CreateBucketConfiguration={'LocationConstraint': 'your-region'} ) # Example: 'us-east-2'

#     except Exception:
#         print(f"⚠️ Bucket '{BUCKET_NAME}' not found. Creating it now...")
#         try:
#             s3_client.create_bucket(Bucket=BUCKET_NAME)
#             print(f"✅ Bucket '{BUCKET_NAME}' exists.")
#             print(f"✅ Bucket '{BUCKET_NAME}' created successfully.")

#             # Make the bucket public by applying a bucket policy
#             public_policy = {
#                 "Version": "2012-10-17",
#                 "Statement": [
#                     {
#                         "Effect": "Allow",
#                         "Principal": "*",
#                         "Action": ["s3:GetObject"],
#                         "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
#                     }
#                 ]
#             }

#             s3_client.put_bucket_policy(
#                 Bucket=BUCKET_NAME,
#                 Policy=json.dumps(public_policy)
#             )
#             print(f"✅ Bucket '{BUCKET_NAME}' is now public.")

#         except Exception as err:
#             print(f"⚠️ Error creating bucket: {err}")
#             raise

def get_next_filename(detected_object):
    """
    Generate the next filename in the format Year/detected_object/incremental_number.jpg.
    """
    current_year = datetime.now().year

    # Ensure detected_object is a string (handle lists)
    if isinstance(detected_object, list):
        detected_object = "_".join(map(str, detected_object))
    elif not isinstance(detected_object, str):
        raise ValueError("Detected object must be a string or a list of strings.")

    object_name = "uk_05_"# changed according to the new logic of only saving the unknown class with a code : uk_05
    prefix = f"{current_year}/{object_name}/"

    # List objects with the given prefix
    objects = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

    # Extract existing indexes
    existing_indexes = []
    if "Contents" in objects:
        for obj in objects["Contents"]:
            match = re.search(rf"{prefix}(\d+)\.jpg", obj["Key"])
            if match:
                existing_indexes.append(int(match.group(1)))

    # Determine next index
    next_index = max(existing_indexes) + 1 if existing_indexes else 1

    return f"{prefix}{next_index}" # only for image f"{prefix}{next_index}.jpg"

def push_image_to_minio(base64_image: str, detected_object: str):
    """
    Uploads a Base64 encoded image to MinIO and returns its public URL.

    :param base64_image: Base64 encoded image string
    :param detected_object: Name of detected object(s)
    :return: Public URL of uploaded image
    """
    #ensure_bucket_exists()  # Ensure the bucket exists before uploading
    
    id = get_next_filename(detected_object)  # Get the next filename
    object_name = f"{id}.jpg"  # Append .jpg extension


    try:
        # Remove the data header if present (e.g., "data:image/jpeg;base64,")
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        # Decode the Base64 string to bytes
        image_bytes = base64.b64decode(base64_image)

        # Create a BytesIO buffer from the decoded bytes
        image_buffer = io.BytesIO(image_bytes)

        # Upload the image to MinIO
        s3_client.upload_fileobj(
            image_buffer,
            BUCKET_NAME,
            object_name,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
        print(f"✅ Image uploaded to MinIO: {object_name}")

        # Construct and return the URL
        image_url = f"{MINIO_URL}/{BUCKET_NAME}/{object_name}"
        return [image_url ,id]

    except Exception as e:
        print(f"⚠️ Error uploading image to MinIO: {e}")
        return None
