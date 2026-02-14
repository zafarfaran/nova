"""Instrumentation wrapper for LLM providers to track metrics and logs."""

import inspect
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from opentelemetry import trace

from app.core.llm_costs import calculate_llm_cost
from app.core.metrics import (
    llm_cost_total,
    llm_errors_total,
    llm_request_duration,
    llm_requests_total,
    llm_tokens_total,
)
from app.core.metrics_config import get_log_level_for_section, is_logging_enabled, should_log

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def extract_token_usage(response: Any, provider: str) -> tuple[int, int]:
    """Extract token usage from LLM response.
    
    Args:
        response: LLM API response object
        provider: Provider name (openai, anthropic)
        
    Returns:
        Tuple of (input_tokens, output_tokens)
    """
    if provider == "openai":
        if hasattr(response, "usage"):
            usage = response.usage
            return (
                usage.prompt_tokens if hasattr(usage, "prompt_tokens") else 0,
                usage.completion_tokens if hasattr(usage, "completion_tokens") else 0,
            )
    elif provider == "anthropic":
        if hasattr(response, "usage"):
            usage = response.usage
            return (
                usage.input_tokens if hasattr(usage, "input_tokens") else 0,
                usage.output_tokens if hasattr(usage, "output_tokens") else 0,
            )
    
    return (0, 0)


def get_source_location() -> tuple[str, str]:
    """Get the source location (file and function) from the call stack.
    
    Returns:
        Tuple of (section, source) where:
        - section: High-level section (e.g., "document_processing", "chat", "validation")
        - source: Source location in format "module:function" or "file:function"
    """
    # Walk up the stack to find the caller (skip this function and track_call)
    frame = inspect.currentframe()
    try:
        # Go up 2 frames: get_source_location -> track_call -> actual caller
        caller_frame = frame.f_back.f_back if frame.f_back else None
        if caller_frame:
            module = caller_frame.f_globals.get("__name__", "unknown")
            function = caller_frame.f_code.co_name
            filename = caller_frame.f_code.co_filename.split("/")[-1].split("\\")[-1]
            
            # Determine section from module path
            section = "unknown"
            if "document" in module.lower() or "extraction" in module.lower():
                section = "document_processing"
            elif "chat" in module.lower():
                section = "chat"
            elif "validation" in module.lower():
                section = "validation"
            elif "chaser" in module.lower() or "email" in module.lower():
                section = "email"
            elif "api" in module.lower():
                section = "api"
            
            # Format source as "module:function" or "file:function"
            source = f"{module}:{function}"
            return section, source
    finally:
        del frame
    
    return "unknown", "unknown:unknown"


class LLMInstrumentation:
    """Wrapper to instrument LLM calls with metrics and logging."""
    
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.logger = logging.getLogger(f"app.ai.{provider}")
        self._last_response = None
        self._last_input_tokens = 0
        self._last_output_tokens = 0
        self._log_response = True
    
    @asynccontextmanager
    async def track_call(
        self,
        operation: str,
        request_data: dict[str, Any] | None = None,
        log_response: bool = True,
        section: str | None = None,
        source: str | None = None,
    ):
        """Context manager to track an LLM call.
        
        Args:
            operation: Operation name (extract_document_data, validate_document, chat, etc.)
            request_data: Request data to log
            log_response: Whether to log the full response
            section: Section tag (e.g., "document_processing", "chat"). If None, auto-detected.
            source: Source location (e.g., "app.services.documents:extract"). If None, auto-detected.
        """
        # Auto-detect section and source if not provided
        if section is None or source is None:
            auto_section, auto_source = get_source_location()
            section = section or auto_section
            source = source or auto_source
        
        start_time = time.time()
        status = "success"
        error_type = None
        input_tokens = 0
        output_tokens = 0
        response_data = None
        
        self._log_response = log_response
        
        with tracer.start_as_current_span(
            f"llm.{self.provider}.{operation}",
            attributes={
                "llm.provider": self.provider,
                "llm.model": self.model,
                "llm.operation": operation,
            }
        ):
            try:
                # Log request (only if logging enabled for this section and level)
                if should_log(section, logging.INFO):
                    self.logger.info(
                        "LLM request started",
                        extra={
                            "extra_fields": {
                                "provider": self.provider,
                                "model": self.model,
                                "operation": operation,
                                "section": section,
                                "source": source,
                                "request": request_data,
                            }
                        }
                    )
                
                yield self
                
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                
                # Always record error metric (metrics always run)
                llm_errors_total.labels(
                    provider=self.provider,
                    model=self.model,
                    operation=operation,
                    error_type=error_type,
                    section=section,
                    source=source,
                ).inc()
                
                # Log error (only if logging enabled for this section and level)
                if should_log(section, logging.ERROR):
                    self.logger.error(
                        "LLM request failed",
                        extra={
                            "extra_fields": {
                                "provider": self.provider,
                                "model": self.model,
                                "operation": operation,
                                "section": section,
                                "source": source,
                                "error": str(e),
                                "error_type": error_type,
                            }
                        },
                        exc_info=True,
                    )
                raise
            
            finally:
                duration = time.time() - start_time
                
                # Get token usage from stored response if available
                if self._last_response:
                    input_tokens, output_tokens = extract_token_usage(
                        self._last_response, self.provider
                    )
                    # Also try to extract response data for logging
                    if hasattr(self._last_response, "choices"):
                        # OpenAI format
                        if self._last_response.choices:
                            response_data = self._last_response.choices[0].message.content if hasattr(self._last_response.choices[0].message, "content") else None
                    elif hasattr(self._last_response, "content"):
                        # Anthropic format
                        if self._last_response.content:
                            response_data = self._last_response.content[0].text if hasattr(self._last_response.content[0], "text") else str(self._last_response.content[0])
                
                # Always record metrics (metrics always run)
                llm_requests_total.labels(
                    provider=self.provider,
                    model=self.model,
                    operation=operation,
                    status=status,
                    section=section,
                    source=source,
                ).inc()
                
                llm_request_duration.labels(
                    provider=self.provider,
                    model=self.model,
                    operation=operation,
                    section=section,
                    source=source,
                ).observe(duration)
                
                # Record tokens and cost if available
                if input_tokens > 0 or output_tokens > 0:
                    if input_tokens > 0:
                        llm_tokens_total.labels(
                            provider=self.provider,
                            model=self.model,
                            operation=operation,
                            token_type="input",
                            section=section,
                            source=source,
                        ).inc(input_tokens)
                    
                    if output_tokens > 0:
                        llm_tokens_total.labels(
                            provider=self.provider,
                            model=self.model,
                            operation=operation,
                            token_type="output",
                            section=section,
                            source=source,
                        ).inc(output_tokens)
                    
                    cost = calculate_llm_cost(
                        self.provider,
                        self.model,
                        input_tokens,
                        output_tokens,
                    )
                    
                    if cost > 0:
                        llm_cost_total.labels(
                            provider=self.provider,
                            model=self.model,
                            operation=operation,
                            section=section,
                            source=source,
                        ).inc(cost)
                
                # Log response (only if logging enabled for this section and level)
                if should_log(section, logging.INFO) and self._log_response and response_data:
                    # Truncate very long responses for logging
                    response_str = str(response_data)
                    if len(response_str) > 10000:
                        response_str = response_str[:10000] + "... [truncated]"
                    
                    self.logger.info(
                        "LLM response received",
                        extra={
                            "extra_fields": {
                                "provider": self.provider,
                                "model": self.model,
                                "operation": operation,
                                "section": section,
                                "source": source,
                                "duration_seconds": duration,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "cost_usd": calculate_llm_cost(
                                    self.provider,
                                    self.model,
                                    input_tokens,
                                    output_tokens,
                                ) if (input_tokens > 0 or output_tokens > 0) else None,
                                "response": response_str if self._log_response else None,
                            }
                        }
                    )
                
                # Reset for next call
                self._last_response = None
                self._last_input_tokens = 0
                self._last_output_tokens = 0
    
    def record_response(
        self,
        response: Any,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        """Record response data for an LLM call.
        
        This should be called after getting the response to update tokens and log.
        
        Args:
            response: The LLM API response object
            input_tokens: Input tokens (if not extractable from response)
            output_tokens: Output tokens (if not extractable from response)
        """
        # Store for logging in finally block
        self._last_response = response
        
        # If tokens not provided, try to extract from response
        if input_tokens == 0 and output_tokens == 0:
            input_tokens, output_tokens = extract_token_usage(response, self.provider)
        
        self._last_input_tokens = input_tokens
        self._last_output_tokens = output_tokens
