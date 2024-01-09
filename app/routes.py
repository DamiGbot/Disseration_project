from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException, InternalServerError
import logging
import traceback
from logging.handlers import RotatingFileHandler

from app.tasks import sleep_test, embed

app = Flask(__name__)

@app.route('/') 
def hello_world():
    return 'Hello, World!'


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions"""
    response = e.get_response()
    response.data = jsonify({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    }).data
    response.content_type = "application/json"
    return response


def setup_logging():
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

setup_logging()


@app.errorhandler(Exception)
def handle_exception(e):
    trace = traceback.format_exc()
    app.logger.error(f'Unhandled Exception: {e}\n{trace}')
    return jsonify(error="An internal error occurred."), 500 

def validate_json(*expected_keys):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not request.is_json:
                abort(400, description="Invalid content type. JSON required.")
            json_data = request.get_json()
            for key in expected_keys:
                if key not in json_data:
                    abort(400, description=f"Missing key: {key}")
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/test', methods=['POST'])
def json_method():
    # Check if the request has the JSON content-type
    if request.is_json:
        # Parse the JSON data from request
        data = request.get_json()
        
        # Access the data using the keys
        students = data['student']
        supervisors = data['supervisor']

        # Process the data as needed (here, we're just returning it back)
        return jsonify({'message': 'JSON received', 'students': students, 'supervisors': supervisors}), 200
    else:
        # Return an error message if the received data is not in JSON format
        return jsonify({'message': 'Request must be JSON'}), 400

@app.route('/process-data', methods=['POST'])
@validate_json('student', 'supervisor')
def process_data():
    data = request.get_json()

    if 'student' not in data or 'supervisor' not in data:
        return jsonify({'message': 'Missing student or supervisor data in request'}), 400
    
    task = embed.delay(data)
    return {"task": task.id}


@app.route('/sleep_test', methods=['POST'])
def sleep_test_route():
    task = sleep_test.delay()
    return {"task": task.id}

@app.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = embed.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is pending'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info),  
        }
    return jsonify(response)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)

