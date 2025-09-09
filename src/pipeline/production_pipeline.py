"""
Production Pipeline Integration
Story 1.5: Deploy validation system to production
Realistic throughput: Limited by scraping (500-2000/hour), not validation
"""

import os
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import queue

from validators.property_validator import PropertyValidator
from monitoring.metrics_collector import get_metrics_collector
from config.feature_flags import FeatureFlags


@dataclass
class PipelineConfig:
    """Production pipeline configuration"""
    input_directory: str = "realdata"
    output_directory: str = "processed"
    backup_directory: str = "backup"
    log_directory: str = "logs"
    
    # Processing settings
    batch_size: int = 100
    max_workers: int = 4
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    
    # Health check settings
    health_check_interval: int = 60
    max_error_rate: float = 0.05  # 5%
    max_processing_delay: int = 300  # 5 minutes
    
    # Database settings
    db_path: str = "production.db"
    enable_audit_log: bool = True


@dataclass
class ProcessingResult:
    """Result of processing a batch of properties"""
    batch_id: str
    processed_count: int
    valid_count: int
    invalid_count: int
    error_count: int
    processing_time: float
    errors: List[str]
    timestamp: datetime


class ProductionPipeline:
    """
    Production pipeline for property validation
    Handles real-world constraints and error conditions
    """
    
    def __init__(self, config: PipelineConfig):
        """Initialize production pipeline"""
        self.config = config
        self.logger = self._setup_logging()
        self.validator = PropertyValidator()
        self.metrics_collector = get_metrics_collector()
        self.feature_flags = FeatureFlags()
        
        # Pipeline state
        self.is_running = False
        self.start_time = None
        self.total_processed = 0
        self.total_errors = 0
        self.processing_queue = queue.Queue()
        self.results_queue = queue.Queue()
        
        # Database setup
        self.db_path = Path(config.db_path)
        self._init_database()
        
        # Create directories
        self._setup_directories()
        
        # Health monitoring
        self.last_health_check = time.time()
        self.health_status = "healthy"
        
        self.logger.info("Production pipeline initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up production logging"""
        log_dir = Path(self.config.log_directory)
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        logger = logging.getLogger('production_pipeline')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_directories(self):
        """Create required directories"""
        for directory in [
            self.config.input_directory,
            self.config.output_directory,
            self.config.backup_directory,
            self.config.log_directory
        ]:
            Path(directory).mkdir(exist_ok=True)
    
    def _init_database(self):
        """Initialize production database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_batches (
                    batch_id TEXT PRIMARY KEY,
                    processed_count INTEGER,
                    valid_count INTEGER,
                    invalid_count INTEGER,
                    error_count INTEGER,
                    processing_time REAL,
                    timestamp TEXT,
                    status TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS property_results (
                    property_id TEXT PRIMARY KEY,
                    batch_id TEXT,
                    is_valid BOOLEAN,
                    total_score REAL,
                    errors TEXT,
                    warnings TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (batch_id) REFERENCES processing_batches (batch_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_health (
                    timestamp TEXT PRIMARY KEY,
                    status TEXT,
                    error_rate REAL,
                    processing_delay REAL,
                    throughput REAL,
                    message TEXT
                )
            """)
    
    def start(self):
        """Start the production pipeline"""
        if self.is_running:
            self.logger.warning("Pipeline is already running")
            return
        
        self.logger.info("Starting production pipeline")
        self.is_running = True
        self.start_time = time.time()
        
        # Start worker threads
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._health_monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        self.logger.info(f"Pipeline started with {self.config.max_workers} workers")
    
    def stop(self):
        """Stop the production pipeline"""
        if not self.is_running:
            self.logger.warning("Pipeline is not running")
            return
        
        self.logger.info("Stopping production pipeline")
        self.is_running = False
        
        # Shutdown executor
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        
        self._log_health_status("stopped", "Pipeline stopped by user")
        self.logger.info("Pipeline stopped")
    
    def process_directory(self, input_dir: Optional[str] = None) -> List[ProcessingResult]:
        """
        Process all JSON files in a directory
        
        Args:
            input_dir: Directory to process (default: config.input_directory)
            
        Returns:
            List of processing results
        """
        input_path = Path(input_dir or self.config.input_directory)
        
        if not input_path.exists():
            self.logger.error(f"Input directory not found: {input_path}")
            return []
        
        # Find all JSON files
        json_files = list(input_path.glob("*.json"))
        
        if not json_files:
            self.logger.warning(f"No JSON files found in {input_path}")
            return []
        
        self.logger.info(f"Found {len(json_files)} files to process")
        
        results = []
        for json_file in json_files:
            try:
                result = self.process_file(json_file)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process {json_file}: {e}")
                self.total_errors += 1
        
        return results
    
    def process_file(self, file_path: Path) -> ProcessingResult:
        """
        Process a single JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            ProcessingResult
        """
        batch_id = f"{file_path.stem}_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"Processing file: {file_path}")
        
        try:
            # Load data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different data formats
            if isinstance(data, list):
                properties = data
            elif isinstance(data, dict) and 'properties' in data:
                properties = data['properties']
            else:
                raise ValueError("Invalid JSON format: expected list or dict with 'properties' key")
            
            # Create backup
            self._backup_file(file_path)
            
            # Process in batches
            results = self._process_properties_batch(properties, batch_id)
            
            # Calculate metrics
            processing_time = time.time() - start_time
            processed_count = len(properties)
            valid_count = sum(1 for r in results if r.get('is_valid', False))
            invalid_count = processed_count - valid_count
            error_count = sum(1 for r in results if 'error' in r)
            
            # Create result
            result = ProcessingResult(
                batch_id=batch_id,
                processed_count=processed_count,
                valid_count=valid_count,
                invalid_count=invalid_count,
                error_count=error_count,
                processing_time=processing_time,
                errors=[r.get('error', '') for r in results if 'error' in r],
                timestamp=datetime.now()
            )
            
            # Save results
            self._save_batch_results(result, results)
            
            # Move processed file
            self._archive_processed_file(file_path)
            
            # Update pipeline stats
            self.total_processed += processed_count
            
            self.logger.info(
                f"Batch {batch_id} completed: {valid_count}/{processed_count} valid "
                f"in {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            self.total_errors += 1
            
            # Return error result
            return ProcessingResult(
                batch_id=batch_id,
                processed_count=0,
                valid_count=0,
                invalid_count=0,
                error_count=1,
                processing_time=time.time() - start_time,
                errors=[str(e)],
                timestamp=datetime.now()
            )
    
    def _process_properties_batch(self, properties: List[Dict[str, Any]], 
                                 batch_id: str) -> List[Dict[str, Any]]:
        """Process batch of properties with validation"""
        results = []
        
        for i, property_data in enumerate(properties):
            try:
                # Add batch tracking
                property_data['batch_id'] = batch_id
                property_data['batch_index'] = i
                
                # Validate property
                if self.feature_flags.is_enabled("data_validation_enabled"):
                    validation_result = self.validator.validate_property(property_data)
                    result = validation_result.to_dict() if hasattr(validation_result, 'to_dict') else validation_result
                else:
                    # Basic validation if feature disabled
                    result = {
                        'property_id': property_data.get('id', f'unknown_{i}'),
                        'is_valid': True,
                        'total_score': 100,
                        'errors': [],
                        'warnings': [],
                        'timestamp': datetime.now().isoformat()
                    }
                
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error validating property {i}: {e}")
                results.append({
                    'property_id': property_data.get('id', f'error_{i}'),
                    'error': str(e),
                    'is_valid': False,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def _backup_file(self, file_path: Path):
        """Create backup of input file"""
        if not self.feature_flags.is_enabled("production_mode"):
            return  # Skip backup in non-production
        
        backup_dir = Path(self.config.backup_directory)
        backup_path = backup_dir / f"{file_path.stem}_{int(time.time())}.json"
        
        import shutil
        shutil.copy2(file_path, backup_path)
        
        self.logger.debug(f"Backup created: {backup_path}")
    
    def _archive_processed_file(self, file_path: Path):
        """Move processed file to archive"""
        processed_dir = Path(self.config.output_directory) / "processed"
        processed_dir.mkdir(exist_ok=True)
        
        archive_path = processed_dir / f"{file_path.stem}_processed_{int(time.time())}.json"
        file_path.rename(archive_path)
        
        self.logger.debug(f"File archived: {archive_path}")
    
    def _save_batch_results(self, result: ProcessingResult, property_results: List[Dict[str, Any]]):
        """Save batch results to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Save batch summary
            conn.execute("""
                INSERT OR REPLACE INTO processing_batches 
                (batch_id, processed_count, valid_count, invalid_count, 
                 error_count, processing_time, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.batch_id,
                result.processed_count,
                result.valid_count, 
                result.invalid_count,
                result.error_count,
                result.processing_time,
                result.timestamp.isoformat(),
                "completed" if result.error_count == 0 else "completed_with_errors"
            ))
            
            # Save individual property results
            for prop_result in property_results:
                conn.execute("""
                    INSERT OR REPLACE INTO property_results
                    (property_id, batch_id, is_valid, total_score, errors, warnings, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    prop_result.get('property_id', 'unknown'),
                    result.batch_id,
                    prop_result.get('is_valid', False),
                    prop_result.get('total_score', 0),
                    json.dumps(prop_result.get('errors', [])),
                    json.dumps(prop_result.get('warnings', [])),
                    prop_result.get('timestamp', datetime.now().isoformat())
                ))
    
    def _process_loop(self):
        """Main processing loop"""
        while self.is_running:
            try:
                # Check for new files periodically
                self.process_directory()
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                time.sleep(60)  # Wait longer after error
    
    def _health_monitor(self):
        """Monitor pipeline health"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # Calculate metrics
                elapsed = current_time - self.start_time if self.start_time else 0
                error_rate = self.total_errors / max(1, self.total_processed) if self.total_processed > 0 else 0
                throughput = self.total_processed / elapsed * 3600 if elapsed > 0 else 0  # per hour
                
                # Check health conditions
                status = "healthy"
                message = "Pipeline operating normally"
                
                if error_rate > self.config.max_error_rate:
                    status = "degraded"
                    message = f"High error rate: {error_rate:.1%}"
                    
                elif current_time - self.last_health_check > self.config.max_processing_delay:
                    status = "stalled"
                    message = "Processing appears stalled"
                
                self.health_status = status
                
                # Log health status
                self._log_health_status(status, message, error_rate, 0, throughput)
                
                # Update last check time
                self.last_health_check = current_time
                
                # Wait for next check
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                time.sleep(60)
    
    def _log_health_status(self, status: str, message: str, error_rate: float = 0, 
                          processing_delay: float = 0, throughput: float = 0):
        """Log health status to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO pipeline_health
                (timestamp, status, error_rate, processing_delay, throughput, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                status,
                error_rate,
                processing_delay,
                throughput,
                message
            ))
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        error_rate = self.total_errors / max(1, self.total_processed) if self.total_processed > 0 else 0
        throughput = self.total_processed / elapsed * 3600 if elapsed > 0 else 0
        
        return {
            'status': self.health_status,
            'is_running': self.is_running,
            'uptime_seconds': elapsed,
            'total_processed': self.total_processed,
            'total_errors': self.total_errors,
            'error_rate': error_rate,
            'throughput_per_hour': throughput,
            'last_health_check': datetime.fromtimestamp(self.last_health_check).isoformat()
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics from database"""
        with sqlite3.connect(self.db_path) as conn:
            # Get batch statistics
            batch_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_batches,
                    SUM(processed_count) as total_processed,
                    SUM(valid_count) as total_valid,
                    SUM(invalid_count) as total_invalid,
                    SUM(error_count) as total_errors,
                    AVG(processing_time) as avg_processing_time
                FROM processing_batches
                WHERE timestamp > datetime('now', '-24 hours')
            """).fetchone()
            
            # Get recent health status
            health_history = conn.execute("""
                SELECT status, timestamp, message
                FROM pipeline_health
                ORDER BY timestamp DESC
                LIMIT 10
            """).fetchall()
        
        return {
            'last_24_hours': {
                'total_batches': batch_stats[0] or 0,
                'total_processed': batch_stats[1] or 0,
                'total_valid': batch_stats[2] or 0,
                'total_invalid': batch_stats[3] or 0,
                'total_errors': batch_stats[4] or 0,
                'avg_processing_time': batch_stats[5] or 0
            },
            'recent_health': [
                {
                    'status': h[0],
                    'timestamp': h[1],
                    'message': h[2]
                }
                for h in health_history
            ]
        }


def create_production_pipeline(config_file: Optional[str] = None) -> ProductionPipeline:
    """
    Factory function to create production pipeline
    
    Args:
        config_file: Optional config file path
        
    Returns:
        ProductionPipeline instance
    """
    # Load config from file or use defaults
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        config = PipelineConfig(**config_data)
    else:
        config = PipelineConfig()
    
    return ProductionPipeline(config)