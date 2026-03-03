"""Pydantic schemas for API request/response"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class MessageRole(str, Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message"""
    role: MessageRole
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request"""
    model: str = Field(default="orchexengine", description="Model name")
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: Optional[bool] = Field(default=False)
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None


class Choice(BaseModel):
    """Chat completion choice"""
    index: int
    message: Message
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    """Token usage statistics"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]
