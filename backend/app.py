import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS

from processor import start_processing

# Set frontend directory path relative to this backend file
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BACKEND_DIR, '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(BACKEND_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

ALLOWED_EXTENSIONS = {'pdf'}

# In-memory dictionary removed, using database instead

import time

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import database

def cleanup_old_tasks():
    """
    Cleans up tasks older than 1 hour from the database.
    Can be run via a scheduler, cron job, or triggered periodically.
    """
    database.cleanup_old_tasks()

# Trigger an initial database task cleanup on application startup
try:
    cleanup_old_tasks()
    print("[Database] Successfully completed initial task cleanup on startup.")
except Exception as e:
    print(f"[Database] Startup task cleanup warning: {e}")

# Serve frontend HTML
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Serve other frontend files (JS, CSS)
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(FRONTEND_DIR, path)

from storage import save_file, initialize_storage
from vector_store import initialize_vector_store

# Initialize MinIO
initialize_storage()
# Initialize Qdrant
initialize_vector_store()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.pdf'):
        task_id = str(uuid.uuid4())
        
        # Read file data in memory and upload to MinIO
        file_data = file.read()
        try:
            save_file(task_id, file_data)
        except Exception as e:
            return jsonify({'error': f'Failed to upload to storage: {str(e)}'}), 500

        # Create task in database
        database.create_task(task_id)

        # Enqueue the processing job to the Redis/RQ worker queue.
        # Enqueuing is a fast, non-blocking operation (~ms), making the spawn of a separate
        # OS-level thread redundant. The background processing is managed asynchronously by RQ.
        import processor
        try:
            processor.start_processing(task_id)
        except Exception as e:
            return jsonify({'error': f'Failed to enqueue processing job: {str(e)}'}), 500

        return jsonify({'message': 'File uploaded and processing started', 'task_id': task_id}), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = database.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
        
    return jsonify(task), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    # For development only; in production use a proper WSGI server
    app.run(host='0.0.0.0', port=5000, debug=True)

