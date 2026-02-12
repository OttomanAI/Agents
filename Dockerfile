FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Jupyter port
EXPOSE 8888

# Default: run the CLI agent.  Override with docker-compose for Jupyter.
CMD ["python", "main.py"]
