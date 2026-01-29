"""
Tests for Week 3: Task Execution System
BUILD 8: Base Executor and Task Scheduler Tests

Testing:
1. Base executor interface
2. Task context creation and isolation
3. Task scheduler queue management
4. Async task execution
5. Error handling and logging
6. Concurrent task execution
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from executor.executor_base import BaseExecutor, TaskContext, TaskResult, TaskStatus
from executor.task_scheduler import TaskScheduler


# ==================== FIXTURES ====================

@pytest.fixture
async def base_executor():
    """Mock executor for testing base functionality."""
    class MockExecutor(BaseExecutor):
        async def execute(self, context: TaskContext) -> TaskResult:
            """Mock execution that simulates work."""
            await asyncio.sleep(0.01)  # Simulate work
            return TaskResult(
                task_id=context.task_id,
                status=TaskStatus.SUCCESS,
                output=f"Executed {context.intent}",
                latency_ms=10
            )
    
    return MockExecutor()


@pytest.fixture
async def task_scheduler():
    """Task scheduler instance for testing."""
    scheduler = TaskScheduler(max_concurrent_tasks=5)
    yield scheduler
    await scheduler.shutdown()


# ==================== BASE EXECUTOR TESTS ====================

@pytest.mark.asyncio
async def test_task_context_creation():
    """Test TaskContext creation with required fields."""
    context = TaskContext(
        task_id="test-001",
        intent="git_commit",
        command="git commit -m 'test'",
        params={"message": "test"}
    )
    
    assert context.task_id == "test-001"
    assert context.intent == "git_commit"
    assert context.command == "git commit -m 'test'"
    assert context.params["message"] == "test"
    assert context.created_at is not None


@pytest.mark.asyncio
async def test_task_context_defaults():
    """Test TaskContext with default values."""
    context = TaskContext(
        intent="git_status",
        command="git status"
    )
    
    assert context.task_id is not None  # Auto-generated
    assert len(context.task_id) > 0
    assert context.params == {}
    assert context.timeout_seconds == 300  # Default 5 minutes


@pytest.mark.asyncio
async def test_base_executor_interface(base_executor):
    """Test that base executor implements required interface."""
    assert hasattr(base_executor, 'execute')
    assert asyncio.iscoroutinefunction(base_executor.execute)
    
    # Test execution
    context = TaskContext(
        intent="test_intent",
        command="echo test"
    )
    result = await base_executor.execute(context)
    
    assert isinstance(result, TaskResult)
    assert result.status == TaskStatus.SUCCESS


@pytest.mark.asyncio
async def test_task_result_structure(base_executor):
    """Test TaskResult contains all required fields."""
    context = TaskContext(
        intent="test_intent",
        command="echo test"
    )
    result = await base_executor.execute(context)
    
    assert hasattr(result, 'task_id')
    assert hasattr(result, 'status')
    assert hasattr(result, 'output')
    assert hasattr(result, 'latency_ms')
    assert hasattr(result, 'error')
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_executor_error_handling(base_executor):
    """Test executor handles errors gracefully."""
    class FailingExecutor(BaseExecutor):
        async def execute(self, context: TaskContext) -> TaskResult:
            import time
            start_time = time.time()
            try:
                raise ValueError("Simulated error")
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                return self._create_error_result(
                    task_id=context.task_id,
                    error=str(e),
                    latency_ms=latency_ms
                )
    
    executor = FailingExecutor()
    context = TaskContext(
        intent="fail_test",
        command="fail"
    )
    
    result = await executor.execute(context)
    
    assert result.status == TaskStatus.FAILED
    assert "error" in result.error.lower() or "simulated" in result.error.lower()


# ==================== TASK SCHEDULER TESTS ====================

@pytest.mark.asyncio
async def test_scheduler_initialization(task_scheduler):
    """Test task scheduler initializes correctly."""
    assert task_scheduler is not None
    assert task_scheduler.max_concurrent_tasks == 5
    assert task_scheduler.get_active_tasks_count() == 0


@pytest.mark.asyncio
async def test_scheduler_submit_task(task_scheduler, base_executor):
    """Test submitting a task to scheduler."""
    context = TaskContext(
        intent="test_intent",
        command="echo test"
    )
    
    task_id = await task_scheduler.submit_task(context, base_executor)
    
    assert task_id is not None
    assert len(task_id) > 0
    
    # Wait for task to complete
    await asyncio.sleep(0.05)
    result = task_scheduler.get_task_result(task_id)
    
    assert result is not None
    assert result.status == TaskStatus.SUCCESS


@pytest.mark.asyncio
async def test_scheduler_task_queue(task_scheduler, base_executor):
    """Test scheduler queues tasks properly."""
    contexts = [
        TaskContext(intent=f"task_{i}", command=f"echo {i}")
        for i in range(3)
    ]
    
    task_ids = []
    for context in contexts:
        task_id = await task_scheduler.submit_task(context, base_executor)
        task_ids.append(task_id)
    
    assert len(task_ids) == 3
    assert len(set(task_ids)) == 3  # All unique
    
    # Wait for all tasks to complete
    await asyncio.sleep(0.1)
    
    for task_id in task_ids:
        result = task_scheduler.get_task_result(task_id)
        assert result is not None
        assert result.status == TaskStatus.SUCCESS


@pytest.mark.asyncio
async def test_scheduler_concurrent_execution(task_scheduler):
    """Test scheduler executes tasks concurrently."""
    class SlowExecutor(BaseExecutor):
        async def execute(self, context: TaskContext) -> TaskResult:
            await asyncio.sleep(0.1)  # Simulate slow task
            return TaskResult(
                task_id=context.task_id,
                status=TaskStatus.SUCCESS,
                output="Done",
                latency_ms=100
            )
    
    executor = SlowExecutor()
    
    # Submit 3 tasks that take 100ms each
    import time
    start_time = time.time()
    
    task_ids = []
    for i in range(3):
        context = TaskContext(intent=f"slow_task_{i}", command=f"sleep {i}")
        task_id = await task_scheduler.submit_task(context, executor)
        task_ids.append(task_id)
    
    # Wait for all to complete
    await asyncio.sleep(0.3)
    
    elapsed = time.time() - start_time
    
    # Should complete in ~150ms (concurrent) not 300ms (sequential)
    # Allow some overhead for task scheduling
    assert elapsed < 0.35, f"Tasks should execute concurrently, took {elapsed}s"
    
    # All should be successful
    for task_id in task_ids:
        result = task_scheduler.get_task_result(task_id)
        assert result.status == TaskStatus.SUCCESS


@pytest.mark.asyncio
async def test_scheduler_max_concurrent_limit():
    """Test scheduler respects max concurrent task limit."""
    scheduler = TaskScheduler(max_concurrent_tasks=2)
    
    class CountingExecutor(BaseExecutor):
        active_count = 0
        max_seen = 0
        
        async def execute(self, context: TaskContext) -> TaskResult:
            CountingExecutor.active_count += 1
            CountingExecutor.max_seen = max(
                CountingExecutor.max_seen,
                CountingExecutor.active_count
            )
            
            await asyncio.sleep(0.05)
            
            CountingExecutor.active_count -= 1
            
            return TaskResult(
                task_id=context.task_id,
                status=TaskStatus.SUCCESS,
                output="Done",
                latency_ms=50
            )
    
    executor = CountingExecutor()
    
    # Submit 5 tasks with limit of 2 concurrent
    task_ids = []
    for i in range(5):
        context = TaskContext(intent=f"task_{i}", command=f"test {i}")
        task_id = await scheduler.submit_task(context, executor)
        task_ids.append(task_id)
    
    # Wait for all to complete
    await asyncio.sleep(0.2)
    
    # Should never have more than 2 running at once
    assert CountingExecutor.max_seen <= 2, f"Max concurrent was {CountingExecutor.max_seen}, expected <= 2"
    
    await scheduler.shutdown()


@pytest.mark.asyncio
async def test_scheduler_task_status_tracking(task_scheduler, base_executor):
    """Test scheduler tracks task status correctly."""
    context = TaskContext(
        intent="test_status",
        command="echo status"
    )
    
    task_id = await task_scheduler.submit_task(context, base_executor)
    
    # Initially should be queued or running
    status = task_scheduler.get_task_status(task_id)
    assert status in [TaskStatus.QUEUED, TaskStatus.RUNNING]
    
    # Wait for completion
    await asyncio.sleep(0.05)
    
    status = task_scheduler.get_task_status(task_id)
    assert status == TaskStatus.SUCCESS


@pytest.mark.asyncio
async def test_scheduler_get_all_tasks(task_scheduler, base_executor):
    """Test getting list of all tasks."""
    # Submit multiple tasks
    task_ids = []
    for i in range(3):
        context = TaskContext(intent=f"task_{i}", command=f"test {i}")
        task_id = await task_scheduler.submit_task(context, base_executor)
        task_ids.append(task_id)
    
    await asyncio.sleep(0.1)
    
    # Get all tasks
    all_tasks = task_scheduler.get_all_tasks()
    
    assert len(all_tasks) >= 3
    for task_id in task_ids:
        assert task_id in [t.context.task_id for t in all_tasks]


@pytest.mark.asyncio
async def test_scheduler_latency(task_scheduler, base_executor):
    """Test task scheduler submission latency is minimal."""
    import time
    
    context = TaskContext(
        intent="latency_test",
        command="echo fast"
    )
    
    start = time.time()
    task_id = await task_scheduler.submit_task(context, base_executor)
    submit_latency = (time.time() - start) * 1000
    
    # Submission should be nearly instant (<5ms)
    assert submit_latency < 5, f"Submission took {submit_latency}ms, expected <5ms"
    
    assert task_id is not None


# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_full_task_lifecycle(task_scheduler, base_executor):
    """Test complete task lifecycle from submission to completion."""
    context = TaskContext(
        intent="lifecycle_test",
        command="echo lifecycle",
        params={"test": "value"}
    )
    
    # 1. Submit
    task_id = await task_scheduler.submit_task(context, base_executor)
    assert task_id is not None
    
    # 2. Check status (should be queued or running)
    status = task_scheduler.get_task_status(task_id)
    assert status in [TaskStatus.QUEUED, TaskStatus.RUNNING]
    
    # 3. Wait for completion
    await asyncio.sleep(0.05)
    
    # 4. Check final status
    status = task_scheduler.get_task_status(task_id)
    assert status == TaskStatus.SUCCESS
    
    # 5. Get result
    result = task_scheduler.get_task_result(task_id)
    assert result is not None
    assert result.task_id == task_id
    assert result.status == TaskStatus.SUCCESS
    assert result.output is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
