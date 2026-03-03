"""API routes"""

from fastapi import APIRouter, HTTPException
from litellm import completion
import time
import uuid

from .schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    Message,
    Usage,
    StreamChunk,
)
from ..router.engine import RouteEngine
from ..utils.config import get_config

router = APIRouter()
config = get_config()
route_engine = RouteEngine(config)


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Routes requests to local or cloud models based on routing rules.
    """
    route_decision = route_engine.select_model(request)

    # Get the appropriate model name for the provider
    if route_decision["target"] == "local":
        model_config = config["models"]["local"]
        model_name = f"{model_config['provider']}/{model_config['model']}"
        api_base = model_config.get("api_base")
        api_key = ""
    else:
        model_config = config["models"]["cloud"]
        model_name = f"{model_config['provider']}/{model_config['model']}"
        api_base = model_config['api_base']
        api_key = model_config['api_key']

    try:
        # Convert messages to LiteLLM format
        messages = [{"role": m.role.value, "content": m.content} for m in request.messages]

        # Call LiteLLM completion
        response = completion(
            model=model_name,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
            api_base=api_base,
            api_key = api_key
        )

        if request.stream:
            return stream_response(response, model_name)

        # Parse non-streaming response
        content = response.choices[0].message.content

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=model_name,
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content=content),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0
            )
        )

    except Exception as e:
        # Fallback logic
        if route_decision["target"] == "local" and route_decision.get("can_fallback"):
            # Try cloud model as fallback
            model_config = config["models"]["cloud"]
            model_name = f"{model_config['provider']}/{model_config['model']}"

            response = completion(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=request.stream,
            )

            content = response.choices[0].message.content

            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                created=int(time.time()),
                model=model_name,
                choices=[
                    Choice(
                        index=0,
                        message=Message(role="assistant", content=content),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0
                )
            )

        raise HTTPException(status_code=500, detail=str(e))


def stream_response(response, model_name: str):
    """Handle streaming response"""
    import json

    async def generate():
        for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                content = delta.content if delta else ""

                chunk_data = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": content or ""},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"

        yield "data: [DONE]\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(generate(), media_type="text/event-stream")
