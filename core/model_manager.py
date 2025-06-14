from typing import Dict, List, Optional, AsyncGenerator
import aiohttp
import json
from utils.logger import get_logger
from utils.config import load_config
from utils.api_verifier import APIVerifier
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

class ModelManager:
    def __init__(self):
        self.config = load_config()
        
        # Updated with correct API endpoints (cần verify với documentation thực tế)
        self.models = {
            "deepseek": {
                "name": "DeepSeek R1 0528",
                "api_key": "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",
                "endpoint": "https://api.deepseek.com/chat/completions",  # Corrected endpoint
                "model": "deepseek-chat",
                "specialty": ["reasoning", "analysis", "complex_problem_solving", "research"]
            },
            "qwen3": {
                "name": "Qwen3 8B",
                "api_key": "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",
                "endpoint": "https://api.siliconflow.cn/v1/chat/completions",  # Common endpoint for Qwen
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "specialty": ["general_conversation", "creative_writing", "summarization", "translation"]
            },
            "agentica": {
                "name": "Agentica Deepcoder 14B",
                "api_key": "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",
                "endpoint": "https://api.agentica.ai/v1/chat/completions",  # Assumed endpoint
                "model": "agentica-deepcoder-14b",
                "specialty": ["coding", "debugging", "code_review", "technical_documentation"]
            },
            "qwen_coder": {
                "name": "Qwen2.5 Coder 32B Instruct",
                "api_key": "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",
                "endpoint": "https://api.siliconflow.cn/v1/chat/completions",
                "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
                "specialty": ["advanced_coding", "system_architecture", "code_optimization", "algorithm_design"]
            }
        }
        
        self.session = None
        self.api_verifier = APIVerifier()
        self.unhealthy_models = set()

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config["performance"]["timeout_seconds"])
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def verify_models(self) -> Dict[str, Dict]:
        """
        Verify all model endpoints are healthy
        """
        results = await self.api_verifier.verify_all_endpoints(self.models)
        
        # Update unhealthy models set
        self.unhealthy_models.clear()
        for model_id, status in results.items():
            if status["status"] != "healthy":
                self.unhealthy_models.add(model_id)
                logger.warning(f"Model {model_id} is unhealthy: {status}")
        
        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_response(self, 
                          model_id: str, 
                          query: str, 
                          context: Optional[Dict] = None) -> Dict:
        """
        Get response from specific model with proper error handling
        """
        if model_id in self.unhealthy_models:
            logger.warning(f"Attempting to use unhealthy model {model_id}")
            
        start_time = time.time()
        await self._ensure_session()
        
        model = self.models.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {model['api_key']}",
            "Content-Type": "application/json",
            "User-Agent": "AI-Agent/1.0"
        }

        # Prepare messages
        messages = []
        
        # Add system context if available
        if context and context.get("history"):
            # Add recent conversation history
            recent_history = context["history"][-3:]  # Last 3 interactions
            for interaction in recent_history:
                messages.append({"role": "user", "content": interaction["query"]})
                messages.append({"role": "assistant", "content": interaction["response"]["response"]})
        
        # Add current query
        messages.append({"role": "user", "content": query})

        # Prepare payload
        payload = {
            "model": model.get("model", "default"),
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "stream": False
        }

        try:
            async with self.session.post(
                model["endpoint"],
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 429:  # Rate limit
                    logger.warning(f"Rate limit hit for {model_id}")
                    raise Exception("Rate limit exceeded")
                
                response.raise_for_status()
                result = await response.json()
                
                response_time = time.time() - start_time
                
                # Extract response content
                if "choices" in result and result["choices"]:
                    content = result["choices"][0]["message"]["content"]
                else:
                    raise Exception("Invalid response format")
                
                return {
                    "model_id": model_id,
                    "response": content,
                    "confidence": self._calculate_confidence(result),
                    "response_time": response_time,
                    "token_usage": result.get("usage", {})
                }

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error for {model_id}: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {model_id}: {str(e)}")
            raise Exception(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting response from {model_id}: {str(e)}")
            raise

    async def get_streaming_response(self, 
                                   model_id: str, 
                                   query: str,
                                   context: Optional[Dict] = None) -> AsyncGenerator:
        """
        Get streaming response from model
        """
        await self._ensure_session()
        model = self.models.get(model_id)
        
        if not model:
            raise ValueError(f"Model {model_id} not found")

        headers = {
            "Authorization": f"Bearer {model['api_key']}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

        # Prepare messages (similar to get_response)
        messages = []
        if context and context.get("history"):
            recent_history = context["history"][-3:]
            for interaction in recent_history:
                messages.append({"role": "user", "content": interaction["query"]})
                messages.append({"role": "assistant", "content": interaction["response"]["response"]})
        
        messages.append({"role": "user", "content": query})

        payload = {
            "model": model.get("model", "default"),
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True
        }

        try:
            async with self.session.post(
                model["endpoint"],
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                
                accumulated_content = ""
                
                async for line in response.content:
                    if not line:
                        continue
                        
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(data_str)
                            
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    accumulated_content += content
                                    yield {
                                        "model_id": model_id,
                                        "content": content,
                                        "accumulated_content": accumulated_content,
                                        "finished": False
                                    }
                                
                                # Check if finished
                                if data["choices"][0].get("finish_reason"):
                                    yield {
                                        "model_id": model_id,
                                        "content": "",
                                        "accumulated_content": accumulated_content,
                                        "finished": True
                                    }
                                    break
                                    
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Error in streaming response from {model_id}: {str(e)}")
            yield {
                "model_id": model_id,
                "content": "",
                "error": str(e),
                "finished": True
            }

    def _calculate_confidence(self, response_data: Dict) -> float:
        """
        Calculate confidence score from response data
        """
        # Basic confidence calculation
        # Can be improved based on actual API response format
        
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            
            # Check for explicit confidence if available
            if "confidence" in choice:
                return float(choice["confidence"])
            
            # Calculate based on response characteristics
            content = choice.get("message", {}).get("content", "")
            
            # Longer responses might indicate higher confidence
            length_factor = min(len(content) / 1000, 1.0)
            
            # Base confidence
            base_confidence = 0.8
            
            return min(base_confidence + length_factor * 0.2, 1.0)
        
        return 0.5  # Default confidence

    async def health_check(self, model_id: str) -> Dict:
        """
        Check if model is healthy and responsive
        """
        try:
            test_response = await self.get_response(
                model_id=model_id,
                query="Hello, are you working?"
            )
            
            return {
                "model_id": model_id,
                "status": "healthy",
                "response_time": test_response.get("response_time", 0)
            }
            
        except Exception as e:
            return {
                "model_id": model_id,
                "status": "unhealthy",
                "error": str(e)
            }

    async def close(self):
        """
        Close aiohttp session
        """
        if self.session:
            await self.session.close()
            self.session = None