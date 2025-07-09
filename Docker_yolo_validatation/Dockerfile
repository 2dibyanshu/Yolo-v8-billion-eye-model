# # Use an official Python image
# FROM python:3.11-slim

# # Install system dependencies (e.g. for OpenCV)
# RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# # Set working directory
# WORKDIR /app

# # Copy only requirements.txt first (better caching)
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir --timeout=100 -r requirements.txt;

# RUN apt install -y nodejs 
# RUN npm install pm2 -g 

# # Copy wait-for-it script (download wait-for-it.sh and place it in your project root)
# COPY wait-for-it.sh /app/wait-for-it.sh
# RUN chmod +x /app/wait-for-it.sh

# # Copy the rest of the application files
# COPY . .

# # Expose any required ports 
# EXPOSE 5672  
# EXPOSE 9000  
# EXPOSE 27017 

# # Use wait-for-it to pause until dependent containers are ready,
# # then start the YOLO script.
# CMD ["/app/wait-for-it.sh", "mongodb:27017", "--", \
#      "/app/wait-for-it.sh", "rabbitmq:5672", "--", \
#      "pm2-runtime", "--interpreter","python3", "--", "optimize_yolo_mongodb.py"]

# Use an official Python image
FROM python:3.11-slim

# Install system dependencies and nodejs
RUN apt-get update && \
    apt-get install -y curl gnupg libgl1 libglib2.0-0 && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pm2 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements.txt first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --timeout=100 -r requirements.txt

# Copy wait-for-it script
COPY wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

# Copy the rest of the application files
COPY . .

# Expose any required ports
EXPOSE 5672  
EXPOSE 9000  
EXPOSE 27017 

# Entry point command
CMD ["/app/wait-for-it.sh", "mongodb:27017", "--", \
     "/app/wait-for-it.sh", "rabbitmq:5672", "--", \
     "pm2-runtime", "--interpreter", "python3", "--", "optimize_yolo_mongodb.py"]
