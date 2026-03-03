"""Routing engine - Core decision logic"""

from typing import Dict, Any
from ..api.schemas import ChatCompletionRequest
from .rules import RoutingRules


class RouteEngine:
    """
    OrchexEngine's brain - decides which model to use for each request.

    MVP: Rule-based routing
    Future: Confidence-driven, cost-aware optimization
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rules_config = config.get("rules", {})

    def select_model(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """
        Select the appropriate model based on routing rules.

        Returns:
            dict: {
                "target": "local" | "cloud",
                "reason": str,
                "can_fallback": bool
            }
        """
        # Evaluate rules
        evaluation = RoutingRules.evaluate(request)

        # Get rule thresholds from config
        max_local_tokens = self.rules_config.get("max_input_tokens_local", 2000)
        json_requires_cloud = self.rules_config.get("json_requires_cloud", True)
        code_requires_cloud = self.rules_config.get("code_requires_cloud", True)

        # Decision logic
        target = "local"
        reason = "Default to local model"

        # Rule 1: Check token count
        if evaluation["estimated_tokens"] > max_local_tokens:
            target = "cloud"
            reason = f"Input too long ({evaluation['estimated_tokens']} > {max_local_tokens} tokens)"

        # Rule 2: Code generation requires cloud model
        elif evaluation["is_code"] and code_requires_cloud:
            target = "cloud"
            reason = "Code generation requires cloud model"

        # Rule 3: JSON output requires cloud model
        elif evaluation["is_json"] and json_requires_cloud:
            target = "cloud"
            reason = "JSON output requires cloud model"

        # Rule 4: Complex reasoning (optional - could go either way)
        elif evaluation["is_reasoning"]:
            # For MVP, still try local first
            reason = "Reasoning request - attempting local model"
            target = "local"

        return {
            "target": target,
            "reason": reason,
            "can_fallback": target == "local",  # Can fallback to cloud if local fails
            "evaluation": evaluation
        }

    def get_routing_info(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """
        Get detailed routing information for logging/telemetry.

        Returns:
            dict: Complete routing decision info
        """
        decision = self.select_model(request)
        evaluation = RoutingRules.evaluate(request)

        return {
            **decision,
            "rules_triggered": {
                "code_detected": evaluation["is_code"],
                "json_detected": evaluation["is_json"],
                "reasoning_detected": evaluation["is_reasoning"],
                "token_estimate": evaluation["estimated_tokens"],
            }
        }
