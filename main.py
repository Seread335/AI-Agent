from fastapi import FastAPI, WebSocket, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
import time
from typing import Optional, Dict, List
import asyncio
import json
from core.agent import AIAgent
from utils.logger import get_logger

logger = get_logger(__name__)

# Prometheus metrics
REQUESTS_TOTAL = Counter(
    "requests_total",
    "Total number of requests by endpoint and status",
    ["endpoint", "status"]
)

RESPONSE_TIME = Histogram(
    "response_time_seconds",
    "Response time in seconds",
    ["endpoint"]
)

app = FastAPI(
    title="AI Agent API",
    description="A sophisticated AI Agent system for intelligent task processing",
    version="1.0.0"
)

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Initialize AI Agent
agent = AIAgent()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict] = None
    user_id: Optional[str] = None
    stream: Optional[bool] = False

class QueryResponse(BaseModel):
    status: str
    response: Dict
    task_info: Optional[Dict] = None
    models_used: Optional[List[str]] = None

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query and return the response
    """
    try:
        response = await agent.process_query(
            query=request.query,
            context=request.context,
            user_id=request.user_id
        )
        
        return QueryResponse(
            status="success",
            response=response["response"],
            task_info=response.get("task_info"),
            models_used=response.get("models_used")
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming responses
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive query
            data = await websocket.receive_text()
            request = json.loads(data)
            
            # Process query with streaming
            async for response_chunk in agent.handle_stream(
                query=request["query"],
                context=request.get("context"),
                user_id=request.get("user_id")
            ):
                await websocket.send_json(response_chunk)

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies core components
    """
    try:
        # Check core components
        components_status = {
            "agent": "healthy",
            "models": {},
            "database": "healthy"
        }
        
        # Check model endpoints
        for model_id in agent.model_manager.models:
            try:
                await agent.model_manager._ensure_session()
                components_status["models"][model_id] = "healthy"
            except Exception as e:
                components_status["models"][model_id] = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy",
            "components": components_status,
            "timestamp": time.time()
        }
    except Exception as e:
        return Response(
            content=json.dumps({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }),
            status_code=500,
            media_type="application/json"
        )

@app.get("/metrics/performance")
async def get_performance_metrics():
    """
    Get detailed performance metrics
    """
    try:
        metrics = agent.performance_monitor.get_performance_summary()
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching metrics: {str(e)}"
        )

@app.on_event("startup")
async def startup_event():
    """
    Initialize resources on startup
    """
    # Any initialization code here
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup resources on shutdown
    """
    # Cleanup code here
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
