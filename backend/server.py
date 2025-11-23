import os
import sys
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from backend/.env explicitly
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path, override=True)

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

@app.route('/api/images', methods=['GET'])
def get_images():
    neighborhood = request.args.get('neighborhood')
    if not neighborhood:
        return jsonify({"error": "No neighborhood provided"}), 400
    
    images = []
    
    # 1. Try Google Custom Search API (Preferred)
    # We try GOOGLE_API_KEY first, then fallback to GEMINI_API_KEY (as it's often the same Google Cloud Project)
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    google_cx = os.getenv("GOOGLE_CX")
    
    if google_key and google_cx and google_key != "tu_api_key":
        try:
            print(f"🔍 Searching Google Images for: {neighborhood}")
            query = f"{neighborhood} Los Angeles neighborhood scenic"
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={google_cx}&key={google_key}&searchType=image&num=5&imgSize=large&safe=active"
            
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    for item in data['items']:
                        images.append({
                            "url": item['link'],
                            "description": item.get('title', neighborhood),
                            "credit": {
                                "name": item.get('displayLink', 'Google Search'),
                                "link": item.get('contextLink', item['link'])
                            }
                        })
                    print(f"✅ Found {len(images)} images via Google.")
                    return jsonify({"images": images})
            else:
                print(f"⚠️ Google API Error: {response.text}")
        except Exception as e:
            print(f"⚠️ Error fetching Google images: {e}")

    # 2. Fallback to Unsplash (if Google fails or keys missing)
    print("⚠️ Falling back to Unsplash...")
    api_key = os.getenv("UNSPLASH_ACCESS_KEY")
    
    # If no key, return empty list (frontend will handle fallback/mock)
    if not api_key:
        print("⚠️ No UNSPLASH_ACCESS_KEY found in environment variables")
        return jsonify({"images": []})
        
    try:
        # Unsplash search strategy
        # 1. Try specific query: "{neighborhood} Los Angeles"
        queries_to_try = [
            f"{neighborhood} Los Angeles",
            f"{neighborhood} California",
            neighborhood,
            "Los Angeles" # Fallback to generic LA images
        ]
        
        for query in queries_to_try:
            url = f"https://api.unsplash.com/search/photos?query={query}&client_id={api_key}&per_page=5&orientation=landscape"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    for img in data['results']:
                        # Avoid duplicates if we are combining results (though here we just take the first good batch)
                        images.append({
                            "url": img['urls']['regular'],
                            "description": img['description'] or img['alt_description'] or neighborhood,
                            "credit": {
                                "name": img['user']['name'],
                                "link": img['user']['links']['html']
                            }
                        })
                    
                    # If we found at least 3 images, stop searching
                    if len(images) >= 3:
                        break
            
        return jsonify({"images": images[:5]}) # Return top 5
    except Exception as e:
        print(f"Error fetching images: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    print("🚀 Server running on http://0.0.0.0:5001")
    app.run(debug=True, port=5001, host='0.0.0.0')
