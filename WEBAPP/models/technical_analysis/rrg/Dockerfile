# Dockerfile

# Use the official Pathway image
FROM pathwaycom/pathway:latest

# Set the working directory
WORKDIR /app

# Copy the requirements file and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the pipeline script
COPY . .

# Command to run when the container starts
CMD ["python", "rrg_calculator.py"]