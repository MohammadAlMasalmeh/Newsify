# Design Document

## Overview

The Fake News Detection System is a lightweight FastAPI-based web service that provides real-time news authenticity classification. The system uses a pretrained transformer model from Hugging Face to analyze text input and return binary classification results (FAKE/REAL) with confidence scores. The architecture prioritizes simplicity, performance, and maintainability while being ready for frontend integration.

## Architecture

The system follows a layered architecture pattern:

```
┌─────────────────────────────────────┐
│           FastAPI Layer             │
│  (API endpoints, request/response)  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         Service Layer               │
│    (Business logic, validation)    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│          Model Layer                │
│   (Hugging Face pipeline wrapper)  │
└─────────────────────────────────────┘
```

### Key Design Principles

- **Single Responsibility**: Each component has a clear, focused purpose
- **Dependency Injection**: Model instance is injected into services for testability
- **Error Isolation**: Comprehensive error handling at each layer
- **Stateless Design**: No session state, enabling horizontal scaling
- **Configuration-Driven**: Environment-based configuration for flexibility

## Components and Interfaces

### 1. FastAPI Application (`app.py`)

**Purpose**: HTTP server setup, routing, and middleware configuration

**Key Components**:
- Application factory pattern for initialization
- CORS middleware for frontend integration
- Global exception handlers
- Health check endpoint
- API documentation configuration

### 2. Prediction Service (`services/prediction_service.py`)

**Purpose**: Business logic for text classification and result formatting

**Interface**:
```python
class PredictionService:
    def __init__(self, model_wrapper: ModelWrapper)
    async def predict_news_authenticity(self, text: str) -> PredictionResult
    def _validate_input(self, text: str) -> None
    def _format_prediction(self, raw_result: dict) -> PredictionResult
```

**Responsibilities**:
- Input validation (minimum length, content checks)
- Calling the model wrapper
- Result formatting and normalization
- Business rule enforcement

### 3. Model Wrapper (`models/model_wrapper.py`)

**Purpose**: Abstraction layer over Hugging Face transformers pipeline

**Interface**:
```python
class ModelWrapper:
    def __init__(self, model_name: str)
    def load_model(self) -> None
    def predict(self, text: str) -> dict
    def is_loaded(self) -> bool
```

**Responsibilities**:
- Model initialization and loading
- Pipeline configuration
- Raw prediction execution
- Model health monitoring

### 4. API Models (`models/api_models.py`)

**Purpose**: Pydantic models for request/response validation

**Models**:
```python
class PredictionRequest(BaseModel):
    text: str = Field(min_length=10, max_length=10000)

class PredictionResponse(BaseModel):
    label: Literal["FAKE", "REAL"]
    score: float = Field(ge=0.0, le=1.0)

class ErrorResponse(BaseModel):
    error: str
    detail: str
```

### 5. Configuration (`config.py`)

**Purpose**: Centralized configuration management

**Settings**:
- Model configuration (name, cache directory)
- Server configuration (host, port, workers)
- API configuration (rate limiting, timeouts)
- Logging configuration

## Data Models

### Input Data Flow

1. **HTTP Request**: JSON payload with news text
2. **Validation**: Pydantic model validation
3. **Processing**: Text preprocessing and tokenization (handled by transformers)
4. **Prediction**: Model inference
5. **Response**: Formatted JSON response

### Model Integration

The system integrates with the `Pulk17/Fake-News-Detection` model using the following approach:

```python
# Model loading strategy
pipeline = transformers.pipeline(
    "text-classification",
    model="Pulk17/Fake-News-Detection",
    tokenizer="Pulk17/Fake-News-Detection",
    device=0 if torch.cuda.is_available() else -1,
    return_all_scores=True
)
```

### Response Format Standardization

The model's raw output is normalized to ensure consistent response format:
- Map model labels to "FAKE"/"REAL"
- Extract highest confidence score
- Round scores to 4 decimal places
- Ensure score represents confidence in the predicted label

## Error Handling

### Error Categories and Responses

1. **Input Validation Errors** (400 Bad Request)
   - Empty or too short text
   - Invalid JSON format
   - Missing required fields

2. **Model Errors** (500 Internal Server Error)
   - Model loading failures
   - Prediction timeouts
   - Memory allocation errors

3. **System Errors** (503 Service Unavailable)
   - Model not loaded
   - Resource exhaustion
   - External dependency failures

### Error Response Format

```json
{
  "error": "ValidationError",
  "detail": "Text must be at least 10 characters long"
}
```

### Graceful Degradation

- Model loading retries with exponential backoff
- Circuit breaker pattern for repeated failures
- Health check endpoint for monitoring
- Detailed logging for debugging

## Testing Strategy

### Unit Testing

- **Service Layer**: Mock model wrapper, test business logic
- **Model Wrapper**: Test model loading and prediction formatting
- **API Models**: Validate Pydantic model constraints
- **Configuration**: Test environment variable handling

### Integration Testing

- **API Endpoints**: Test full request/response cycle
- **Model Integration**: Test with actual Hugging Face model
- **Error Scenarios**: Test error handling and edge cases

### Performance Testing

- **Response Time**: Ensure predictions complete within 5 seconds
- **Memory Usage**: Monitor model memory consumption
- **Concurrent Requests**: Test multiple simultaneous predictions

### Test Data Strategy

- Use diverse news samples (real and fake)
- Include edge cases (very short/long text, special characters)
- Test with various confidence score ranges
- Validate against known model outputs

## Deployment Considerations

### Local Development

- Use uvicorn with auto-reload for development
- Environment-based configuration
- Docker support for consistent environments
- Clear setup documentation

### Production Readiness

- Gunicorn with uvicorn workers for production
- Model caching and warm-up strategies
- Monitoring and logging integration
- Security headers and rate limiting

### Frontend Integration

- CORS configuration for web frontend
- OpenAPI/Swagger documentation
- Consistent error response format
- WebSocket support for real-time updates (future enhancement)