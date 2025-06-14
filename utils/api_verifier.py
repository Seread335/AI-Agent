from typing import Dict, Optional
import aiohttp
import json
from utils.logger import get_logger

logger = get_logger(__name__)

class APIVerifier:
    def __init__(self):
        self.session = None
        self.verification_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def verify_endpoint(self, url: str, api_key: str, 
                            test_prompt: str = "test") -> Dict:
        """
        Verify an API endpoint is responsive and working correctly
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Simple test query
            payload = {
                "messages": [{"role": "user", "content": test_prompt}],
                "temperature": 0.7,
                "max_tokens": 50
            }

            async with self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            ) as response:
                response.raise_for_status()
                result = await response.json()

                return {
                    "status": "healthy",
                    "latency": response.elapsed.total_seconds(),
                    "response_code": response.status,
                    "model_response": bool(result.get("choices"))
                }

        except aiohttp.ClientResponseError as e:
            return {
                "status": "error",
                "error_type": "api_error",
                "status_code": e.status,
                "message": str(e)
            }
        except aiohttp.ClientError as e:
            return {
                "status": "error",
                "error_type": "connection_error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "unknown_error",
                "message": str(e)
            }

    async def verify_all_endpoints(self, models: Dict) -> Dict[str, Dict]:
        """
        Verify all model endpoints
        """
        results = {}
        for model_id, model_info in models.items():
            results[model_id] = await self.verify_endpoint(
                url=model_info["endpoint"],
                api_key=model_info["apiKey"]
            )
        return results

    async def close(self):
        """
        Close the aiohttp session
        """
        if self.session:
            await self.session.close()
            self.session = None
