# 🌟 Fake News Detection API

A celestial-themed FastAPI backend for detecting fake news using machine learning. This API leverages a pretrained Hugging Face transformer model to analyze news text and classify it as either "FAKE" or "REAL" with confidence scores.

## ✨ Features

- **Real-time Detection**: Analyze news articles in under 5 seconds
- **High Accuracy**: Uses the pretrained `Pulk17/Fake-News-Detection` model
- **RESTful API**: Clean, documented endpoints with automatic OpenAPI docs
- **Confidence Scoring**: Get probability scores (0.0-1.0) for predictions
- **Error Handling**: Comprehensive error responses and validation
- **CORS Enabled**: Ready for frontend integration

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository** (or download the files)
   ```bash
   git clone <your-repo-url>
   cd fake-news-detection
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Verify it's working**
   - Open http://localhost:8000/docs for interactive API documentation
   - Check health: http://localhost:8000/health

## 📡 API Usage

### Predict News Authenticity

**Endpoint:** `POST /predict`

**Request Body:**
```json
{
  "text": "Your news article text here..."
}
```

**Response:**
```json
{
  "label": "FAKE",
  "score": 0.8542
}
```

### Example with curl

```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Breaking news: Scientists discover new planet in our solar system with signs of alien life."
     }'
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "Pulk17/Fake-News-Detection"
}
```

## 🛠️ Configuration

The API can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `Pulk17/Fake-News-Detection` | Hugging Face model to use |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `PREDICTION_TIMEOUT` | `5` | Prediction timeout in seconds |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MIN_TEXT_LENGTH` | `10` | Minimum text length |
| `MAX_TEXT_LENGTH` | `10000` | Maximum text length |

Create a `.env` file in the project root to set these values:

```env
MODEL_NAME=Pulk17/Fake-News-Detection
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Development

### Project Structure

```
fake-news-detection/
├── app.py                 # FastAPI application
├── main.py               # Server entry point
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── models/
│   ├── __init__.py
│   ├── api_models.py     # Pydantic request/response models
│   └── model_wrapper.py  # Hugging Face model wrapper
├── services/
│   ├── __init__.py
│   └── prediction_service.py  # Business logic
└── README.md
```

### Running in Development Mode

```bash
# With auto-reload enabled
python main.py

# Or with uvicorn directly
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 🚨 Error Handling

The API provides detailed error responses:

### Validation Errors (400)
```json
{
  "error": "ValidationError",
  "detail": "Text must be at least 10 characters long"
}
```

### Server Errors (500)
```json
{
  "error": "PredictionError", 
  "detail": "Failed to process prediction request"
}
```

### Service Unavailable (503)
```json
{
  "error": "ServiceUnavailable",
  "detail": "Service unavailable: Model not loaded"
}
```

## 🎯 Input Requirements

- **Minimum text length**: 10 characters
- **Maximum text length**: 10,000 characters
- **Format**: Plain text (no special formatting required)
- **Language**: English (model trained on English news)

## 🔍 Troubleshooting

### Common Issues

1. **Model loading fails**
   - Ensure you have internet connection for first-time model download
   - Check available disk space (model is ~500MB)
   - Verify Python version compatibility

2. **Slow predictions**
   - First prediction may be slower due to model initialization
   - Consider using GPU if available (automatic detection)

3. **Memory issues**
   - Model requires ~2GB RAM minimum
   - Close other applications if running low on memory

4. **Port already in use**
   ```bash
   # Use a different port
   uvicorn app:app --port 8001
   ```

### Logs

Check the console output for detailed logs. Increase verbosity with:
```bash
LOG_LEVEL=DEBUG python main.py
```

## 🌟 Next Steps

This backend is ready for frontend integration! Consider adding:

- Web interface for easy testing
- Batch processing endpoints
- User authentication
- Rate limiting
- Caching for improved performance
- Deployment to cloud platforms

## 📄 License

This project is open source and available under the MIT License.