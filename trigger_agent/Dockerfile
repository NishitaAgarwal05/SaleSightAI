# Use slim Python image
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Command to run on container start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload", "--port", "8001"]