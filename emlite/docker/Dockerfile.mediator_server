# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /mediator

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the server will listen on
EXPOSE 50051

# Start the server
CMD ["python", "-m", "emlite.grpc.emlite-mediator-server"]