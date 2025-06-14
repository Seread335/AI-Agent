# API Documentation

## Endpoints

### Query Endpoint

```http
POST /query
```

Process a query through the AI Agent system.

**Request Body:**
```json
{
    "query": "string",
    "context": {
        "additional": "context"
    },
    "user_id": "string",
    "stream": false
}
```

**Response:**
```json
{
    "status": "success",
    "response": {
        "content": "string",
        "confidence": 0.95
    },
    "task_info": {
        "primary_category": "string",
        "confidence": 0.8,
        "models_used": ["model1", "model2"]
    }
}
```

### WebSocket Streaming

```http
WebSocket /ws
```

Real-time streaming responses from the AI Agent.

**Message Format:**
```json
{
    "query": "string",
    "context": {},
    "user_id": "string"
}
```

**Stream Response Format:**
```json
{
    "model_id": "string",
    "content": "string",
    "finished": false
}
```

### Health Check

```http
GET /health
```

Check system health status.

**Response:**
```json
{
    "status": "healthy",
    "components": {
        "agent": "healthy",
        "models": {
            "model1": "healthy",
            "model2": "healthy"
        },
        "database": "healthy"
    },
    "timestamp": 1623456789.123
}
```

### Performance Metrics

```http
GET /metrics/performance
```

Get detailed performance metrics.

**Response:**
```json
{
    "status": "success",
    "metrics": {
        "average_response_time": 0.5,
        "total_interactions": 1000,
        "model_usage": {},
        "task_statistics": {}
    },
    "timestamp": 1623456789.123
}
```

## Error Handling

All endpoints follow a consistent error response format:

```json
{
    "status": "error",
    "detail": "Error message",
    "error_code": "ERROR_CODE"
}
```

Common error codes:
- `INVALID_REQUEST`: Invalid request format
- `MODEL_ERROR`: AI model processing error
- `RATE_LIMIT`: Rate limit exceeded
- `SERVER_ERROR`: Internal server error
