"""
Base Executor Interface for CodeVoice Task Execution
BUILD 8: Core executor abstraction

Provides:
- TaskContext: Isolated task execution context
- TaskResult: Structured execution results
- TaskStatus: Task state tracking
- BaseExecutor: Abstract base class for all executors
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class TaskStatus(Enum):
    """Task execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class TaskContext:
    """
    Isolated execution context for a task.
    
    Contains all information needed to execute a command,
    with proper isolation from other tasks.
    """
    intent: str
    command: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    params: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300  # 5 minutes default
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.intent:
            raise ValueError("Intent is required")
        if not self.command:
            raise ValueError("Command is required")


@dataclass
class TaskResult:
    """
    Result of task execution.
    
    Contains status, output, timing, and error information.
    """
    task_id: str
    status: TaskStatus
    output: str = ""
    error: str = ""
    latency_ms: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.SUCCESS
    
    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED]


class BaseExecutor(ABC):
    """
    Abstract base class for all executors.
    
    All concrete executors (PowerShell, VS Code, Browser, etc.)
    must implement the execute() method.
    """
    
    def __init__(self):
        """Initialize executor."""
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        Execute a task in the given context.
        
        Args:
            context: Task execution context
            
        Returns:
            TaskResult with execution status and output
        """
        pass
    
    async def _execute_with_timeout(
        self,
        context: TaskContext,
        coro
    ) -> TaskResult:
        """
        Execute a coroutine with timeout protection.
        
        Args:
            context: Task context
            coro: Coroutine to execute
            
        Returns:
            TaskResult with timeout handling
        """
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                coro,
                timeout=context.timeout_seconds
            )
            return result
            
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return TaskResult(
                task_id=context.task_id,
                status=TaskStatus.TIMEOUT,
                error=f"Task timed out after {context.timeout_seconds}s",
                latency_ms=latency_ms
            )
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TaskResult(
                task_id=context.task_id,
                status=TaskStatus.FAILED,
                error=f"Execution error: {str(e)}",
                latency_ms=latency_ms
            )
    
    def _create_success_result(
        self,
        task_id: str,
        output: str,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """
        Create a success result.
        
        Args:
            task_id: Task identifier
            output: Command output
            latency_ms: Execution time in milliseconds
            metadata: Optional additional metadata
            
        Returns:
            TaskResult with SUCCESS status
        """
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            output=output,
            latency_ms=latency_ms,
            completed_at=datetime.now(),
            metadata=metadata or {}
        )
    
    def _create_error_result(
        self,
        task_id: str,
        error: str,
        latency_ms: float,
        output: str = ""
    ) -> TaskResult:
        """
        Create a failure result.
        
        Args:
            task_id: Task identifier
            error: Error message
            latency_ms: Execution time in milliseconds
            output: Partial output if any
            
        Returns:
            TaskResult with FAILED status
        """
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=error,
            output=output,
            latency_ms=latency_ms,
            completed_at=datetime.now()
        )


class MockExecutor(BaseExecutor):
    """
    Mock executor for testing purposes.
    
    Simulates task execution without actually running commands.
    """
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """Execute mock task."""
        start_time = time.time()
        
        # Simulate work
        await asyncio.sleep(0.01)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return self._create_success_result(
            task_id=context.task_id,
            output=f"Mock execution of {context.intent}: {context.command}",
            latency_ms=latency_ms,
            metadata={"mock": True}
        )
