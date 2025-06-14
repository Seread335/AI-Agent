from typing import Dict, List, Optional
import asyncio
from core.model_manager import ModelManager
from core.task_router import TaskRouter
from core.response_synthesizer import ResponseSynthesizer
from utils.context_manager import ContextManager
from utils.performance_monitor import PerformanceMonitor
from utils.logger import get_logger

logger = get_logger(__name__)

class AIAgent:
    def __init__(self):
        self.model_manager = ModelManager()
        self.task_router = TaskRouter()
        self.response_synthesizer = ResponseSynthesizer()
        self.context_manager = ContextManager()
        self.performance_monitor = PerformanceMonitor()
        
    async def process_query(self, 
                          query: str, 
                          context: Optional[Dict] = None, 
                          user_id: Optional[str] = None) -> Dict:
        """
        Process a user query and return the appropriate response
        """
        try:
            # Update context
            conversation_context = self.context_manager.get_context(user_id)
            if context:
                conversation_context.update(context)

            # Classify task and get appropriate models
            task_info = await self.task_router.classify_task(query, conversation_context)
            selected_models = self.task_router.select_models(task_info)

            # Get responses from selected models
            model_responses = []
            tasks = []
            
            for model_id in selected_models:
                task = asyncio.create_task(
                    self.model_manager.get_response(
                        model_id=model_id,
                        query=query,
                        context=conversation_context
                    )
                )
                tasks.append(task)
            
            model_responses = await asyncio.gather(*tasks)

            # Synthesize final response
            final_response = await self.response_synthesizer.synthesize(
                model_responses=model_responses,
                task_info=task_info
            )

            # Update context with the interaction
            self.context_manager.update_context(
                user_id=user_id,
                query=query,
                response=final_response
            )

            # Log performance metrics
            self.performance_monitor.log_interaction(
                task_info=task_info,
                models=selected_models,
                response_time=final_response.get("response_time")
            )

            return {
                "status": "success",
                "response": final_response,
                "task_info": task_info,
                "models_used": selected_models
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "query": query
            }

    async def handle_stream(self, 
                          query: str, 
                          context: Optional[Dict] = None,
                          user_id: Optional[str] = None):
        """
        Handle streaming responses for real-time communication
        """
        try:
            task_info = await self.task_router.classify_task(query, context)
            selected_models = self.task_router.select_models(task_info)
            
            async for response_chunk in self.model_manager.get_streaming_response(
                model_id=selected_models[0],  # Use primary model for streaming
                query=query,
                context=context
            ):
                yield response_chunk

        except Exception as e:
            logger.error(f"Error in stream handling: {str(e)}")
            yield {
                "status": "error",
                "error": str(e)
            }
