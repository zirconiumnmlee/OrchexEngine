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
from ..telemetry.collector import TelemetryCollector, LatencyTracker
from ..database.session import SessionLocal

router = APIRouter()
config = get_config()
route_engine = RouteEngine(config)


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Routes requests to local or cloud models based on routing rules.
    """
    # Start timing
    tracker = LatencyTracker()
    tracker.start()

    # Get routing decision
    route_decision = route_engine.select_model(request)
    routing_info = route_engine.get_routing_info(request)

    # Generate request ID
    request_id = str(uuid.uuid4())

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

    provider = route_decision["target"]
    routing_reason = route_decision["reason"]

    db = SessionLocal()
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
            api_key=api_key
        )

        if request.stream:
            # For streaming, we log the request but don't wait for completion
            tracker.stop()
            telemetry = TelemetryCollector.create_telemetry(
                request_id=request_id,
                selected_model=model_name,
                provider=provider,
                latency_ms=tracker.elapsed_ms(),
                routing_reason=routing_reason,
                metadata={"stream": True, **routing_info.get("rules_triggered", {})},
            )
            TelemetryCollector.log_request(telemetry, db)
            return stream_response(response, model_name, request_id)

        # Parse non-streaming response
        content = response.choices[0].message.content

        # Extract token usage
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        total_tokens = response.usage.total_tokens if response.usage else 0

        # Log telemetry
        tracker.stop()
        telemetry = TelemetryCollector.create_telemetry(
            request_id=request_id,
            selected_model=model_name,
            provider=provider,
            latency_ms=tracker.elapsed_ms(),
            routing_reason=routing_reason,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            metadata={**routing_info.get("rules_triggered", {})},
        )
        TelemetryCollector.log_request(telemetry, db)

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
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
        )

    except Exception as e:
        # Fallback logic
        if route_decision["target"] == "local" and route_decision.get("can_fallback"):
            # Try cloud model as fallback
            model_config = config["models"]["cloud"]
            model_name = f"{model_config['provider']}/{model_config['model']}"
            fallback_provider = "cloud"
            fallback_reason = f"Fallback from local: {str(e)}"

            response = completion(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=request.stream,
            )

            if request.stream:
                # Log streaming fallback
                tracker.stop()
                telemetry = TelemetryCollector.create_telemetry(
                    request_id=request_id,
                    selected_model=model_name,
                    provider=fallback_provider,
                    latency_ms=tracker.elapsed_ms(),
                    routing_reason=fallback_reason,
                    metadata={"stream": True, "was_fallback": True},
                )
                TelemetryCollector.log_request(telemetry, db)
                return stream_response(response, model_name, request_id)

            # Parse non-streaming fallback response
            content = response.choices[0].message.content

            # Extract token usage
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0

            # Log telemetry
            tracker.stop()
            telemetry = TelemetryCollector.create_telemetry(
                request_id=request_id,
                selected_model=model_name,
                provider=fallback_provider,
                latency_ms=tracker.elapsed_ms(),
                routing_reason=fallback_reason,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                metadata={"was_fallback": True},
            )
            TelemetryCollector.log_request(telemetry, db)

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
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=response.usage.total_tokens if response.usage else 0
                )
            )

        # Log error
        tracker.stop()
        telemetry = TelemetryCollector.create_telemetry(
            request_id=request_id,
            selected_model=model_name,
            provider=provider,
            latency_ms=tracker.elapsed_ms(),
            routing_reason=routing_reason,
            error=str(e),
        )
        TelemetryCollector.log_request(telemetry, db)

        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def stream_response(response, model_name: str, request_id: str = None):
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
