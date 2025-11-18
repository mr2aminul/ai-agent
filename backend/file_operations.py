import os
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any


class FileOperations:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

    def _validate_path(self, file_path: str) -> Path:
        """Validate and resolve file path to prevent directory traversal attacks"""
        requested_path = (self.project_path / file_path).resolve()

        if not str(requested_path).startswith(str(self.project_path)):
            raise ValueError(f"Path traversal detected: {file_path}")

        return requested_path

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file contents"""
        try:
            path = self._validate_path(file_path)

            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            if not path.is_file():
                return {"success": False, "error": f"Path is not a file: {file_path}"}

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "path": str(path),
                "size": len(content)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, file_path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        """Write file contents"""
        try:
            path = self._validate_path(file_path)

            if path.exists() and not overwrite:
                return {"success": False, "error": f"File already exists: {file_path}"}

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "path": str(path),
                "size": len(content),
                "message": f"File {'created' if not path.exists() else 'updated'}: {file_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def append_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Append content to file"""
        try:
            path = self._validate_path(file_path)

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "path": str(path),
                "message": f"Content appended to: {file_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete file"""
        try:
            path = self._validate_path(file_path)

            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            if not path.is_file():
                return {"success": False, "error": f"Path is not a file: {file_path}"}

            path.unlink()

            return {
                "success": True,
                "path": str(path),
                "message": f"File deleted: {file_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """Create directory"""
        try:
            path = self._validate_path(dir_path)
            path.mkdir(parents=True, exist_ok=True)

            return {
                "success": True,
                "path": str(path),
                "message": f"Directory created: {dir_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_directory(self, dir_path: str) -> Dict[str, Any]:
        """Delete directory and contents"""
        try:
            path = self._validate_path(dir_path)

            if not path.exists():
                return {"success": False, "error": f"Directory not found: {dir_path}"}

            if not path.is_dir():
                return {"success": False, "error": f"Path is not a directory: {dir_path}"}

            shutil.rmtree(path)

            return {
                "success": True,
                "path": str(path),
                "message": f"Directory deleted: {dir_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, dir_path: str = ".") -> Dict[str, Any]:
        """List directory contents"""
        try:
            path = self._validate_path(dir_path)

            if not path.exists():
                return {"success": False, "error": f"Directory not found: {dir_path}"}

            if not path.is_dir():
                return {"success": False, "error": f"Path is not a directory: {dir_path}"}

            items = []
            for item in sorted(path.iterdir()):
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "path": str(item.relative_to(self.project_path))
                })

            return {
                "success": True,
                "path": str(path),
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename_file(self, old_path: str, new_path: str) -> Dict[str, Any]:
        """Rename file"""
        try:
            old = self._validate_path(old_path)
            new = self._validate_path(new_path)

            if not old.exists():
                return {"success": False, "error": f"File not found: {old_path}"}

            if new.exists():
                return {"success": False, "error": f"Target already exists: {new_path}"}

            old.rename(new)

            return {
                "success": True,
                "old_path": str(old),
                "new_path": str(new),
                "message": f"File renamed from {old_path} to {new_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy_file(self, source_path: str, dest_path: str) -> Dict[str, Any]:
        """Copy file"""
        try:
            source = self._validate_path(source_path)
            dest = self._validate_path(dest_path)

            if not source.exists():
                return {"success": False, "error": f"Source file not found: {source_path}"}

            if not source.is_file():
                return {"success": False, "error": f"Source is not a file: {source_path}"}

            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)

            return {
                "success": True,
                "source": str(source),
                "destination": str(dest),
                "message": f"File copied from {source_path} to {dest_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def file_exists(self, file_path: str) -> Dict[str, Any]:
        """Check if file exists"""
        try:
            path = self._validate_path(file_path)
            return {
                "success": True,
                "exists": path.exists(),
                "is_file": path.is_file() if path.exists() else False,
                "is_dir": path.is_dir() if path.exists() else False
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        try:
            path = self._validate_path(file_path)

            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            stat = path.stat()

            return {
                "success": True,
                "path": str(path),
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_dir": path.is_dir(),
                "is_file": path.is_file()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, pattern: str, dir_path: str = ".") -> Dict[str, Any]:
        """Search files by pattern"""
        try:
            import fnmatch

            path = self._validate_path(dir_path)

            if not path.is_dir():
                return {"success": False, "error": f"Path is not a directory: {dir_path}"}

            results = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        full_path = Path(root) / file
                        results.append(str(full_path.relative_to(self.project_path)))

            return {
                "success": True,
                "pattern": pattern,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
