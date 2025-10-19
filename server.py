from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from main import get_truthfulness_score
from mediacloud_integration import analyze_articles_by_planet
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
            "planet": result.get('planet', '☀️ Sun'),
            "fake_news_score": round(result.get('fake_news_score', 0), 4),
            "sarcasm_score": round(result.get('sarcasm_score', 0), 4)
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": "InternalServerError", "detail": str(e)}), 500

@app.route('/api/similar-articles', methods=['POST'])
def search_similar_articles():
    """Search for similar articles using MediaCloud and analyze their credibility."""
    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({"error": "ValidationError", "detail": "Request body is required"}), 400
        
        # Validate required parameters
        query = data.get('query', '').strip()
        if not query:
            return jsonify({"error": "ValidationError", "detail": "Query parameter is required"}), 400
        
        # Validate optional parameters
        articles_per_planet = data.get('articles_per_planet', 1)
        try:
            articles_per_planet = int(articles_per_planet)
            if articles_per_planet < 1 or articles_per_planet > 10:
                return jsonify({"error": "ValidationError", "detail": "articles_per_planet must be between 1 and 10"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "ValidationError", "detail": "articles_per_planet must be a valid integer"}), 400
        
        logger.info(f"Searching for similar articles with query: {query}, articles_per_planet: {articles_per_planet}")
        
        # Call MediaCloud integration function
        result = analyze_articles_by_planet(query, articles_per_planet)
        
        # Check for errors in the result
        if 'error' in result:
            error_detail = result['error']
            if 'MediaCloud API key not configured' in error_detail:
                return jsonify({"error": "ConfigurationError", "detail": "MediaCloud API key is not configured"}), 503
            else:
                return jsonify({"error": "MediaCloudError", "detail": error_detail}), 500
        
        # Format response for frontend
        response = {
            "query": result['query'],
            "results_by_planet": result['results_by_planet'],
            "total_articles": result['total_articles'],
            "articles_per_planet_limit": result['articles_per_planet_limit'],
            "search_timestamp": result['search_timestamp'],
            "cache_hit": result.get('cache_hit', False)
        }
        
        # Add message if no articles found
        if result['total_articles'] == 0:
            response["message"] = result.get('message', 'No articles found for the given query')
        
        logger.info(f"Found {result['total_articles']} articles for query: {query}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in similar articles search: {e}")
        return jsonify({"error": "InternalServerError", "detail": str(e)}), 500

@app.route('/api/analyze-article', methods=['POST'])
def analyze_single_article():
    """Analyze a single article for detailed credibility comparison."""
    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({"error": "ValidationError", "detail": "Request body is required"}), 400
        
        # Validate required parameters
        url = data.get('url', '').strip()
        if not url:
            return jsonify({"error": "ValidationError", "detail": "URL parameter is required"}), 400
        
        # Validate URL format
        if not (url.startswith('http://') or url.startswith('https://')):
            return jsonify({"error": "ValidationError", "detail": "URL must start with http:// or https://"}), 400
        
        logger.info(f"Analyzing single article: {url}")
        
        # Call existing truthfulness analysis function
        result = get_truthfulness_score(url)
        
        # Check for errors
        if 'error' in result:
            return jsonify({"error": "AnalysisError", "detail": result['error']}), 400
        
        # Format detailed response for credibility comparison
        response = {
            "url": url,
            "credibility_score": result['score'],
            "fake_news_score": result['fake_news_score'],
            "sarcasm_score": result['sarcasm_score'],
            "planet": result['planet'],
            "label": result['label'],
            "confidence": result['confidence'],
            "chunks_processed": result.get('chunks_processed', 1),
            "analysis_timestamp": datetime.now().isoformat(),
            "detailed_scores": {
                "fake_news_probability": result['fake_news_score'],
                "sarcasm_probability": result['sarcasm_score'],
                "overall_credibility": result['score'],
                "credibility_rating": result['planet']
            }
        }
        
        logger.info(f"Article analysis complete for {url}: {result['planet']} ({result['score']:.3f})")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in single article analysis: {e}")
        return jsonify({"error": "InternalServerError", "detail": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)