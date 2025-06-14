from typing import Dict, List, Optional
import time
import json
import os
from collections import deque
from utils.logger import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    def __init__(self, metrics_file: str = "logs/metrics.json"):
        self.metrics_file = metrics_file
        self.metrics_window = 1000  # Store last 1000 interactions
        self.response_times = deque(maxlen=self.metrics_window)
        self.model_usage = {}
        self.task_stats = {}
        self.error_counts = {}
        
        # Load existing metrics if available
        self._load_metrics()

    def log_interaction(self, 
                       task_info: Dict,
                       models: List[str],
                       response_time: Optional[float] = None) -> None:
        """
        Log performance metrics for an interaction
        """
        try:
            # Record response time
            if response_time:
                self.response_times.append(response_time)

            # Update model usage
            for model in models:
                if model not in self.model_usage:
                    self.model_usage[model] = {
                        "total_calls": 0,
                        "average_response_time": 0,
                        "error_count": 0
                    }
                self.model_usage[model]["total_calls"] += 1
                if response_time:
                    current_avg = self.model_usage[model]["average_response_time"]
                    total_calls = self.model_usage[model]["total_calls"]
                    new_avg = (
                        (current_avg * (total_calls - 1) + response_time) / 
                        total_calls
                    )
                    self.model_usage[model]["average_response_time"] = new_avg

            # Update task statistics
            category = task_info.get("primary_category", "unknown")
            if category not in self.task_stats:
                self.task_stats[category] = {
                    "count": 0,
                    "success_rate": 100.0,
                    "average_confidence": 0.0
                }
            
            self.task_stats[category]["count"] += 1
            confidence = task_info.get("confidence", 1.0)
            current_avg = self.task_stats[category]["average_confidence"]
            total_count = self.task_stats[category]["count"]
            new_avg = (
                (current_avg * (total_count - 1) + confidence) / 
                total_count
            )
            self.task_stats[category]["average_confidence"] = new_avg

            # Save metrics periodically
            self._save_metrics()

        except Exception as e:
            logger.error(f"Error logging performance metrics: {str(e)}")

    def log_error(self, 
                  error_type: str, 
                  model_id: Optional[str] = None) -> None:
        """
        Log an error occurrence
        """
        try:
            if error_type not in self.error_counts:
                self.error_counts[error_type] = 0
            self.error_counts[error_type] += 1

            if model_id and model_id in self.model_usage:
                self.model_usage[model_id]["error_count"] += 1

            self._save_metrics()

        except Exception as e:
            logger.error(f"Error logging error metrics: {str(e)}")

    def get_performance_summary(self) -> Dict:
        """
        Get a summary of current performance metrics
        """
        try:
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )

            return {
                "average_response_time": avg_response_time,
                "total_interactions": sum(
                    stats["count"] for stats in self.task_stats.values()
                ),
                "model_usage": self.model_usage,
                "task_statistics": self.task_stats,
                "error_counts": self.error_counts
            }

        except Exception as e:
            logger.error(f"Error generating performance summary: {str(e)}")
            return {}

    def _save_metrics(self) -> None:
        """
        Save metrics to file
        """
        try:
            metrics = {
                "timestamp": time.time(),
                "model_usage": self.model_usage,
                "task_stats": self.task_stats,
                "error_counts": self.error_counts
            }

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)

            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")

    def _load_metrics(self) -> None:
        """
        Load metrics from file
        """
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    metrics = json.load(f)
                    self.model_usage = metrics.get("model_usage", {})
                    self.task_stats = metrics.get("task_stats", {})
                    self.error_counts = metrics.get("error_counts", {})

        except Exception as e:
            logger.error(f"Error loading metrics: {str(e)}")
            # Initialize empty metrics
            self.model_usage = {}
            self.task_stats = {}
            self.error_counts = {}
