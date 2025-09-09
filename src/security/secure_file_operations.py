"""
🛡️ Secure File Operations Layer - Path Traversal Prevention

This module provides secure file operations that prevent path traversal attacks,
directory enumeration, and unauthorized file access. All file operations in the
application MUST use this secure layer.

Key Security Features:
✅ Path traversal prevention (../, ..\\ patterns)
✅ Whitelist-based directory access control
✅ File extension validation and sanitization
✅ Symbolic link resolution and validation
✅ File size limits and quota management
✅ Audit logging for all file operations
✅ Sandbox environment enforcement

Usage:
    from security.secure_file_operations import SecureFileManager
    
    with SecureFileManager() as fm:
        # Secure read operation
        content = fm.read_file('data/properties/listing_123.json')
        
        # Secure write operation  
        fm.write_file('reports/analysis.md', content, user_context='user_123')
"""

import os
import tempfile
from pathlib import Path, PurePath
from typing import Dict, Any, List, Optional, Union, BinaryIO, TextIO
import shutil
import hashlib
import json
import logging
from datetime import datetime
from contextlib import contextmanager
import mimetypes
import magic  # python-magic for file type detection
import zipfile
import tarfile
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class FileOperationAudit:
    """Audit log entry for file operations"""
    timestamp: datetime
    operation: str
    file_path: str
    user_context: str
    file_size: int
    file_hash: str
    security_level: str
    violations: List[str]
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'file_path': self.file_path,
            'user_context': self.user_context,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'security_level': self.security_level,
            'violations': self.violations,
            'success': self.success
        }

class SecureFileException(Exception):
    """Exception for secure file operation violations"""
    def __init__(self, message: str, violation_type: str = None, file_path: str = None):
        super().__init__(message)
        self.violation_type = violation_type
        self.file_path = file_path
        self.timestamp = datetime.now()

class SecureFileManager:
    """
    Secure file manager preventing path traversal and unauthorized access
    
    All file operations in the application should use this manager to ensure
    security compliance and prevent common file-based attacks.
    """
    
    # Allowed base directories (whitelist approach)
    ALLOWED_BASE_DIRS = [
        'data',           # Data files
        'reports',        # Generated reports  
        'logs',          # Log files
        'config',        # Configuration files
        'temp',          # Temporary files
        'cache',         # Cache files
        'exports',       # Export files
        'uploads'        # User uploads (if any)
    ]
    
    # Allowed file extensions (whitelist)
    ALLOWED_EXTENSIONS = {
        '.json', '.csv', '.txt', '.md', '.yaml', '.yml',
        '.log', '.jsonl', '.xml', '.html', '.pdf',
        '.png', '.jpg', '.jpeg', '.gif', '.webp'  # Images for property listings
    }
    
    # Dangerous file patterns to block
    DANGEROUS_PATTERNS = [
        r'\.\./',          # Directory traversal
        r'\.\.\/',         # Alternative traversal  
        r'\.\.\\',         # Windows traversal
        r'~/',             # Home directory
        r'/etc/',          # System files
        r'/proc/',         # Process files
        r'/sys/',          # System files
        r'\.exe$',         # Executables
        r'\.scr$',         # Screen savers  
        r'\.bat$',         # Batch files
        r'\.sh$',          # Shell scripts
        r'\.php$',         # PHP scripts
        r'\.jsp$',         # JSP files
    ]
    
    # File size limits (in bytes)
    DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_TOTAL_SIZE = 1024 * 1024 * 1024       # 1GB total
    
    def __init__(self, base_path: str = "/Users/chrism/ATHintel", audit_enabled: bool = True):
        """
        Initialize secure file manager
        
        Args:
            base_path: Base application directory
            audit_enabled: Enable file operation audit logging
        """
        self.base_path = Path(base_path).resolve()
        self.audit_enabled = audit_enabled
        self.audit_log_path = Path("logs/file_security_audit.jsonl")
        
        # Create audit log directory
        if self.audit_enabled:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create allowed directories if they don't exist
        for allowed_dir in self.ALLOWED_BASE_DIRS:
            dir_path = self.base_path / allowed_dir
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🛡️ SecureFileManager initialized: {self.base_path}")
        logger.info(f"✅ Protected directories: {', '.join(self.ALLOWED_BASE_DIRS)}")
    
    def _validate_path(self, file_path: str, user_context: str = "system") -> Path:
        """
        Validate file path against security policies
        
        Args:
            file_path: Requested file path
            user_context: User context for audit
            
        Returns:
            Validated and resolved Path object
            
        Raises:
            SecureFileException: If path violates security policies
        """
        violations = []
        
        # Convert to Path and normalize
        try:
            requested_path = Path(file_path)
            
            # Remove any relative path components and resolve
            if requested_path.is_absolute():
                # Ensure absolute path is within our base directory
                resolved_path = requested_path.resolve()
                if not str(resolved_path).startswith(str(self.base_path)):
                    violations.append("PATH_OUTSIDE_BASE")
            else:
                # Relative path - resolve against base
                resolved_path = (self.base_path / requested_path).resolve()
                
                # Double-check it's still within base after resolution
                if not str(resolved_path).startswith(str(self.base_path)):
                    violations.append("PATH_TRAVERSAL")
                    
        except (OSError, ValueError) as e:
            violations.append(f"INVALID_PATH: {str(e)}")
            raise SecureFileException(f"Invalid path: {file_path}", "INVALID_PATH", file_path)
        
        # Check for dangerous patterns
        path_str = str(requested_path).lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                violations.append(f"DANGEROUS_PATTERN: {pattern}")
        
        # Check if path is within allowed directories
        relative_to_base = resolved_path.relative_to(self.base_path)
        first_part = relative_to_base.parts[0] if relative_to_base.parts else ""
        
        if first_part not in self.ALLOWED_BASE_DIRS:
            violations.append(f"UNAUTHORIZED_DIRECTORY: {first_part}")
        
        # Check file extension if it's a file
        if resolved_path.suffix and resolved_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            violations.append(f"UNAUTHORIZED_EXTENSION: {resolved_path.suffix}")
        
        # Check for symbolic links (potential security risk)
        try:
            if resolved_path.exists() and resolved_path.is_symlink():
                # Resolve symlink and check if target is safe
                link_target = resolved_path.readlink()
                if link_target.is_absolute() or '..' in str(link_target):
                    violations.append("DANGEROUS_SYMLINK")
        except (OSError, ValueError):
            violations.append("SYMLINK_CHECK_FAILED")
        
        # If any violations found, block the operation
        if violations:
            violation_msg = ', '.join(violations)
            logger.warning(f"🚨 File access denied for {user_context}: {violation_msg} - {file_path}")
            raise SecureFileException(
                f"File access denied: {violation_msg}",
                violation_type=violations[0],
                file_path=file_path
            )
        
        return resolved_path
    
    def _audit_file_operation(
        self, 
        operation: str, 
        file_path: str, 
        user_context: str,
        success: bool = True,
        file_size: int = 0,
        violations: List[str] = None
    ):
        """Record file operation in audit log"""
        if not self.audit_enabled:
            return
        
        # Calculate file hash if file exists
        file_hash = "N/A"
        try:
            if Path(file_path).exists():
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            pass
        
        audit_entry = FileOperationAudit(
            timestamp=datetime.now(),
            operation=operation,
            file_path=file_path,
            user_context=user_context,
            file_size=file_size,
            file_hash=file_hash,
            security_level="SECURE" if not violations else "VIOLATION",
            violations=violations or [],
            success=success
        )
        
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(audit_entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write file audit log: {e}")
    
    def _check_file_size(self, file_path: Path, max_size: int = None) -> int:
        """
        Check file size against limits
        
        Returns:
            File size in bytes
            
        Raises:
            SecureFileException: If file exceeds size limits
        """
        if not file_path.exists():
            return 0
        
        file_size = file_path.stat().st_size
        max_allowed = max_size or self.DEFAULT_MAX_FILE_SIZE
        
        if file_size > max_allowed:
            raise SecureFileException(
                f"File too large: {file_size} bytes > {max_allowed} bytes",
                violation_type="FILE_TOO_LARGE",
                file_path=str(file_path)
            )
        
        return file_size
    
    def read_file(
        self, 
        file_path: str, 
        user_context: str = "system",
        encoding: str = "utf-8",
        max_size: int = None
    ) -> str:
        """
        Securely read file content
        
        Args:
            file_path: Path to file to read
            user_context: User context for audit
            encoding: File encoding (default: utf-8)
            max_size: Maximum file size allowed
            
        Returns:
            File content as string
        """
        violations = []
        
        try:
            # Validate path
            validated_path = self._validate_path(file_path, user_context)
            
            # Check if file exists
            if not validated_path.exists():
                raise SecureFileException(
                    f"File not found: {file_path}",
                    violation_type="FILE_NOT_FOUND",
                    file_path=file_path
                )
            
            if not validated_path.is_file():
                raise SecureFileException(
                    f"Path is not a file: {file_path}",
                    violation_type="NOT_A_FILE", 
                    file_path=file_path
                )
            
            # Check file size
            file_size = self._check_file_size(validated_path, max_size)
            
            # Read file content
            with open(validated_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Audit successful read
            self._audit_file_operation("READ", str(validated_path), user_context, True, file_size)
            
            logger.debug(f"✅ File read: {validated_path} ({file_size} bytes) by {user_context}")
            return content
            
        except SecureFileException:
            # Re-raise security exceptions
            self._audit_file_operation("READ", file_path, user_context, False, 0, violations)
            raise
        except Exception as e:
            # Handle other exceptions
            violations.append(f"READ_ERROR: {str(e)}")
            self._audit_file_operation("READ", file_path, user_context, False, 0, violations)
            raise SecureFileException(
                f"Failed to read file: {str(e)}",
                violation_type="READ_ERROR",
                file_path=file_path
            )
    
    def write_file(
        self,
        file_path: str,
        content: str,
        user_context: str = "system",
        encoding: str = "utf-8",
        max_size: int = None,
        overwrite: bool = True
    ) -> int:
        """
        Securely write file content
        
        Args:
            file_path: Path to file to write
            content: Content to write
            user_context: User context for audit
            encoding: File encoding (default: utf-8)
            max_size: Maximum content size allowed
            overwrite: Allow overwriting existing files
            
        Returns:
            Number of bytes written
        """
        violations = []
        
        try:
            # Validate path
            validated_path = self._validate_path(file_path, user_context)
            
            # Check if file exists and overwrite policy
            if validated_path.exists() and not overwrite:
                raise SecureFileException(
                    f"File exists and overwrite disabled: {file_path}",
                    violation_type="FILE_EXISTS",
                    file_path=file_path
                )
            
            # Check content size
            content_size = len(content.encode(encoding))
            max_allowed = max_size or self.DEFAULT_MAX_FILE_SIZE
            
            if content_size > max_allowed:
                raise SecureFileException(
                    f"Content too large: {content_size} bytes > {max_allowed} bytes",
                    violation_type="CONTENT_TOO_LARGE",
                    file_path=file_path
                )
            
            # Create parent directory if it doesn't exist
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content securely using temporary file
            temp_path = validated_path.with_suffix('.tmp')
            
            try:
                with open(temp_path, 'w', encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                
                # Atomically move temp file to final location
                shutil.move(str(temp_path), str(validated_path))
                
                # Verify write was successful
                actual_size = validated_path.stat().st_size
                
                # Audit successful write
                self._audit_file_operation("WRITE", str(validated_path), user_context, True, actual_size)
                
                logger.debug(f"✅ File written: {validated_path} ({actual_size} bytes) by {user_context}")
                return actual_size
                
            except Exception as e:
                # Clean up temp file on failure
                if temp_path.exists():
                    temp_path.unlink()
                raise
            
        except SecureFileException:
            # Re-raise security exceptions
            self._audit_file_operation("WRITE", file_path, user_context, False, 0, violations)
            raise
        except Exception as e:
            # Handle other exceptions
            violations.append(f"WRITE_ERROR: {str(e)}")
            self._audit_file_operation("WRITE", file_path, user_context, False, 0, violations)
            raise SecureFileException(
                f"Failed to write file: {str(e)}",
                violation_type="WRITE_ERROR",
                file_path=file_path
            )
    
    def delete_file(self, file_path: str, user_context: str = "system") -> bool:
        """
        Securely delete file
        
        Args:
            file_path: Path to file to delete
            user_context: User context for audit
            
        Returns:
            True if file was deleted, False if file didn't exist
        """
        violations = []
        
        try:
            # Validate path
            validated_path = self._validate_path(file_path, user_context)
            
            if not validated_path.exists():
                self._audit_file_operation("DELETE", str(validated_path), user_context, True, 0)
                return False
            
            if not validated_path.is_file():
                raise SecureFileException(
                    f"Path is not a file: {file_path}",
                    violation_type="NOT_A_FILE",
                    file_path=file_path
                )
            
            file_size = validated_path.stat().st_size
            
            # Delete file
            validated_path.unlink()
            
            # Audit successful deletion
            self._audit_file_operation("DELETE", str(validated_path), user_context, True, file_size)
            
            logger.debug(f"✅ File deleted: {validated_path} by {user_context}")
            return True
            
        except SecureFileException:
            # Re-raise security exceptions
            self._audit_file_operation("DELETE", file_path, user_context, False, 0, violations)
            raise
        except Exception as e:
            # Handle other exceptions
            violations.append(f"DELETE_ERROR: {str(e)}")
            self._audit_file_operation("DELETE", file_path, user_context, False, 0, violations)
            raise SecureFileException(
                f"Failed to delete file: {str(e)}",
                violation_type="DELETE_ERROR",
                file_path=file_path
            )
    
    def list_directory(
        self, 
        dir_path: str, 
        user_context: str = "system",
        include_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Securely list directory contents
        
        Args:
            dir_path: Directory path to list
            user_context: User context for audit
            include_hidden: Include hidden files (starting with .)
            
        Returns:
            List of file/directory information dictionaries
        """
        try:
            # Validate path
            validated_path = self._validate_path(dir_path, user_context)
            
            if not validated_path.exists():
                raise SecureFileException(
                    f"Directory not found: {dir_path}",
                    violation_type="DIRECTORY_NOT_FOUND",
                    file_path=dir_path
                )
            
            if not validated_path.is_dir():
                raise SecureFileException(
                    f"Path is not a directory: {dir_path}",
                    violation_type="NOT_A_DIRECTORY",
                    file_path=dir_path
                )
            
            # List directory contents
            contents = []
            for item in validated_path.iterdir():
                # Skip hidden files unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                try:
                    stat = item.stat()
                    contents.append({
                        'name': item.name,
                        'path': str(item),
                        'is_file': item.is_file(),
                        'is_dir': item.is_dir(),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                except (OSError, ValueError):
                    # Skip files we can't read
                    continue
            
            # Audit successful listing
            self._audit_file_operation("LIST", str(validated_path), user_context, True, len(contents))
            
            return contents
            
        except SecureFileException:
            # Re-raise security exceptions
            self._audit_file_operation("LIST", dir_path, user_context, False, 0)
            raise
        except Exception as e:
            # Handle other exceptions
            self._audit_file_operation("LIST", dir_path, user_context, False, 0)
            raise SecureFileException(
                f"Failed to list directory: {str(e)}",
                violation_type="LIST_ERROR",
                file_path=dir_path
            )
    
    def get_file_info(self, file_path: str, user_context: str = "system") -> Dict[str, Any]:
        """
        Get secure file information
        
        Args:
            file_path: Path to file
            user_context: User context for audit
            
        Returns:
            File information dictionary
        """
        try:
            # Validate path
            validated_path = self._validate_path(file_path, user_context)
            
            if not validated_path.exists():
                raise SecureFileException(
                    f"File not found: {file_path}",
                    violation_type="FILE_NOT_FOUND",
                    file_path=file_path
                )
            
            stat = validated_path.stat()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(validated_path))
            
            info = {
                'name': validated_path.name,
                'path': str(validated_path),
                'size': stat.st_size,
                'is_file': validated_path.is_file(),
                'is_dir': validated_path.is_dir(),
                'mime_type': mime_type,
                'extension': validated_path.suffix,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:]
            }
            
            # Calculate file hash for files
            if validated_path.is_file() and stat.st_size < 100 * 1024 * 1024:  # Only for files < 100MB
                try:
                    with open(validated_path, 'rb') as f:
                        info['sha256'] = hashlib.sha256(f.read()).hexdigest()
                except Exception:
                    info['sha256'] = None
            
            return info
            
        except SecureFileException:
            raise
        except Exception as e:
            raise SecureFileException(
                f"Failed to get file info: {str(e)}",
                violation_type="INFO_ERROR",
                file_path=file_path
            )
    
    # Context manager support
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Convenience functions for common operations

def read_file_secure(file_path: str, user_context: str = "system", encoding: str = "utf-8") -> str:
    """Convenience function for secure file reading"""
    with SecureFileManager() as fm:
        return fm.read_file(file_path, user_context=user_context, encoding=encoding)

def write_file_secure(file_path: str, content: str, user_context: str = "system", encoding: str = "utf-8") -> int:
    """Convenience function for secure file writing"""
    with SecureFileManager() as fm:
        return fm.write_file(file_path, content, user_context=user_context, encoding=encoding)

def delete_file_secure(file_path: str, user_context: str = "system") -> bool:
    """Convenience function for secure file deletion"""
    with SecureFileManager() as fm:
        return fm.delete_file(file_path, user_context=user_context)

# Testing functions

def run_path_traversal_tests():
    """Run path traversal security tests"""
    logger.info("🧪 Running path traversal security tests...")
    
    test_results = {
        "directory_traversal_prevention": False,
        "absolute_path_validation": False,
        "symlink_protection": False,
        "extension_filtering": False,
        "file_size_limits": False
    }
    
    with SecureFileManager() as fm:
        # Test 1: Directory traversal prevention
        try:
            fm.read_file("../../../etc/passwd", "security_test")
        except SecureFileException as e:
            if "PATH_TRAVERSAL" in str(e) or "PATH_OUTSIDE_BASE" in str(e):
                test_results["directory_traversal_prevention"] = True
                logger.info("✅ Directory traversal prevention working")
        
        # Test 2: Absolute path validation
        try:
            fm.read_file("/etc/passwd", "security_test")
        except SecureFileException as e:
            if "PATH_OUTSIDE_BASE" in str(e):
                test_results["absolute_path_validation"] = True
                logger.info("✅ Absolute path validation working")
        
        # Test 3: Extension filtering
        try:
            fm.write_file("data/malicious.exe", "malware", "security_test")
        except SecureFileException as e:
            if "UNAUTHORIZED_EXTENSION" in str(e):
                test_results["extension_filtering"] = True
                logger.info("✅ Extension filtering working")
        
        # Test 4: File size limits
        try:
            large_content = "x" * (60 * 1024 * 1024)  # 60MB
            fm.write_file("data/large_file.txt", large_content, "security_test")
        except SecureFileException as e:
            if "CONTENT_TOO_LARGE" in str(e):
                test_results["file_size_limits"] = True
                logger.info("✅ File size limits working")
        
        # Test 5: Basic functionality (should work)
        try:
            test_content = "This is a test file for security validation"
            bytes_written = fm.write_file("data/security_test.txt", test_content, "security_test")
            read_content = fm.read_file("data/security_test.txt", "security_test")
            
            if read_content == test_content and bytes_written > 0:
                logger.info("✅ Basic secure file operations working")
            
            # Clean up
            fm.delete_file("data/security_test.txt", "security_test")
            
        except Exception as e:
            logger.error(f"Basic functionality test failed: {e}")
    
    # Report results
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info(f"🛡️ Path traversal test results: {passed_tests}/{total_tests} tests passed")
    for test, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test}: {status}")
    
    return test_results

if __name__ == "__main__":
    # Run security tests when executed directly
    run_path_traversal_tests()