"""
Task Scheduler for CodeVoice
BUILD 8: Async task queue and execution management

Features:
- Async task queue with concurrent execution
- Task status tracking
- Result storage and retrieval
- Configurable concurrency limits
- Non-blocking task submission
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .executor_base import BaseExecutor, TaskContext, TaskResult, TaskStatus


@dataclass
class ScheduledTask:
    """Task in the scheduler queue."""
    context: TaskContext
    executor: BaseExecutor
    result: Optional[TaskResult] = None
    submitted_at: datetime = None
    started_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.submitted_at is None:
            self.submitted_at = datetime.now()


class TaskScheduler:
    """
    Async task scheduler with concurrent execution.
    
    Manages a queue of tasks, executes them concurrently up to
    a configurable limit, and tracks results.
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        """
        Initialize task scheduler.
        
        Args:
            max_concurrent_tasks: Maximum number of tasks to run concurrently
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self._tasks: Dict[str, ScheduledTask] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._active_tasks: int = 0
        self._lock = asyncio.Lock()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        # Start background worker
        self._start_worker()
    
    def _start_worker(self):
        """Start background worker task."""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())
    
    async def _worker_loop(self):
        """Background worker that processes task queue."""
        while self._running:
            try:
                # Wait for a task with timeout to allow shutdown
                try:
                    scheduled_task = await asyncio.wait_for(
                        self._task_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Wait if at concurrency limit
                while self._active_tasks >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.01)
                
                # Execute task
                asyncio.create_task(self._execute_task(scheduled_task))
                
            except Exception as e:
                # Log error but keep worker running
                print(f"Worker error: {e}")
    
    async def _execute_task(self, scheduled_task: ScheduledTask):
        """
        Execute a single task.
        
        Args:
            scheduled_task: Task to execute
        """
        task_id = scheduled_task.context.task_id
        
        async with self._lock:
            self._active_tasks += 1
            scheduled_task.started_at = datetime.now()
            
            # Update status to running
            if task_id in self._tasks:
                self._tasks[task_id].result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.RUNNING,
                    started_at=datetime.now()
                )
        
        try:
            start_time = time.time()
            
            # Execute the task
            result = await scheduled_task.executor.execute(scheduled_task.context)
            
            # Store result
            async with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].result = result
            
        except Exception as e:
            # Handle execution error
            latency_ms = (time.time() - start_time) * 1000
            error_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                latency_ms=latency_ms,
                completed_at=datetime.now()
            )
            
            async with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].result = error_result
        
        finally:
            async with self._lock:
                self._active_tasks -= 1
    
    async def submit_task(
        self,
        context: TaskContext,
        executor: BaseExecutor
    ) -> str:
        """
        Submit a task for execution.
        
        Args:
            context: Task execution context
            executor: Executor to run the task
            
        Returns:
            Task ID for tracking
        """
        task_id = context.task_id
        
        # Create scheduled task
        scheduled_task = ScheduledTask(
            context=context,
            executor=executor
        )
        
        # Store task
        async with self._lock:
            self._tasks[task_id] = scheduled_task
        
        # Add to queue (non-blocking)
        await self._task_queue.put(scheduled_task)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get current status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskStatus or None if task not found
        """
        if task_id not in self._tasks:
            return None
        
        scheduled_task = self._tasks[task_id]
        
        # If no result yet, task is queued
        if scheduled_task.result is None:
            return TaskStatus.QUEUED
        
        return scheduled_task.result.status
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """
        Get result of a completed task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskResult or None if task not found or not completed
        """
        if task_id not in self._tasks:
            return None
        
        return self._tasks[task_id].result
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """
        Get all tasks in the scheduler.
        
        Returns:
            List of all scheduled tasks
        """
        return list(self._tasks.values())
    
    def get_active_tasks_count(self) -> int:
        """
        Get count of currently executing tasks.
        
        Returns:
            Number of active tasks
        """
        return self._active_tasks
    
    def get_queued_tasks_count(self) -> int:
        """
        Get count of tasks waiting in queue.
        
        Returns:
            Number of queued tasks
        """
        return self._task_queue.qsize()
    
    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Optional[TaskResult]:
        """
        Wait for a task to complete.
        
        Args:
            task_id: Task identifier
            timeout: Maximum time to wait in seconds
            
        Returns:
            TaskResult when completed, or None on timeout
        """
        start_time = time.time()
        
        while True:
            result = self.get_task_result(task_id)
            
            if result is not None and result.status != TaskStatus.RUNNING:
                return result
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None
            
            # Small delay before checking again
            await asyncio.sleep(0.01)
    
    async def wait_for_all_tasks(self, timeout: Optional[float] = None):
        """
        Wait for all tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        start_time = time.time()
        
        while True:
            # Check if all tasks are complete
            all_complete = True
            
            for scheduled_task in self._tasks.values():
                result = scheduled_task.result
                if result is None or result.status == TaskStatus.RUNNING:
                    all_complete = False
                    break
            
            if all_complete and self._active_tasks == 0:
                break
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    break
            
            await asyncio.sleep(0.01)
    
    async def shutdown(self):
        """Shutdown the scheduler and wait for active tasks."""
        self._running = False
        
        # Wait for worker to stop
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._worker_task.cancel()
        
        # Wait for active tasks to complete
        await self.wait_for_all_tasks(timeout=5.0)
    
    def clear_completed_tasks(self):
        """Remove completed tasks from storage to free memory."""
        completed_ids = [
            task_id for task_id, scheduled_task in self._tasks.items()
            if scheduled_task.result and scheduled_task.result.status not in [
                TaskStatus.QUEUED, TaskStatus.RUNNING
            ]
        ]
        
        for task_id in completed_ids:
            del self._tasks[task_id]
