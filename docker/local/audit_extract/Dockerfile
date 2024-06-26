# Use an official Python runtime as a parent image
FROM python:3.11-slim AS audit-extraction

# Specify python version
ENV PYTHON_VERSION=3.11

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev micro nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY ./docker/local/audit_extract/requirements.txt ./
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --default-timeout=100 -r requirements.txt

# Add english pipeline
RUN python -m spacy download en_core_web_sm

EXPOSE 8085

COPY ./code .

# Run Uvicorn to serve the FastAPI application
CMD ["uvicorn", "extract.inference:app", "--host", "0.0.0.0", "--port", "8085"]
