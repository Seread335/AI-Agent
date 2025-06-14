from fastapi import APIRouter, HTTPException
from typing import Dict
import time
from core.agent import AIAgent
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

class HealthCheck:
    def __init__(self, agent: AIAgent):
        self.agent = agent

    async def check_model_health(self) -> Dict:
        """
        Check health of all AI models
        """
        model_health = {}
        try:
            results = await self.agent.model_manager.verify_models()
            for model_id, status in results.items():
                model_health[model_id] = {
                    "status": status["status"],
                    "latency": status.get("latency", 0),
                    "last_check": time.time()
                }
        except Exception as e:
            logger.error(f"Error checking model health: {str(e)}")
            model_health["error"] = str(e)
        return model_health

    async def check_system_health(self) -> Dict:
        """
        Check overall system health including memory usage and performance
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "cpu_percent": process.cpu_percent(),
                "memory_usage": {
                    "rss": memory_info.rss / 1024 / 1024,  # MB
                    "vms": memory_info.vms / 1024 / 1024,  # MB
                },
                "threads": process.num_threads(),
                "connections": len(process.connections())
            }
        except ImportError:
            return {"status": "psutil not available"}
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {"error": str(e)}

    def check_database_health(self) -> Dict:
        """
        Check database connections and performance
        """
        # Placeholder for database health checks
        return {
            "status": "healthy",
            "connections": "ok",
            "latency": 0
        }

    async def full_health_check(self) -> Dict:
        """
        Perform a comprehensive health check of all components
        """
        model_health = await self.check_model_health()
        system_health = await self.check_system_health()
        db_health = self.check_database_health()
        
        # Get performance metrics
        performance_metrics = self.agent.performance_monitor.get_performance_summary()

        return {
            "status": "healthy" if all(
                m.get("status") == "healthy" for m in model_health.values()
                if isinstance(m, dict) and "status" in m
            ) else "degraded",
            "timestamp": time.time(),
            "components": {
                "models": model_health,
                "system": system_health,
                "database": db_health
            },
            "performance": performance_metrics
        }

@router.get("/health")
async def health_check(agent: AIAgent) -> Dict:
    """
    Comprehensive health check endpoint
    """
    try:
        checker = HealthCheck(agent)
        return await checker.full_health_check()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/health/models")
async def model_health(agent: AIAgent) -> Dict:
    """
    Check only model health
    """
    try:
        checker = HealthCheck(agent)
        return await checker.check_model_health()
    except Exception as e:
        logger.error(f"Model health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Model health check failed: {str(e)}"
        )

@router.get("/health/system")
async def system_health(agent: AIAgent) -> Dict:
    """
    Check only system health
    """
    try:
        checker = HealthCheck(agent)
        return await checker.check_system_health()
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"System health check failed: {str(e)}"
        )
