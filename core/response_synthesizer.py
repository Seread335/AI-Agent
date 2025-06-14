from typing import Dict, List
import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)

class ResponseSynthesizer:
    def __init__(self):
        self.confidence_threshold = 0.8

    async def synthesize(self, 
                        model_responses: List[Dict], 
                        task_info: Dict) -> Dict:
        """
        Synthesize final response from multiple model outputs
        """
        try:
            if len(model_responses) == 1:
                # Single model response
                return self._format_response(model_responses[0])

            # Multiple model responses need to be combined
            return await self._combine_responses(model_responses, task_info)

        except Exception as e:
            logger.error(f"Error in response synthesis: {str(e)}")
            # Return the first available response as fallback
            return self._format_response(model_responses[0])

    async def _combine_responses(self, 
                               responses: List[Dict], 
                               task_info: Dict) -> Dict:
        """
        Combine multiple model responses based on task type and confidence
        """
        primary_category = task_info["primary_category"]
        
        if primary_category == "coding":
            return await self._combine_code_responses(responses)
        elif primary_category == "analysis":
            return await self._combine_analysis_responses(responses)
        else:
            return await self._combine_general_responses(responses)

    async def _combine_code_responses(self, responses: List[Dict]) -> Dict:
        """
        Combine coding-related responses with special handling for code blocks
        """
        # Sort responses by confidence
        sorted_responses = sorted(responses, 
                                key=lambda x: x.get("confidence", 0), 
                                reverse=True)
        
        # Use the highest confidence response as base
        primary_response = sorted_responses[0]["response"]
        
        # Extract code blocks from other responses
        additional_code = []
        for resp in sorted_responses[1:]:
            code_blocks = self._extract_code_blocks(resp["response"])
            if code_blocks:
                additional_code.extend(code_blocks)

        # Combine responses
        combined_response = primary_response
        if additional_code:
            combined_response += "\n\nAlternative/Additional Implementations:\n"
            combined_response += "\n".join(additional_code)

        return {
            "response": combined_response,
            "confidence": sorted_responses[0].get("confidence", 1.0),
            "source": "multiple_models"
        }

    async def _combine_analysis_responses(self, responses: List[Dict]) -> Dict:
        """
        Combine analysis responses with focus on complementary insights
        """
        # Sort responses by confidence
        sorted_responses = sorted(responses, 
                                key=lambda x: x.get("confidence", 0), 
                                reverse=True)
        
        # Extract key points from each response
        all_points = []
        for resp in sorted_responses:
            points = self._extract_key_points(resp["response"])
            all_points.extend(points)

        # Remove duplicates while preserving order
        unique_points = []
        seen = set()
        for point in all_points:
            if point not in seen:
                unique_points.append(point)
                seen.add(point)

        # Combine into coherent response
        combined_response = "\n".join(unique_points)
        
        return {
            "response": combined_response,
            "confidence": max(r.get("confidence", 0) for r in responses),
            "source": "multiple_models"
        }

    async def _combine_general_responses(self, responses: List[Dict]) -> Dict:
        """
        Combine general responses using confidence-weighted approach
        """
        # Use highest confidence response as primary
        sorted_responses = sorted(responses, 
                                key=lambda x: x.get("confidence", 0), 
                                reverse=True)
        
        return self._format_response(sorted_responses[0])

    def _format_response(self, response: Dict) -> Dict:
        """
        Format a single model response
        """
        return {
            "response": response["response"],
            "confidence": response.get("confidence", 1.0),
            "source": response.get("model_id", "unknown")
        }

    def _extract_code_blocks(self, text: str) -> List[str]:
        """
        Extract code blocks from markdown text
        """
        blocks = []
        lines = text.split("\n")
        in_block = False
        current_block = []

        for line in lines:
            if line.startswith("```"):
                if in_block:
                    blocks.append("\n".join(current_block))
                    current_block = []
                in_block = not in_block
            elif in_block:
                current_block.append(line)

        return blocks

    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from analysis text
        """
        points = []
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered lists
            if line.startswith(("- ", "* ", "• ", "1.", "2.", "3.")):
                points.append(line)
            # Look for complete sentences that might be key points
            elif line and line[0].isupper() and line[-1] in ".!?":
                points.append(line)

        return points
