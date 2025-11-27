# Start with an official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code into the container
COPY ./sql_app /app/sql_app

# --- ADD THIS NEW LINE ---
# Run the database initialization script to create the tables.
RUN python -m sql_app.init_db

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application using Uvicorn
CMD ["uvicorn", "sql_app.main:app", "--host", "0.0.0.0", "--port", "8000"]