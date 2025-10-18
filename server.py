from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from main import get_truthfulness_score
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

@app.route('/')
def serve_frontend():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check."""
    return jsonify({
        "status": "healthy",
        "model_loaded": True,
        "model_name": "bert-tiny-finetuned-fake-news-detection + english-sarcasm-detector"
    })

@app.route('/predict-url', methods=['POST'])
def predict_url():
    """Analyze news article from URL using your main.py function."""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "ValidationError", "detail": "URL is required"}), 400
        
        url = data['url']
        logger.info(f"🌟 Analyzing article from URL: {url}")
        
        # Call your main.py function directly
        result = get_truthfulness_score(url)
        
        # Check for errors
        if 'error' in result:
            return jsonify({"error": "AnalysisError", "detail": result['error']}), 400
        
        # Convert to frontend format
        if result['label'] == 'Fake':
            frontend_label = "FAKE"
            frontend_score = result['score']
        else:
            frontend_label = "REAL"
            frontend_score = 1.0 - result['score']
        
        response = {
            "label": frontend_label,
            "score": round(frontend_score, 4),
            "extracted_text": f"Article analyzed with {result.get('chunks_processed', 1)} text chunks processed.",
            "planet": result.get('planet', '☀️ Sun')
        }
        
        logger.info(f"✨ Analysis complete: {frontend_label} (confidence: {frontend_score:.4f})")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"💥 Analysis failed: {str(e)}")
        return jsonify({"error": "InternalServerError", "detail": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)