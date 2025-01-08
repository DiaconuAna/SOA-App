# Use the Node.js base image
FROM node:18

# Install Python, pip, venv, and necessary build tools
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv python3-dev build-essential libpq-dev && \
    apt-get clean

# Set the working directory in the container
WORKDIR /usr/src/app

# Create and activate a Python virtual environment
RUN python3 -m venv /venv

# Copy project files into the container
COPY . .

# Install Python dependencies into the virtual environment
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Set the PATH to include the virtual environment
ENV PATH="/venv/bin:$PATH"

# Install Node.js dependencies
RUN npm install

# Expose the port for Serverless Offline
EXPOSE 3000

# Command to run Serverless Offline
CMD ["npx", "serverless", "offline", "--host", "0.0.0.0"]
