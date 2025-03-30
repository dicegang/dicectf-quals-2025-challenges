FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy biosim files
COPY biosim/ /app/biosim/

# Copy bioweb files
COPY bioweb/ /app/bioweb/

# Install biosim requirements if they exist
RUN if [ -f /app/biosim/requirements.txt ]; then \
    pip install --no-cache-dir -r /app/biosim/requirements.txt; \
    fi

# Install Flask server requirements
RUN pip install --no-cache-dir -r /app/bioweb/requirements.txt

# Install biosim requirements
RUN pip install --no-cache-dir -r /app/biosim/requirements.txt

# Create directory for public files if it doesn't exist
RUN mkdir -p /app/bioweb/public

# Create directory for experiments if it doesn't exist
RUN mkdir -p /app/biosim/experiments

# Install Node.js dependencies
RUN cd /app/bioweb/panel && npm install

# Build the panel
RUN cd /app/bioweb/panel && npm run build

# Install serve
RUN npm install -g serve

# Make sure SQLite database can be created and is persistent
VOLUME /app/bioweb/data
ENV DATABASE_PATH=/app/bioweb/data/experiments.db

# Expose ports
EXPOSE 3200
EXPOSE 3201

# Copy start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Run flask and serve the panel
CMD ["/app/start.sh"]