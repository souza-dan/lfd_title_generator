# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    curl -fsSL https://ollama.com/install.sh | sh


# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=server.py
ENV OLLAMA_MODEL=gemma

# Run server.py when the container launches
CMD /bin/sh -c "nohup ollama serve & python server.py"
