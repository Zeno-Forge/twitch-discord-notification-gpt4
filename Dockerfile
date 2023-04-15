# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the application files into the container
COPY . /app

# Make port 8000 available to the world outside this container
ENV PORT=8000

# Run Gunicorn when the container launches
CMD ["python", "wsgi.py"]
