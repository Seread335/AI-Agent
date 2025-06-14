import re
from typing import Dict, List, Optional
import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)

class TaskRouter:
    def __init__(self):
        # Rule-based classification patterns
        self.classification_patterns = {
            "coding": [
                r'\b(code|function|class|algorithm|programming|debug|implement|script|api)\b',
                r'\b(python|javascript|java|c\+\+|html|css|sql|react)\b',
                r'\b(bug|error|syntax|compile|runtime)\b'
            ],
            "analysis": [
                r'\b(analyze|analysis|compare|evaluate|assess|study|research)\b',
                r'\b(data|statistics|metrics|performance|trend|pattern)\b',
                r'\b(why|how|what|explain|reason|cause)\b'
            ],
            "creative": [
                r'\b(write|create|generate|design|story|poem|article|content)\b',
                r'\b(creative|imagination|artistic|novel|original)\b',
                r'\b(brainstorm|ideate|inspire)\b'
            ],
            "research": [
                r'\b(research|investigate|find|search|explore|discover)\b',
                r'\b(information|facts|source|reference|study|paper)\b',
                r'\b(latest|recent|current|news|update)\b'
            ],
            "general": [
                r'\b(help|question|ask|tell|explain|what|how|when|where)\b',
                r'\b(general|basic|simple|quick)\b'
            ]
        }
        
        self.task_models = {
            "coding": ["agentica", "qwen_coder"],
            "analysis": ["deepseek", "qwen3"],
            "creative": ["qwen3"],
            "research": ["deepseek"],
            "general": ["qwen3"]
        }
        
        self.specialization_weights = {
            "coding": {
                "agentica": 0.8,
                "qwen_coder": 0.9,
                "deepseek": 0.4,
                "qwen3": 0.5
            },
            "analysis": {
                "deepseek": 0.9,
                "qwen3": 0.7,
                "agentica": 0.5,
                "qwen_coder": 0.6
            },
            "creative": {
                "qwen3": 0.9,
                "deepseek": 0.6,
                "agentica": 0.3,
                "qwen_coder": 0.3
            },
            "research": {
                "deepseek": 0.9,
                "qwen3": 0.7,
                "agentica": 0.4,
                "qwen_coder": 0.4
            },
            "general": {
                "qwen3": 0.8,
                "deepseek": 0.7,
                "agentica": 0.5,
                "qwen_coder": 0.5
            }
        }

    async def classify_task(self, 
                          query: str, 
                          context: Optional[Dict] = None) -> Dict:
        """
        Classify the task type using rule-based approach
        """
        try:
            query_lower = query.lower()
            category_scores = {}
            
            # Calculate scores for each category
            for category, patterns in self.classification_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, query_lower))
                    score += matches
                
                # Normalize score
                category_scores[category] = score / len(patterns)
            
            # Sort by score
            sorted_categories = sorted(category_scores.items(), 
                                     key=lambda x: x[1], 
                                     reverse=True)
            
            primary_category = sorted_categories[0][0]
            primary_score = sorted_categories[0][1]
            
            # If no clear match, default to general
            if primary_score == 0:
                primary_category = "general"
                primary_score = 0.5
            else:
                # Normalize score to 0-1 range
                primary_score = min(primary_score, 1.0)
            
            # Determine if multiple models needed
            needs_multiple_models = (
                primary_score < 0.8 or
                len([score for _, score in sorted_categories if score > 0.3]) > 1
            )

            return {
                "primary_category": primary_category,
                "confidence": primary_score,
                "secondary_categories": [cat for cat, _ in sorted_categories[1:3]],
                "needs_multiple_models": needs_multiple_models,
                "complexity": self._estimate_complexity(query),
                "context_requirements": self._analyze_context_requirements(query, context)
            }

        except Exception as e:
            logger.error(f"Error in task classification: {str(e)}")
            return {
                "primary_category": "general",
                "confidence": 0.5,
                "secondary_categories": [],
                "needs_multiple_models": False,
                "complexity": "medium",
                "context_requirements": {"requires_context": False}
            }

    def select_models(self, task_info: Dict) -> List[str]:
        """
        Select appropriate models based on task classification
        """
        try:
            primary_category = task_info["primary_category"]
            needs_multiple_models = task_info["needs_multiple_models"]
            complexity = task_info["complexity"]

            selected_models = []
            
            # Add primary model
            primary_model = self._get_best_model(primary_category, complexity)
            selected_models.append(primary_model)
            
            # Add secondary model if needed
            if needs_multiple_models and task_info.get("secondary_categories"):
                secondary_category = task_info["secondary_categories"][0]
                secondary_model = self._get_best_model(secondary_category, complexity)
                if secondary_model not in selected_models:
                    selected_models.append(secondary_model)

            return selected_models

        except Exception as e:
            logger.error(f"Error in model selection: {str(e)}")
            return ["qwen3"]

    def _estimate_complexity(self, query: str) -> str:
        """
        Estimate task complexity based on query characteristics
        """
        # Length factor
        word_count = len(query.split())
        length_score = min(word_count / 50, 1.0)  # Normalize to max 1.0
        
        # Complexity indicators
        high_complexity_indicators = [
            "complex", "advanced", "sophisticated", "optimize", "architecture", 
            "system", "integration", "comprehensive", "detailed", "thorough"
        ]
        
        medium_complexity_indicators = [
            "multiple", "several", "various", "different", "compare", 
            "analyze", "implement", "design", "create"
        ]
        
        high_score = sum(1 for ind in high_complexity_indicators 
                        if ind.lower() in query.lower()) / len(high_complexity_indicators)
        
        medium_score = sum(1 for ind in medium_complexity_indicators 
                          if ind.lower() in query.lower()) / len(medium_complexity_indicators)
        
        total_score = (length_score + high_score * 2 + medium_score) / 4
        
        if total_score > 0.6:
            return "high"
        elif total_score > 0.3:
            return "medium"
        else:
            return "low"

    def _analyze_context_requirements(self, 
                                   query: str, 
                                   context: Optional[Dict]) -> Dict:
        """
        Analyze context requirements
        """
        context_indicators = {
            "previous": ["previous", "before", "last time", "earlier", "continue"],
            "code": ["code", "function", "class", "implementation", "script"],
            "system": ["system", "architecture", "design", "structure"],
            "user": ["my", "preference", "setting", "profile", "remember"]
        }
        
        required_context = {
            "requires_context": False,
            "context_types": []
        }
        
        query_lower = query.lower()
        for context_type, indicators in context_indicators.items():
            if any(ind in query_lower for ind in indicators):
                required_context["requires_context"] = True
                required_context["context_types"].append(context_type)
        
        return required_context

    def _get_best_model(self, category: str, complexity: str) -> str:
        """
        Get the best model for category and complexity
        """
        available_models = self.task_models.get(category, ["qwen3"])
        weights = self.specialization_weights.get(category, {})
        
        if not weights:
            return available_models[0]
        
        # Complexity multiplier
        complexity_multiplier = {
            "low": 0.9,
            "medium": 1.0,
            "high": 1.1
        }.get(complexity, 1.0)
        
        # Calculate weighted scores
        best_model = None
        best_score = 0
        
        for model in available_models:
            score = weights.get(model, 0.5) * complexity_multiplier
            if score > best_score:
                best_score = score
                best_model = model
        
        return best_model or "qwen3"
    
    def get_fallback_model(self, task_info: Dict) -> str:
        """
        Get fallback model when primary is unavailable
        """
        primary_category = task_info["primary_category"]
        available_models = set(self.task_models[primary_category])
        
        # Remove unhealthy models from consideration
        if hasattr(self, 'unhealthy_models'):
            available_models = available_models - self.unhealthy_models
        
        if not available_models:
            # If no models available for category, use general model
            return "qwen3"
            
        # Get best available model
        best_model = None
        best_score = 0
        
        for model in available_models:
            score = self.specialization_weights[primary_category].get(model, 0)
            if score > best_score:
                best_score = score
                best_model = model
                
        return best_model or "qwen3"

    def handle_task_failure(self, 
                          task_info: Dict,
                          failed_model: str) -> List[str]:
        """
        Handle task routing failure and provide alternative models
        """
        # Get primary and secondary categories
        primary_cat = task_info["primary_category"]
        secondary_cats = task_info.get("secondary_categories", [])
        
        # Get all potential models
        potential_models = set()
        potential_models.update(self.task_models.get(primary_cat, []))
        for cat in secondary_cats:
            potential_models.update(self.task_models.get(cat, []))
            
        # Remove failed model
        potential_models.discard(failed_model)
        
        # Sort by specialization weight
        model_scores = []
        for model in potential_models:
            score = max(
                self.specialization_weights.get(cat, {}).get(model, 0)
                for cat in [primary_cat] + secondary_cats
            )
            model_scores.append((model, score))
            
        # Return top 2 alternatives
        alternatives = sorted(model_scores, key=lambda x: x[1], reverse=True)
        return [model for model, _ in alternatives[:2]]

    def adjust_routing_weights(self, 
                             model_id: str,
                             task_category: str,
                             success: bool,
                             response_quality: float):
        """
        Dynamically adjust routing weights based on model performance
        """
        if task_category not in self.specialization_weights:
            return
            
        if model_id not in self.specialization_weights[task_category]:
            return
            
        current_weight = self.specialization_weights[task_category][model_id]
        
        # Adjust weight based on success and quality
        if success:
            # Increase weight slightly for successful responses
            adjustment = 0.01 * response_quality
        else:
            # Decrease weight for failures
            adjustment = -0.02
            
        # Apply adjustment with bounds
        new_weight = max(0.1, min(0.9, current_weight + adjustment))
        self.specialization_weights[task_category][model_id] = new_weight