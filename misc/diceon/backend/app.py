import os
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sever import run_graph

# Initialize Flask app
app = Flask(__name__, static_folder='public/', static_url_path='/')
app.config['SECRET_KEY'] = 'your-secret-key'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

Base = declarative_base()
class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(String, primary_key=True)
    prompt = Column(Text, nullable=False)
    responses = Column(Text, nullable=False)  # Stored as JSON
    timestamp = Column(DateTime, default=datetime.utcnow)


# Database setup
import time
while True:
    try:
        engine = create_engine('postgresql+psycopg2://postgres:lmaolmaolmao@db:5432')
        Session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        break
    except Exception as e:
        print(f"Database connection error: {e}")
        time.sleep(5)  # Wait before retrying

def run_llm_task(prompt, conversation_id):
    messages = run_graph(prompt, conversation_id, socketio, app.logger)

    session = Session()
    conversation = Conversation(
        id=conversation_id,
        prompt=prompt,
        responses=json.dumps(messages)
    )
    session.add(conversation)
    session.commit()
    session.close()

# SocketIO event handler for prompt submission
@socketio.on('submit_prompt')
def handle_socket_prompt(data):
    prompt = data.get('prompt')

    if not prompt:
        emit('error', {'message': 'Prompt is required'})
        return

    # Generate a unique conversation ID
    conversation_id = str(uuid.uuid4())

    # Join the client to the conversation room
    join_room(conversation_id)

    # Send initial acknowledgment
    emit('prompt_received', {
        'conversation_id': conversation_id,
        'message': 'Processing started'
    })

    app.logger.debug(f"Prompt received: {prompt}")

    # Start processing in a background task
    # This works better from a SocketIO event handler
    socketio.start_background_task(run_llm_task, prompt, conversation_id)

@app.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    session = Session()
    conversation = session.query(Conversation).filter_by(id=conversation_id).first()
    session.close()

    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    return jsonify({
        'id': conversation.id,
        'prompt': conversation.prompt,
        'responses': json.loads(conversation.responses),
        'timestamp': conversation.timestamp.isoformat()
    })

@app.get('/')
def index():
    return app.send_static_file('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return app.send_static_file('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def on_join(data):
    room = data.get('conversation_id')
    if room:
        print(f"Client joined room: {room}")

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")