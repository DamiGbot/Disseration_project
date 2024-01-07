# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
# RUN apk add py3-scikit-learn
RUN pip install --upgrade pip
RUN pip install scikit-learn
RUN pip install  -r requirements.txt

# Copy the rest of your application's code
COPY . /app/

# Run your application
CMD ["python", "app/routes.py"]
