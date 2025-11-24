"""
Tracing service using Langfuse for monitoring and observability.
Tracks all operations, latencies, and errors.
"""

from langfuse import Langfuse
from functools import wraps
import time
import logging
from typing import Any, Callable

from src.config import settings

logger = logging.getLogger(__name__)

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)


class TracingService:
    """Service for tracing operations with Langfuse."""

    def __init__(self):
        self.client = langfuse

    def trace_function(self, name: str, metadata: dict = None):
        """
        Decorator to trace function execution.

        Args:
            name: Name of the operation to trace
            metadata: Additional metadata to log

        Usage:
            @tracing_service.trace_function("password_check")
            async def check_password(text: str):
                ...
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                trace = self.client.trace(name=name, metadata=metadata or {})
                start_time = time.time()

                try:
                    result = await func(*args, **kwargs)
                    latency = time.time() - start_time

                    trace.update(
                        output={"result": str(result)[:500]},  # Truncate long outputs
                        metadata={
                            **(metadata or {}),
                            "latency_ms": round(latency * 1000, 2),
                            "status": "success",
                        },
                    )

                    logger.debug(f"Traced {name}: {latency:.3f}s")
                    return result

                except Exception as e:
                    latency = time.time() - start_time

                    trace.update(
                        metadata={
                            **(metadata or {}),
                            "latency_ms": round(latency * 1000, 2),
                            "status": "error",
                            "error": str(e),
                        },
                    )

                    logger.error(f"Traced {name} failed: {e}")
                    raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                trace = self.client.trace(name=name, metadata=metadata or {})
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    latency = time.time() - start_time

                    trace.update(
                        output={"result": str(result)[:500]},
                        metadata={
                            **(metadata or {}),
                            "latency_ms": round(latency * 1000, 2),
                            "status": "success",
                        },
                    )

                    logger.debug(f"Traced {name}: {latency:.3f}s")
                    return result

                except Exception as e:
                    latency = time.time() - start_time

                    trace.update(
                        metadata={
                            **(metadata or {}),
                            "latency_ms": round(latency * 1000, 2),
                            "status": "error",
                            "error": str(e),
                        },
                    )

                    logger.error(f"Traced {name} failed: {e}")
                    raise

            # Return appropriate wrapper based on function type
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def log_event(
        self,
        name: str,
        level: str = "INFO",
        metadata: dict = None,
        trace_id: str = None,
    ):
        """
        Log a custom event to Langfuse.

        Args:
            name: Event name
            level: Log level (INFO, WARNING, ERROR)
            metadata: Additional metadata
            trace_id: Optional trace ID to associate with
        """
        try:
            self.client.score(
                name=name,
                value=1 if level == "INFO" else 0,
                data_type="NUMERIC",
                comment=f"{level}: {name}",
                trace_id=trace_id,
            )

            if metadata:
                logger.debug(f"Logged event {name}: {metadata}")

        except Exception as e:
            logger.error(f"Failed to log event {name}: {e}")


# Global tracing service instance
tracing_service = TracingService()


if __name__ == "__main__":
    # Test script for tracing service
    import asyncio

    @tracing_service.trace_function("test_operation")
    async def test_operation():
        await asyncio.sleep(0.1)
        return "success"

    async def test_tracing():
        result = await test_operation()
        print(f"Result: {result}")
        print("Check Langfuse dashboard for trace!")

    asyncio.run(test_tracing())
