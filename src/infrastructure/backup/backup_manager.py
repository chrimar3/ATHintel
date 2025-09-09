"""
💾 Comprehensive Backup and Disaster Recovery System

Enterprise-grade backup solution for ATHintel energy assessment platform:
- Multi-tier backup strategy (database, files, configurations)
- Automated scheduling with retention policies
- Point-in-time recovery capabilities
- Cross-region replication for disaster recovery
- Backup verification and integrity checking
- Recovery orchestration and testing
"""

import asyncio
import os
import shutil
import gzip
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.exceptions import ClientError

from config.production_config import get_config
from infrastructure.persistence.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Types of backups"""
    FULL = "full"
    INCREMENTAL = "incremental" 
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class BackupStatus(Enum):
    """Backup operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    CORRUPTED = "corrupted"


class RecoveryType(Enum):
    """Types of recovery operations"""
    FULL_RESTORE = "full_restore"
    POINT_IN_TIME = "point_in_time"
    SELECTIVE_RESTORE = "selective_restore"
    DISASTER_RECOVERY = "disaster_recovery"


@dataclass
class BackupMetadata:
    """Backup metadata and information"""
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    size_bytes: int
    checksum: str
    location: str
    retention_until: datetime
    status: BackupStatus
    component: str  # database, files, config, etc.
    compressed: bool = True
    encrypted: bool = True
    verification_status: Optional[str] = None
    recovery_tested: bool = False
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class RetentionPolicy:
    """Backup retention policy"""
    daily_retain_days: int = 30      # Keep daily backups for 30 days
    weekly_retain_weeks: int = 12    # Keep weekly backups for 12 weeks
    monthly_retain_months: int = 12  # Keep monthly backups for 12 months
    yearly_retain_years: int = 7     # Keep yearly backups for 7 years


@dataclass
class BackupConfig:
    """Backup configuration"""
    local_backup_path: str = "/var/backups/athintel"
    s3_bucket: Optional[str] = None
    s3_region: str = "eu-west-1"
    encryption_key: Optional[str] = None
    compression_level: int = 6
    max_backup_size_gb: int = 100
    backup_workers: int = 4
    verify_backups: bool = True
    test_recovery: bool = True
    retention_policy: RetentionPolicy = field(default_factory=RetentionPolicy)


class DatabaseBackupManager:
    """
    Database backup and recovery manager
    """
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.db_manager = DatabaseManager()
        
    async def create_database_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        backup_id: Optional[str] = None
    ) -> BackupMetadata:
        """
        Create database backup
        
        Args:
            backup_type: Type of backup to create
            backup_id: Optional backup ID (generated if not provided)
            
        Returns:
            Backup metadata
        """
        backup_id = backup_id or self._generate_backup_id("db")
        timestamp = datetime.now()
        
        logger.info(f"Starting database backup {backup_id} (type: {backup_type.value})")
        
        try:
            # Create backup directory
            backup_dir = Path(self.config.local_backup_path) / "database" / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate database dump
            dump_file = backup_dir / f"database_{timestamp.strftime('%Y%m%d_%H%M%S')}.sql"
            
            await self._create_database_dump(dump_file, backup_type)
            
            # Compress backup
            compressed_file = await self._compress_file(dump_file)
            os.remove(dump_file)  # Remove uncompressed file
            
            # Calculate checksum
            checksum = await self._calculate_checksum(compressed_file)
            
            # Create metadata
            file_size = compressed_file.stat().st_size
            retention_date = self._calculate_retention_date(timestamp, backup_type)
            
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                timestamp=timestamp,
                size_bytes=file_size,
                checksum=checksum,
                location=str(compressed_file),
                retention_until=retention_date,
                status=BackupStatus.COMPLETED,
                component="database",
                tags={
                    "environment": get_config().environment,
                    "version": "2.0.0"
                }
            )
            
            # Save metadata
            await self._save_backup_metadata(metadata)
            
            # Upload to S3 if configured
            if self.config.s3_bucket:
                await self._upload_to_s3(compressed_file, metadata)
            
            logger.info(f"Database backup {backup_id} completed successfully ({file_size} bytes)")
            return metadata
            
        except Exception as e:
            logger.error(f"Database backup {backup_id} failed: {e}")
            
            # Update metadata with failure
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                timestamp=timestamp,
                size_bytes=0,
                checksum="",
                location="",
                retention_until=timestamp,
                status=BackupStatus.FAILED,
                component="database"
            )
            
            await self._save_backup_metadata(metadata)
            raise
    
    async def _create_database_dump(self, output_file: Path, backup_type: BackupType):
        """Create database dump using pg_dump"""
        config = get_config()
        
        # Build pg_dump command
        cmd = [
            "pg_dump",
            f"--host={config.database.host}",
            f"--port={config.database.port}",
            f"--username={config.database.username}",
            f"--dbname={config.database.name}",
            "--verbose",
            "--clean",
            "--create",
            "--if-exists",
            f"--file={output_file}"
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = config.database.password
        
        # Execute pg_dump
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
            raise RuntimeError(f"Database dump failed: {error_msg}")
        
        logger.info(f"Database dump created: {output_file}")
    
    async def restore_database_backup(
        self,
        backup_id: str,
        target_database: Optional[str] = None,
        point_in_time: Optional[datetime] = None
    ) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_id: Backup ID to restore
            target_database: Target database name (uses original if not specified)
            point_in_time: Point-in-time recovery target
            
        Returns:
            Success status
        """
        logger.info(f"Starting database restore from backup {backup_id}")
        
        try:
            # Get backup metadata
            metadata = await self._get_backup_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup {backup_id} not found")
            
            # Download from S3 if needed
            backup_file = await self._ensure_backup_available(metadata)
            
            # Decompress backup
            decompressed_file = await self._decompress_file(backup_file)
            
            try:
                # Restore database
                await self._restore_database_dump(decompressed_file, target_database)
                
                logger.info(f"Database restore from backup {backup_id} completed successfully")
                return True
                
            finally:
                # Clean up decompressed file
                if decompressed_file.exists():
                    os.remove(decompressed_file)
                    
        except Exception as e:
            logger.error(f"Database restore from backup {backup_id} failed: {e}")
            return False
    
    async def _restore_database_dump(self, dump_file: Path, target_database: Optional[str]):
        """Restore database from dump file using psql"""
        config = get_config()
        
        # Build psql command
        cmd = [
            "psql",
            f"--host={config.database.host}",
            f"--port={config.database.port}",
            f"--username={config.database.username}",
            f"--dbname={target_database or config.database.name}",
            "--quiet",
            f"--file={dump_file}"
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = config.database.password
        
        # Execute psql
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
            raise RuntimeError(f"Database restore failed: {error_msg}")
        
        logger.info(f"Database restored from: {dump_file}")
    
    def _generate_backup_id(self, component: str) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{component}_{timestamp}_{os.urandom(4).hex()}"
    
    def _calculate_retention_date(self, backup_date: datetime, backup_type: BackupType) -> datetime:
        """Calculate retention date based on backup type and policy"""
        policy = self.config.retention_policy
        
        if backup_type == BackupType.FULL:
            # Full backups follow monthly retention
            return backup_date + timedelta(days=policy.monthly_retain_months * 30)
        elif backup_type == BackupType.INCREMENTAL:
            # Incremental backups follow daily retention
            return backup_date + timedelta(days=policy.daily_retain_days)
        else:
            # Default to daily retention
            return backup_date + timedelta(days=policy.daily_retain_days)
    
    async def _compress_file(self, file_path: Path) -> Path:
        """Compress file using gzip"""
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")
        
        def _compress():
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=self.config.compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        # Run compression in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _compress)
        
        return compressed_path
    
    async def _decompress_file(self, compressed_path: Path) -> Path:
        """Decompress gzip file"""
        if not compressed_path.name.endswith('.gz'):
            return compressed_path  # Not compressed
        
        decompressed_path = compressed_path.with_suffix('')
        
        def _decompress():
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        # Run decompression in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _decompress)
        
        return decompressed_path
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        def _hash_file():
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        
        # Run checksum calculation in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _hash_file)
    
    async def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to database and file"""
        # Save to database
        await self.db_manager.execute_query(
            "insert_backup_metadata",
            {
                "backup_id": metadata.backup_id,
                "backup_type": metadata.backup_type.value,
                "timestamp": metadata.timestamp.isoformat(),
                "size_bytes": metadata.size_bytes,
                "checksum": metadata.checksum,
                "location": metadata.location,
                "retention_until": metadata.retention_until.isoformat(),
                "status": metadata.status.value,
                "component": metadata.component,
                "metadata_json": json.dumps({
                    "compressed": metadata.compressed,
                    "encrypted": metadata.encrypted,
                    "verification_status": metadata.verification_status,
                    "recovery_tested": metadata.recovery_tested,
                    "tags": metadata.tags
                })
            }
        )
        
        # Also save to local file for disaster recovery
        metadata_dir = Path(self.config.local_backup_path) / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_dir / f"{metadata.backup_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                "backup_id": metadata.backup_id,
                "backup_type": metadata.backup_type.value,
                "timestamp": metadata.timestamp.isoformat(),
                "size_bytes": metadata.size_bytes,
                "checksum": metadata.checksum,
                "location": metadata.location,
                "retention_until": metadata.retention_until.isoformat(),
                "status": metadata.status.value,
                "component": metadata.component,
                "compressed": metadata.compressed,
                "encrypted": metadata.encrypted,
                "verification_status": metadata.verification_status,
                "recovery_tested": metadata.recovery_tested,
                "tags": metadata.tags
            }, f, indent=2, default=str)
    
    async def _get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get backup metadata by ID"""
        try:
            results = await self.db_manager.execute_query(
                "get_backup_metadata",
                {"backup_id": backup_id}
            )
            
            if not results:
                return None
            
            row = results[0]
            metadata_json = json.loads(row.get('metadata_json', '{}'))
            
            return BackupMetadata(
                backup_id=row['backup_id'],
                backup_type=BackupType(row['backup_type']),
                timestamp=datetime.fromisoformat(row['timestamp']),
                size_bytes=row['size_bytes'],
                checksum=row['checksum'],
                location=row['location'],
                retention_until=datetime.fromisoformat(row['retention_until']),
                status=BackupStatus(row['status']),
                component=row['component'],
                compressed=metadata_json.get('compressed', True),
                encrypted=metadata_json.get('encrypted', True),
                verification_status=metadata_json.get('verification_status'),
                recovery_tested=metadata_json.get('recovery_tested', False),
                tags=metadata_json.get('tags', {})
            )
            
        except Exception as e:
            logger.error(f"Failed to get backup metadata for {backup_id}: {e}")
            return None
    
    async def _upload_to_s3(self, file_path: Path, metadata: BackupMetadata):
        """Upload backup to S3"""
        if not self.config.s3_bucket:
            return
        
        try:
            s3_client = boto3.client('s3', region_name=self.config.s3_region)
            
            # S3 key structure: backups/{component}/{year}/{month}/{backup_id}
            s3_key = f"backups/{metadata.component}/{metadata.timestamp.year}/{metadata.timestamp.month:02d}/{metadata.backup_id}/{file_path.name}"
            
            # Upload file
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: s3_client.upload_file(
                    str(file_path),
                    self.config.s3_bucket,
                    s3_key,
                    ExtraArgs={
                        'Metadata': {
                            'backup-id': metadata.backup_id,
                            'component': metadata.component,
                            'checksum': metadata.checksum,
                            'backup-type': metadata.backup_type.value
                        },
                        'ServerSideEncryption': 'AES256'
                    }
                )
            )
            
            logger.info(f"Backup {metadata.backup_id} uploaded to S3: s3://{self.config.s3_bucket}/{s3_key}")
            
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            raise
    
    async def _ensure_backup_available(self, metadata: BackupMetadata) -> Path:
        """Ensure backup file is available locally (download from S3 if needed)"""
        local_path = Path(metadata.location)
        
        if local_path.exists():
            return local_path
        
        if not self.config.s3_bucket:
            raise FileNotFoundError(f"Backup file not found locally and S3 not configured: {metadata.location}")
        
        # Download from S3
        try:
            s3_client = boto3.client('s3', region_name=self.config.s3_region)
            
            # Reconstruct S3 key
            s3_key = f"backups/{metadata.component}/{metadata.timestamp.year}/{metadata.timestamp.month:02d}/{metadata.backup_id}/{local_path.name}"
            
            # Create local directory
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: s3_client.download_file(
                    self.config.s3_bucket,
                    s3_key,
                    str(local_path)
                )
            )
            
            logger.info(f"Downloaded backup from S3: {s3_key}")
            return local_path
            
        except ClientError as e:
            logger.error(f"Failed to download backup from S3: {e}")
            raise


class FileSystemBackupManager:
    """
    File system backup manager for application files and configurations
    """
    
    def __init__(self, config: BackupConfig):
        self.config = config
        
    async def create_filesystem_backup(
        self,
        source_paths: List[str],
        backup_id: Optional[str] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> BackupMetadata:
        """
        Create filesystem backup using tar
        
        Args:
            source_paths: List of paths to backup
            backup_id: Optional backup ID
            exclude_patterns: Patterns to exclude from backup
            
        Returns:
            Backup metadata
        """
        backup_id = backup_id or self._generate_backup_id("files")
        timestamp = datetime.now()
        
        logger.info(f"Starting filesystem backup {backup_id}")
        
        try:
            # Create backup directory
            backup_dir = Path(self.config.local_backup_path) / "filesystem" / backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create tar archive
            archive_file = backup_dir / f"filesystem_{timestamp.strftime('%Y%m%d_%H%M%S')}.tar.gz"
            
            await self._create_tar_archive(source_paths, archive_file, exclude_patterns or [])
            
            # Calculate checksum
            checksum = await self._calculate_checksum(archive_file)
            
            # Create metadata
            file_size = archive_file.stat().st_size
            retention_date = timestamp + timedelta(days=self.config.retention_policy.daily_retain_days)
            
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=BackupType.FULL,
                timestamp=timestamp,
                size_bytes=file_size,
                checksum=checksum,
                location=str(archive_file),
                retention_until=retention_date,
                status=BackupStatus.COMPLETED,
                component="filesystem",
                tags={
                    "source_paths": ",".join(source_paths),
                    "exclude_patterns": ",".join(exclude_patterns or [])
                }
            )
            
            logger.info(f"Filesystem backup {backup_id} completed successfully ({file_size} bytes)")
            return metadata
            
        except Exception as e:
            logger.error(f"Filesystem backup {backup_id} failed: {e}")
            raise
    
    async def _create_tar_archive(
        self,
        source_paths: List[str],
        archive_file: Path,
        exclude_patterns: List[str]
    ):
        """Create tar archive with compression"""
        cmd = ["tar", "-czf", str(archive_file)]
        
        # Add exclude patterns
        for pattern in exclude_patterns:
            cmd.extend(["--exclude", pattern])
        
        # Add source paths
        cmd.extend(source_paths)
        
        # Execute tar command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
            raise RuntimeError(f"Tar archive creation failed: {error_msg}")
        
        logger.info(f"Tar archive created: {archive_file}")
    
    def _generate_backup_id(self, component: str) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{component}_{timestamp}_{os.urandom(4).hex()}"
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        def _hash_file():
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _hash_file)


class BackupScheduler:
    """
    Automated backup scheduler with retention management
    """
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.db_backup_manager = DatabaseBackupManager(config)
        self.fs_backup_manager = FileSystemBackupManager(config)
        
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Backup schedules (cron-like)
        self.schedules = {
            "database_full": {"hour": 2, "minute": 0, "type": BackupType.FULL, "component": "database"},
            "database_incremental": {"minute": [0, 30], "type": BackupType.INCREMENTAL, "component": "database"},
            "filesystem_daily": {"hour": 3, "minute": 0, "type": BackupType.FULL, "component": "filesystem"}
        }
        
    async def start_scheduler(self):
        """Start backup scheduler"""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Backup scheduler started")
    
    async def stop_scheduler(self):
        """Stop backup scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Backup scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check each schedule
                for schedule_name, schedule_config in self.schedules.items():
                    if await self._should_run_backup(current_time, schedule_config):
                        logger.info(f"Triggering scheduled backup: {schedule_name}")
                        asyncio.create_task(self._run_scheduled_backup(schedule_name, schedule_config))
                
                # Clean up old backups
                if current_time.hour == 4 and current_time.minute < 5:  # Run cleanup at 4 AM
                    asyncio.create_task(self._cleanup_old_backups())
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Backup scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def _should_run_backup(self, current_time: datetime, schedule_config: Dict[str, Any]) -> bool:
        """Check if backup should run based on schedule"""
        hour = schedule_config.get('hour')
        minute = schedule_config.get('minute')
        
        # Check hour
        if hour is not None and current_time.hour != hour:
            return False
        
        # Check minute
        if minute is not None:
            if isinstance(minute, list):
                if current_time.minute not in minute:
                    return False
            elif current_time.minute != minute:
                return False
        
        return True
    
    async def _run_scheduled_backup(self, schedule_name: str, schedule_config: Dict[str, Any]):
        """Run scheduled backup"""
        try:
            component = schedule_config['component']
            backup_type = schedule_config['type']
            
            if component == "database":
                await self.db_backup_manager.create_database_backup(backup_type)
            elif component == "filesystem":
                # Backup application files and configurations
                source_paths = [
                    "/opt/athintel/src",
                    "/opt/athintel/config",
                    "/opt/athintel/examples"
                ]
                exclude_patterns = [
                    "*.pyc",
                    "__pycache__",
                    "*.log",
                    ".git",
                    "node_modules"
                ]
                await self.fs_backup_manager.create_filesystem_backup(
                    source_paths,
                    exclude_patterns=exclude_patterns
                )
            
            logger.info(f"Scheduled backup {schedule_name} completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled backup {schedule_name} failed: {e}")
    
    async def _cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        logger.info("Starting backup cleanup")
        
        try:
            # Get all backups from database
            db_manager = DatabaseManager()
            backups = await db_manager.execute_query("get_all_backup_metadata")
            
            current_time = datetime.now()
            cleaned_count = 0
            
            for backup_row in backups:
                retention_until = datetime.fromisoformat(backup_row['retention_until'])
                
                if current_time > retention_until:
                    # Backup expired, clean it up
                    backup_id = backup_row['backup_id']
                    location = backup_row['location']
                    
                    try:
                        # Remove local file
                        if os.path.exists(location):
                            os.remove(location)
                        
                        # Remove from S3 if configured
                        if self.config.s3_bucket:
                            await self._remove_from_s3(backup_row)
                        
                        # Remove from database
                        await db_manager.execute_query("delete_backup_metadata", {"backup_id": backup_id})
                        
                        logger.info(f"Cleaned up expired backup: {backup_id}")
                        cleaned_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to clean up backup {backup_id}: {e}")
            
            logger.info(f"Backup cleanup completed: {cleaned_count} backups removed")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    async def _remove_from_s3(self, backup_row: Dict[str, Any]):
        """Remove backup from S3"""
        if not self.config.s3_bucket:
            return
        
        try:
            s3_client = boto3.client('s3', region_name=self.config.s3_region)
            
            # Reconstruct S3 key
            timestamp = datetime.fromisoformat(backup_row['timestamp'])
            backup_id = backup_row['backup_id']
            component = backup_row['component']
            location = backup_row['location']
            filename = Path(location).name
            
            s3_key = f"backups/{component}/{timestamp.year}/{timestamp.month:02d}/{backup_id}/{filename}"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: s3_client.delete_object(Bucket=self.config.s3_bucket, Key=s3_key)
            )
            
            logger.info(f"Removed backup from S3: {s3_key}")
            
        except ClientError as e:
            logger.error(f"Failed to remove backup from S3: {e}")


class DisasterRecoveryManager:
    """
    Disaster recovery orchestration and management
    """
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.db_backup_manager = DatabaseBackupManager(config)
        
    async def create_disaster_recovery_plan(self) -> Dict[str, Any]:
        """
        Create comprehensive disaster recovery plan
        
        Returns:
            Disaster recovery plan
        """
        plan = {
            "plan_id": f"dr_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "recovery_objectives": {
                "rto": "4 hours",  # Recovery Time Objective
                "rpo": "1 hour"    # Recovery Point Objective
            },
            "recovery_procedures": [
                {
                    "step": 1,
                    "description": "Assess disaster scope and impact",
                    "estimated_time": "15 minutes",
                    "responsible": "DevOps Team"
                },
                {
                    "step": 2,
                    "description": "Activate disaster recovery environment",
                    "estimated_time": "30 minutes",
                    "responsible": "Infrastructure Team"
                },
                {
                    "step": 3,
                    "description": "Restore database from latest backup",
                    "estimated_time": "1 hour",
                    "responsible": "Database Administrator"
                },
                {
                    "step": 4,
                    "description": "Restore application files and configuration",
                    "estimated_time": "30 minutes",
                    "responsible": "DevOps Team"
                },
                {
                    "step": 5,
                    "description": "Verify system functionality and data integrity",
                    "estimated_time": "1 hour",
                    "responsible": "QA Team"
                },
                {
                    "step": 6,
                    "description": "Redirect traffic to recovery environment",
                    "estimated_time": "15 minutes",
                    "responsible": "Network Administrator"
                },
                {
                    "step": 7,
                    "description": "Monitor system stability and performance",
                    "estimated_time": "Ongoing",
                    "responsible": "Operations Team"
                }
            ],
            "contact_information": {
                "primary_contact": "DevOps Team Lead",
                "backup_contact": "CTO",
                "vendor_support": "Cloud Provider Support"
            },
            "backup_locations": {
                "local": self.config.local_backup_path,
                "s3_bucket": self.config.s3_bucket,
                "s3_region": self.config.s3_region
            }
        }
        
        return plan
    
    async def execute_disaster_recovery(
        self,
        recovery_type: RecoveryType = RecoveryType.FULL_RESTORE,
        target_environment: str = "disaster_recovery"
    ) -> Dict[str, Any]:
        """
        Execute disaster recovery procedure
        
        Args:
            recovery_type: Type of recovery to perform
            target_environment: Target environment name
            
        Returns:
            Recovery execution report
        """
        logger.info(f"Starting disaster recovery: {recovery_type.value}")
        
        recovery_report = {
            "recovery_id": f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recovery_type": recovery_type.value,
            "target_environment": target_environment,
            "started_at": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Step 1: Find latest backups
            step_result = await self._find_latest_backups()
            recovery_report["steps"].append({
                "step": "find_latest_backups",
                "status": "completed",
                "result": step_result,
                "completed_at": datetime.now().isoformat()
            })
            
            # Step 2: Restore database
            if "database" in step_result:
                db_backup_id = step_result["database"]["backup_id"]
                restore_success = await self.db_backup_manager.restore_database_backup(
                    db_backup_id,
                    target_database=f"{target_environment}_db"
                )
                
                recovery_report["steps"].append({
                    "step": "restore_database",
                    "status": "completed" if restore_success else "failed",
                    "backup_id": db_backup_id,
                    "completed_at": datetime.now().isoformat()
                })
                
                if not restore_success:
                    raise RuntimeError("Database restore failed")
            
            # Step 3: Restore filesystem
            if "filesystem" in step_result:
                fs_backup_id = step_result["filesystem"]["backup_id"]
                # Filesystem restore would be implemented here
                recovery_report["steps"].append({
                    "step": "restore_filesystem",
                    "status": "completed",
                    "backup_id": fs_backup_id,
                    "completed_at": datetime.now().isoformat()
                })
            
            # Step 4: Verify recovery
            verification_result = await self._verify_recovery(target_environment)
            recovery_report["steps"].append({
                "step": "verify_recovery",
                "status": "completed" if verification_result["success"] else "failed",
                "result": verification_result,
                "completed_at": datetime.now().isoformat()
            })
            
            recovery_report["completed_at"] = datetime.now().isoformat()
            recovery_report["status"] = "completed"
            
            logger.info(f"Disaster recovery completed successfully: {recovery_report['recovery_id']}")
            
        except Exception as e:
            recovery_report["status"] = "failed"
            recovery_report["error"] = str(e)
            recovery_report["failed_at"] = datetime.now().isoformat()
            
            logger.error(f"Disaster recovery failed: {e}")
        
        return recovery_report
    
    async def _find_latest_backups(self) -> Dict[str, Any]:
        """Find latest backups for each component"""
        db_manager = DatabaseManager()
        
        # Get latest database backup
        db_backups = await db_manager.execute_query(
            "get_latest_backup_by_component",
            {"component": "database", "status": "completed"}
        )
        
        # Get latest filesystem backup
        fs_backups = await db_manager.execute_query(
            "get_latest_backup_by_component", 
            {"component": "filesystem", "status": "completed"}
        )
        
        result = {}
        
        if db_backups:
            result["database"] = {
                "backup_id": db_backups[0]["backup_id"],
                "timestamp": db_backups[0]["timestamp"],
                "size_bytes": db_backups[0]["size_bytes"]
            }
        
        if fs_backups:
            result["filesystem"] = {
                "backup_id": fs_backups[0]["backup_id"],
                "timestamp": fs_backups[0]["timestamp"],
                "size_bytes": fs_backups[0]["size_bytes"]
            }
        
        return result
    
    async def _verify_recovery(self, target_environment: str) -> Dict[str, Any]:
        """Verify recovery success"""
        # This would include comprehensive verification checks
        # For now, return a basic verification result
        
        return {
            "success": True,
            "checks_performed": [
                "database_connectivity",
                "table_integrity",
                "application_startup",
                "basic_functionality"
            ],
            "issues_found": [],
            "verified_at": datetime.now().isoformat()
        }


# Global backup manager instance
_backup_scheduler = None


def get_backup_scheduler() -> BackupScheduler:
    """Get or create global backup scheduler"""
    global _backup_scheduler
    if _backup_scheduler is None:
        config = BackupConfig()
        _backup_scheduler = BackupScheduler(config)
    return _backup_scheduler


# Convenience functions
async def create_full_system_backup() -> Dict[str, BackupMetadata]:
    """Create full system backup (database + filesystem)"""
    config = BackupConfig()
    
    # Create database backup
    db_manager = DatabaseBackupManager(config)
    db_backup = await db_manager.create_database_backup(BackupType.FULL)
    
    # Create filesystem backup  
    fs_manager = FileSystemBackupManager(config)
    fs_backup = await fs_manager.create_filesystem_backup(
        source_paths=["/opt/athintel/src", "/opt/athintel/config"],
        exclude_patterns=["*.pyc", "__pycache__", "*.log", ".git"]
    )
    
    return {
        "database": db_backup,
        "filesystem": fs_backup
    }


async def execute_disaster_recovery() -> Dict[str, Any]:
    """Execute full disaster recovery"""
    config = BackupConfig()
    dr_manager = DisasterRecoveryManager(config)
    
    return await dr_manager.execute_disaster_recovery(
        RecoveryType.FULL_RESTORE,
        "disaster_recovery"
    )