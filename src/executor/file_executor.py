"""
File Operations Executor for CodeVoice
BUILD 10: File system operations

Handles:
- Opening files
- Creating files
- Reading file contents
- Writing to files
- Deleting files
- Directory operations
- Path resolution
"""

import asyncio
import time
from pathlib import Path
from typing import Optional

from .executor_base import BaseExecutor, TaskContext, TaskResult, TaskStatus


class FileExecutor(BaseExecutor):
    """
    Executor for file system operations.
    
    Performs file operations like open, create, read, write, delete.
    """
    
    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize file executor.
        
        Args:
            workspace_root: Root directory for relative path resolution
        """
        super().__init__()
        self.workspace_root = workspace_root or Path.cwd()
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        Execute a file operation.
        
        Args:
            context: Task context with file operation command
            
        Returns:
            TaskResult with operation status
        """
        start_time = time.time()
        task_id = context.task_id
        
        try:
            # Determine operation from intent
            intent = context.intent.lower()
            
            if intent == "open_file":
                result = await self._open_file(context)
            elif intent == "create_file":
                result = await self._create_file(context)
            elif intent == "read_file":
                result = await self._read_file(context)
            elif intent == "write_file":
                result = await self._write_file(context)
            elif intent == "delete_file":
                result = await self._delete_file(context)
            elif intent == "check_file":
                result = await self._check_file_exists(context)
            elif intent == "create_directory":
                result = await self._create_directory(context)
            elif intent == "list_directory":
                result = await self._list_directory(context)
            else:
                latency_ms = (time.time() - start_time) * 1000
                return self._create_error_result(
                    task_id=task_id,
                    error=f"Unknown file operation: {intent}",
                    latency_ms=latency_ms
                )
            
            return result
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_result(
                task_id=task_id,
                error=f"File operation error: {str(e)}",
                latency_ms=latency_ms
            )
    
    def _resolve_path(self, file_path: str) -> Path:
        """
        Resolve file path (relative or absolute).
        
        Args:
            file_path: Path string
            
        Returns:
            Resolved Path object
        """
        path = Path(file_path)
        
        if not path.is_absolute():
            path = self.workspace_root / path
        
        return path.resolve()
    
    async def _open_file(self, context: TaskContext) -> TaskResult:
        """Open a file in VS Code or default system application."""
        start_time = time.time()
        
        file_path = context.params.get("file", "")
        if not file_path:
            # Try to extract from command
            parts = context.command.split()
            if len(parts) > 1:
                file_path = parts[1]
        
        path = self._resolve_path(file_path)
        
        if not path.exists():
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_result(
                task_id=context.task_id,
                error=f"File not found: {path}",
                latency_ms=latency_ms
            )
        
        try:
            # Try VS Code first (preferred for code files)
            process = await asyncio.create_subprocess_exec(
                "code",
                str(path.absolute()),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Don't wait for VS Code to exit (it launches async)
            await asyncio.sleep(0.2)  # Brief wait to check if command failed
            
            latency_ms = (time.time() - start_time) * 1000
            return self._create_success_result(
                task_id=context.task_id,
                output=f"Opened file in VS Code: {path}",
                latency_ms=latency_ms,
                metadata={"file_path": str(path), "method": "vscode"}
            )
            
        except FileNotFoundError:
            # VS Code not available, use Windows default application
            try:
                import os
                os.startfile(str(path.absolute()))
                
                latency_ms = (time.time() - start_time) * 1000
                return self._create_success_result(
                    task_id=context.task_id,
                    output=f"Opened file with default app: {path}",
                    latency_ms=latency_ms,
                    metadata={"file_path": str(path), "method": "default_app"}
                )
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                return self._create_error_result(
                    task_id=context.task_id,
                    error=f"Failed to open file: {str(e)}",
                    latency_ms=latency_ms
                )
    
    async def _create_file(self, context: TaskContext) -> TaskResult:
        """Create a new file with optional content."""
        start_time = time.time()
        
        file_path = context.params.get("file", "")
        content = context.params.get("content", "")
        
        if not file_path:
            parts = context.command.split()
            if len(parts) > 1:
                file_path = parts[1]
        
        path = self._resolve_path(file_path)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        path.write_text(content, encoding='utf-8')
        
        latency_ms = (time.time() - start_time) * 1000
        return self._create_success_result(
            task_id=context.task_id,
            output=f"Created file: {path}",
            latency_ms=latency_ms,
            metadata={"file_path": str(path), "size_bytes": len(content)}
        )
    
    async def _read_file(self, context: TaskContext) -> TaskResult:
        """Read file contents."""
        start_time = time.time()
        
        file_path = context.params.get("file", "")
        if not file_path:
            parts = context.command.split()
            if len(parts) > 1:
                file_path = parts[1]
        
        path = self._resolve_path(file_path)
        
        if not path.exists():
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_result(
                task_id=context.task_id,
                error=f"File not found: {path}",
                latency_ms=latency_ms
            )
        
        # Read file content
        content = path.read_text(encoding='utf-8')
        
        latency_ms = (time.time() - start_time) * 1000
        return self._create_success_result(
            task_id=context.task_id,
            output=content,
            latency_ms=latency_ms,
            metadata={"file_path": str(path), "size_bytes": len(content)}
        )
    
    async def _write_file(self, context: TaskContext) -> TaskResult:
        """Write content to existing file."""
        start_time = time.time()
        
        file_path = context.params.get("file", "")
        content = context.params.get("content", "")
        
        if not file_path:
            parts = context.command.split()
            if len(parts) > 1:
                file_path = parts[1]
        
        path = self._resolve_path(file_path)
        
        # Write content
        path.write_text(content, encoding='utf-8')
        
        latency_ms = (time.time() - start_time) * 1000
        return self._create_success_result(
            task_id=context.task_id,
            output=f"Wrote {len(content)} bytes to {path}",
            latency_ms=latency_ms,
            metadata={"file_path": str(path), "size_bytes": len(content)}
        )
    
    async def _delete_file(self, context: TaskContext) -> TaskResult:
        """Delete a file."""
        start_time = time.time()
        
        file_path = context.params.get("file", "")
        if not file_path:
            parts = context.command.split()
            if len(parts) > 1:
                file_path = parts[1]
        
        path = self._resolve_path(file_path)
        
        if not path.exists():
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_result(
                task_id=context.task_id,
                error=f"File not found: {path}",
                latency_ms=latency_ms
            )
        
        # Delete file
        path.unlink()
        
        latency_ms = (time.time() - start_time) * 1000
        return self._create_success_result(
            task_id=context.task_id,
            output=f"Deleted file: {path}",
            latency_ms=latency_ms,
            metadata={"file_path": str(path)}
        )
    
    async def _check_file_exists(self, context: TaskContext) -> TaskResult:
        """Check if file exists."""
        start_time = time.time()
        
        file_path = context.params.get("file", "")
        if not file_path:
            parts = context.command.split()
            if len(parts) > 1:
                file_path = parts[1]
        
        path = self._resolve_path(file_path)
        
        exists = path.exists()
        
        latency_ms = (time.time() - start_time) * 1000
        return self._create_success_result(
            task_id=context.task_id,
            output=f"File {'exists' if exists else 'does not exist'}: {path}",
            latency_ms=latency_ms,
            metadata={"file_path": str(path), "exists": exists}
        )
    
    async def _create_directory(self, context: TaskContext) -> TaskResult:
        """Create a directory."""
        start_time = time.time()
        
        dir_path = context.params.get("directory", "")
        if not dir_path:
            parts = context.command.split()
            if len(parts) > 1:
                dir_path = parts[1]
        
        path = self._resolve_path(dir_path)
        
        # Create directory
        path.mkdir(parents=True, exist_ok=True)
        
        latency_ms = (time.time() - start_time) * 1000
        return self._create_success_result(
            task_id=context.task_id,
            output=f"Created directory: {path}",
            latency_ms=latency_ms,
            metadata={"directory_path": str(path)}
        )
    
    async def _list_directory(self, context: TaskContext) -> TaskResult:
        """List directory contents."""
        start_time = time.time()
        
        dir_path = context.params.get("directory", "")
        if not dir_path:
            parts = context.command.split()
            if len(parts) > 1:
                dir_path = parts[1]
            else:
                dir_path = "."
        
        path = self._resolve_path(dir_path)
        
        if not path.exists():
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_result(
                task_id=context.task_id,
                error=f"Directory not found: {path}",
                latency_ms=latency_ms
            )
        
        if not path.is_dir():
            latency_ms = (time.time() - start_time) * 1000
            return self._create_error_result(
                task_id=context.task_id,
                error=f"Not a directory: {path}",
                latency_ms=latency_ms
            )
        
        # List contents
        items = [item.name for item in path.iterdir()]
        items.sort()
        
        output = "\n".join(items)
        
        latency_ms = (time.time() - start_time) * 1000
        return self._create_success_result(
            task_id=context.task_id,
            output=output,
            latency_ms=latency_ms,
            metadata={"directory_path": str(path), "item_count": len(items)}
        )
