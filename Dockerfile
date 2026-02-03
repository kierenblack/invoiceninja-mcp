# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy your requirements (or just install the basics)
RUN pip install mcp[server] fastmcp requests

# Copy your server script into the container
COPY server.py .

# Expose the port your SSE server runs on
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]