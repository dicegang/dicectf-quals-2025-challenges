import os
import json
import time
import base64
import sqlite3
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
import threading
import uuid
from flask_socketio import join_room, emit
from flask import render_template_string
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


# Initialize Flask app
app = Flask(__name__, static_folder='panel/build/', static_url_path='/')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=300, ping_interval=60)

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///experiments.db')
Session = sessionmaker(bind=engine)

class ExperimentResult(Base):
    __tablename__ = 'experiment_results'

    id = Column(String, primary_key=True)
    experiment_name = Column(String, nullable=False)
    input_data = Column(Text, nullable=False)
    output_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)


@app.route('/api/experiments', methods=['GET'])
def get_experiments():
    """Get list of available experiments."""

    return jsonify([
        {
            'id': 'diffusion',
            'name': 'Diffusion',
            'model': 'bios',
            'expected_duration': 69
        },
        {
            'id': 'transcription',
            'name': 'Transcription',
            'model': 'bios',
            'expected_duration': 1111
        },
        {
            'id': 'translation',
            'name': 'Translation',
            'model': 'bios_plus',
            'expected_duration': 105
        },
    ])


def run_experiment_proxy(experiment_id, input_data, run_id):
    input_b64 = base64.b64encode(input_data.encode('latin-1')).decode()

    cmd = [
        'python3',
        '/app/biosim/run.py',
        '--experiment',
        f'/app/biosim/experiments/{experiment_id}.json',
        '--input_b64',
        input_b64
    ]

    print(cmd)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    output_data = None
    
    # Process output
    for line in iter(process.stdout.readline, ''):
        if line.strip():
            try:
                update = json.loads(line)
                # Emit update via socketio
                print(f'experiment_update: {update}')
                socketio.emit(f'experiment_update', {
                    'run_id': run_id,
                    'status': 'running',
                    'update': update
                }, to=run_id)
                socketio.sleep(0)
                
                # If experiment completed, store the result
                if update.get('status') == 'completed':
                    output_data = update.get('output', '')
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line}")
    
    # Process errors
    stderr = process.stderr.read()
    if stderr:
        error_data = {'error': stderr}
        socketio.emit(f'experiment-update', {
            'run_id': run_id,
            'status': 'error',
            'error': error_data
        }, to=run_id)
        socketio.sleep(0)

    # Wait for process to complete
    process.wait()
    
    session = Session()
    experiment_result = ExperimentResult(
        id=run_id,
        experiment_name=experiment_id,
        input_data=input_data,
        output_data=output_data
    )
    session.add(experiment_result)
    session.commit()
    session.close()


@socketio.on('run_experiment')
def run_experiment(data):
    """Run an experiment asynchronously."""
    experiment_id = data.get('experiment')
    input_data = data.get('input', '')
    
    if not experiment_id:
        return jsonify({'error': 'Experiment ID is required'}), 400
    
    # Generate a unique run ID
    run_id = str(uuid.uuid4())

    join_room(run_id)

    socketio.emit('run_starting', {
        'run_id': run_id,
    }, to=run_id)
    
    socketio.start_background_task(run_experiment_proxy, experiment_id, input_data, run_id)


@app.route('/api/results/<run_id>', methods=['GET'])
def get_result(run_id):
    """Get a specific experiment result by run ID."""
    session = Session()
    experiment_result = session.query(ExperimentResult).filter_by(id=run_id).first()
    session.close()

    if not experiment_result:
        return jsonify({'error': 'Result not found'}), 404
    
    return jsonify({
        'id': experiment_result.id,
        'experiment_name': experiment_result.experiment_name,
        'input_data': experiment_result.input_data,
        'output_data': experiment_result.output_data,
        'created_at': experiment_result.created_at.isoformat()
    })


@app.route('/test_payload')
def test_payload():
    # Render raw html
    return render_template_string('''
    <html>
        <body>
            <p>Result: a<svg/onload=eval(name)></p>
        </body>
    </html>
    ''')


@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def on_join(data):
    print('Client joined room', data)
    join_room(data['room'])

@app.get('/')
def index():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return app.send_static_file('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3200))
    # Print server info
    print(f"Starting Flask server on port {port}")
    # Start the socket.io server
    socketio.run(app, host='0.0.0.0', port=port)
