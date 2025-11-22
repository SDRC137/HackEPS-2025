import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Paths setup
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from backend.backend_api import BackendOrchestrator

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes and origins

# Initialize Orchestrator
orchestrator = BackendOrchestrator()

@app.route('/api/start', methods=['POST'])
def start_session():
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
        
    try:
        result = orchestrator.start_session(prompt)
        return jsonify(result)
    except Exception as e:
        print(f"Error in start_session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
        
    try:
        result = orchestrator.process_feedback(message)
        return jsonify(result)
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    print("🚀 Server running on http://0.0.0.0:5001")
    app.run(debug=True, port=5001, host='0.0.0.0')
