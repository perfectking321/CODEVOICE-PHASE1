"""
PowerShell Executor for CodeVoice
BUILD 9: CLI command execution on Windows

Executes PowerShell commands with:
- Async execution
- Output/error capture
- Timeout handling
- Working directory control
- Environment variables
- Exit code tracking
"""

import asyncio
import subprocess
import time
from typing import Optional
from pathlib import Path

from .executor_base import BaseExecutor, TaskContext, TaskResult, TaskStatus


class PowerShellExecutor(BaseExecutor):
    """
    Executor for PowerShell commands.
    
    Runs commands in PowerShell and captures output, errors, and exit codes.
    """
    
    def __init__(self):
        """Initialize PowerShell executor."""
        super().__init__()
        self.shell = "powershell.exe"
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        Execute a PowerShell command.
        
        Args:
            context: Task execution context with command and parameters
            
        Returns:
            TaskResult with execution status and output
        """
        start_time = time.time()
        task_id = context.task_id
        
        try:
            # Prepare command
            command = self._prepare_command(context.command)
            
            # Setup working directory
            working_dir = context.working_directory
            if working_dir:
                working_dir = Path(working_dir).resolve()
                if not working_dir.exists():
                    return self._create_error_result(
                        task_id=task_id,
                        error=f"Working directory does not exist: {working_dir}",
                        latency_ms=(time.time() - start_time) * 1000
                    )
            
            # Setup environment
            env = None
            if context.environment:
                import os
                env = os.environ.copy()
                env.update(context.environment)
            
            # Execute with timeout
            try:
                process = await asyncio.create_subprocess_exec(
                    self.shell,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(working_dir) if working_dir else None,
                    env=env
                )
                
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=context.timeout_seconds
                )
                
                # Decode output
                output = stdout.decode('utf-8', errors='replace').strip()
                error = stderr.decode('utf-8', errors='replace').strip()
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Check exit code
                if process.returncode == 0:
                    return self._create_success_result(
                        task_id=task_id,
                        output=output,
                        latency_ms=latency_ms,
                        metadata={
                            "exit_code": process.returncode,
                            "command": command
                        }
                    )
                else:
                    # Non-zero exit code indicates failure
                    return self._create_error_result(
                        task_id=task_id,
                        error=error if error else f"Command failed with exit code {process.returncode}",
                        latency_ms=latency_ms,
                        output=output
                    )
            
            except asyncio.TimeoutError:
                # Kill process on timeout
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                
                latency_ms = (time.time() - start_time) * 1000
                return TaskResult(
                    task_id=task_id,
                    status=TaskStatus.TIMEOUT,
                    error=f"command timeout after {context.timeout_seconds}s",
                    latency_ms=latency_ms
                )
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_result(
                task_id=task_id,
                error=f"Execution error: {str(e)}",
                latency_ms=latency_ms
            )
    
    def _prepare_command(self, command: str) -> str:
        """
        Prepare command for PowerShell execution.
        
        Args:
            command: Raw command string
            
        Returns:
            Prepared command string
        """
        # Remove leading/trailing whitespace
        command = command.strip()
        
        # Handle multiline commands
        if "\n" in command:
            # Join lines with semicolons
            lines = [line.strip() for line in command.split("\n") if line.strip()]
            command = "; ".join(lines)
        
        return command
    
    def _format_output(self, output: str) -> str:
        """
        Format command output for display.
        
        Args:
            output: Raw output string
            
        Returns:
            Formatted output
        """
        # Remove excessive whitespace
        lines = [line.rstrip() for line in output.split("\n")]
        return "\n".join(line for line in lines if line)


class GitExecutor(PowerShellExecutor):
    """
    Specialized executor for git commands.
    
    Adds git-specific validation and formatting.
    """
    
    def __init__(self):
        """Initialize git executor."""
        super().__init__()
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        Execute a git command with validation.
        
        Args:
            context: Task context with git command
            
        Returns:
            TaskResult with git-specific formatting
        """
        # Ensure command starts with 'git'
        command = context.command.strip()
        if not command.lower().startswith("git"):
            command = f"git {command}"
            context.command = command
        
        # Execute using parent PowerShell executor
        result = await super().execute(context)
        
        # Add git-specific metadata
        if result.metadata is None:
            result.metadata = {}
        result.metadata["executor_type"] = "git"
        
        return result


class PythonExecutor(PowerShellExecutor):
    """
    Specialized executor for Python commands.
    
    Handles virtual environment activation and Python-specific features.
    """
    
    def __init__(self, venv_path: Optional[str] = None):
        """
        Initialize Python executor.
        
        Args:
            venv_path: Optional path to virtual environment
        """
        super().__init__()
        self.venv_path = venv_path
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        Execute a Python command with venv support.
        
        Args:
            context: Task context with Python command
            
        Returns:
            TaskResult with Python execution
        """
        command = context.command.strip()
        
        # If venv is specified, activate it first
        if self.venv_path:
            venv_activate = f"{self.venv_path}\\Scripts\\Activate.ps1"
            command = f"& '{venv_activate}'; {command}"
        
        # Ensure command uses python
        if not command.lower().startswith("python"):
            command = f"python {command}"
        
        context.command = command
        
        # Execute using parent PowerShell executor
        result = await super().execute(context)
        
        # Add Python-specific metadata
        if result.metadata is None:
            result.metadata = {}
        result.metadata["executor_type"] = "python"
        
        return result
