# Use an official Python base image
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy backend code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your app runs on
EXPOSE 10000

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"] 