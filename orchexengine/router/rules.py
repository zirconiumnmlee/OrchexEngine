"""Routing rules for model selection"""

import re
from typing import List, Tuple
from ..api.schemas import ChatCompletionRequest


class RoutingRules:
    """
    Define routing rules for model selection.

    Rules determine whether a request can be handled by a local model
    or should be routed to a cloud model.
    """

    # Keywords that indicate code generation
    CODE_KEYWORDS = [
        "write code", "generate code", "implement", "function",
        "class", "def ", "import ", "```python", "```javascript",
        "```java", "```cpp", "```rust", "```go"
    ]

    # Keywords that indicate JSON output request
    JSON_KEYWORDS = [
        "json", "JSON", "as a dictionary", "as an object",
        "structured data", "key-value"
    ]

    # Keywords that indicate complex reasoning
    REASONING_KEYWORDS = [
        "analyze", "compare", "evaluate", "critique", "review",
        "explain step by step", "chain of thought", "reasoning"
    ]

    @classmethod
    def detect_code_request(cls, messages: List[dict]) -> bool:
        """Check if the request involves code generation"""
        content = " ".join([m.get("content", "") for m in messages])
        content_lower = content.lower()

        # Check for code keywords
        for keyword in cls.CODE_KEYWORDS:
            if keyword.lower() in content_lower:
                return True

        # Check for code blocks
        if "```" in content:
            return True

        return False

    @classmethod
    def detect_json_request(cls, messages: List[dict]) -> bool:
        """Check if the request requires JSON output"""
        content = " ".join([m.get("content", "") for m in messages])
        content_lower = content.lower()

        for keyword in cls.JSON_KEYWORDS:
            if keyword.lower() in content_lower:
                return True

        return False

    @classmethod
    def detect_reasoning_request(cls, messages: List[dict]) -> bool:
        """Check if the request requires complex reasoning"""
        content = " ".join([m.get("content", "") for m in messages])
        content_lower = content.lower()

        for keyword in cls.REASONING_KEYWORDS:
            if keyword.lower() in content_lower:
                return True

        return False

    @classmethod
    def estimate_token_count(cls, messages: List[dict]) -> int:
        """
        Rough estimate of token count.

        Simple heuristic: ~4 characters per token
        """
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4

    @classmethod
    def evaluate(cls, request: ChatCompletionRequest) -> dict:
        """
        Evaluate request against all rules.

        Returns a dict with routing hints.
        """
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]

        return {
            "is_code": cls.detect_code_request(messages),
            "is_json": cls.detect_json_request(messages),
            "is_reasoning": cls.detect_reasoning_request(messages),
            "estimated_tokens": cls.estimate_token_count(messages),
        }
