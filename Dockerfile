# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip uninstall -y Werkzeug Flask flask-cors gunicorn beautifulsoup4 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Make port 5000 available
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]