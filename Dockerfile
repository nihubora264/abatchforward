# Set the base image
FROM python:3.11-slim as base

# Install required system packages
RUN apt-get update && \
    apt-get install -y git
RUN apt-get install build-essential python3-dev -y
# Set the working directory
WORKDIR /app

# Copy the requirements file to the working directory
COPY . .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the command to run the Python script
CMD [ "python", "main.py" ]