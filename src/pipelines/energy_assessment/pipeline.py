"""
⚡ Energy Assessment Pipeline Implementation

Advanced pipeline architecture for processing energy assessments with real-time
capabilities, ML integration, and comprehensive error handling.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable
from decimal import Decimal
import logging

from domains.energy.entities.property_energy import PropertyEnergyEntity
from domains.energy.value_objects.energy_class import EnergyClass
from ml.energy_prediction.models import EnergyModelEnsemble
from ml.energy_prediction.features import FeatureExtractor
from infrastructure.cqrs import get_command_bus, get_event_publisher

logger = logging.getLogger(__name__)

class PipelineStage:
    """Base class for pipeline stages"""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.metrics = {
            'processed_count': 0,
            'error_count': 0,
            'total_processing_time': 0.0
        }
    
    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through this stage"""
        start_time = datetime.now()
        
        try:
            result = await self._execute(data, context)
            self.metrics['processed_count'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics['total_processing_time'] += processing_time
            
            logger.debug(f"Stage {self.stage_name} completed in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            self.metrics['error_count'] += 1
            logger.error(f"Stage {self.stage_name} failed: {e}")
            raise
    
    async def _execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method in subclasses"""
        raise NotImplementedError()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get stage performance metrics"""
        avg_time = (self.metrics['total_processing_time'] / 
                   max(self.metrics['processed_count'], 1))
        
        return {
            'stage_name': self.stage_name,
            'processed_count': self.metrics['processed_count'],
            'error_count': self.metrics['error_count'],
            'error_rate': self.metrics['error_count'] / max(self.metrics['processed_count'], 1),
            'average_processing_time': avg_time
        }

class EnergyAssessmentPipeline:
    """
    Main energy assessment pipeline orchestrator
    
    Processes property data through multiple stages:
    1. Data validation and normalization
    2. Feature extraction and engineering  
    3. ML prediction and confidence scoring
    4. Upgrade recommendation generation
    5. Report generation and storage
    """
    
    def __init__(self, ml_ensemble: Optional[EnergyModelEnsemble] = None):
        self.pipeline_id = str(uuid.uuid4())
        self.stages: List[PipelineStage] = []
        self.ml_ensemble = ml_ensemble or EnergyModelEnsemble()
        self.feature_extractor = FeatureExtractor()
        
        # Pipeline configuration
        self.config = {
            'enable_ml_predictions': True,
            'enable_recommendations': True,
            'enable_market_comparison': True,
            'parallel_processing': True,
            'cache_intermediate_results': True,
            'max_processing_time_seconds': 300  # 5 minutes timeout
        }
        
        # Initialize default stages
        self._setup_default_stages()
        
        # Event publisher for pipeline events
        self.event_publisher = get_event_publisher()
        
    def add_stage(self, stage: PipelineStage):
        """Add a processing stage to the pipeline"""
        self.stages.append(stage)
        logger.info(f"Added stage {stage.stage_name} to pipeline {self.pipeline_id}")
    
    async def process_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single property through the entire pipeline"""
        
        start_time = datetime.now()
        processing_id = str(uuid.uuid4())
        
        # Initialize processing context
        context = {
            'processing_id': processing_id,
            'pipeline_id': self.pipeline_id,
            'start_time': start_time,
            'property_id': property_data.get('property_id', 'unknown'),
            'config': self.config,
            'intermediate_results': {},
            'errors': [],
            'warnings': []
        }
        
        logger.info(f"Starting energy assessment for property {context['property_id']} "
                   f"(processing_id: {processing_id})")
        
        try:
            # Process through each stage
            current_data = property_data.copy()
            
            for i, stage in enumerate(self.stages):
                stage_start = datetime.now()
                
                logger.debug(f"Processing stage {i+1}/{len(self.stages)}: {stage.stage_name}")
                
                # Process stage
                current_data = await stage.process(current_data, context)
                
                # Store intermediate results if enabled
                if self.config['cache_intermediate_results']:
                    context['intermediate_results'][stage.stage_name] = current_data.copy()
                
                # Check timeout
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if elapsed_time > self.config['max_processing_time_seconds']:
                    raise TimeoutError(f"Pipeline processing exceeded {self.config['max_processing_time_seconds']}s")
            
            # Finalize results
            total_time = (datetime.now() - start_time).total_seconds()
            
            final_result = {
                'processing_id': processing_id,
                'property_id': context['property_id'],
                'assessment_result': current_data,
                'processing_metadata': {
                    'total_processing_time': total_time,
                    'stages_completed': len(self.stages),
                    'pipeline_version': '2.0',
                    'completed_at': datetime.now().isoformat(),
                    'warnings': context['warnings']
                }
            }
            
            logger.info(f"Property assessment completed in {total_time:.2f}s "
                       f"(processing_id: {processing_id})")
            
            return final_result
            
        except Exception as e:
            error_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"Pipeline processing failed after {error_time:.2f}s "
                        f"(processing_id: {processing_id}): {e}")
            
            return {
                'processing_id': processing_id,
                'property_id': context['property_id'],
                'success': False,
                'error': str(e),
                'processing_metadata': {
                    'total_processing_time': error_time,
                    'failed_at_stage': len([s for s in self.stages if s.metrics['processed_count'] > 0]),
                    'errors': context['errors']
                }
            }
    
    async def process_batch(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple properties in parallel"""
        
        if not self.config['parallel_processing']:
            # Sequential processing
            results = []
            for prop_data in properties:
                result = await self.process_property(prop_data)
                results.append(result)
            return results
        
        # Parallel processing with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent assessments
        
        async def process_with_semaphore(prop_data):
            async with semaphore:
                return await self.process_property(prop_data)
        
        tasks = [process_with_semaphore(prop_data) for prop_data in properties]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'processing_id': str(uuid.uuid4()),
                    'property_id': properties[i].get('property_id', f'property_{i}'),
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _setup_default_stages(self):
        """Setup default pipeline stages"""
        from .stages import (
            DataValidationStage,
            FeatureExtractionStage, 
            MLPredictionStage,
            RecommendationGenerationStage,
            ReportGenerationStage
        )
        
        # Add stages in processing order
        self.add_stage(DataValidationStage())
        self.add_stage(FeatureExtractionStage(self.feature_extractor))
        self.add_stage(MLPredictionStage(self.ml_ensemble))
        self.add_stage(RecommendationGenerationStage())
        self.add_stage(ReportGenerationStage())
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline performance metrics"""
        stage_metrics = [stage.get_metrics() for stage in self.stages]
        
        total_processed = sum(s['processed_count'] for s in stage_metrics)
        total_errors = sum(s['error_count'] for s in stage_metrics)
        avg_processing_time = sum(s['average_processing_time'] for s in stage_metrics)
        
        return {
            'pipeline_id': self.pipeline_id,
            'total_properties_processed': total_processed,
            'total_errors': total_errors,
            'overall_error_rate': total_errors / max(total_processed, 1),
            'average_end_to_end_time': avg_processing_time,
            'stage_metrics': stage_metrics,
            'configuration': self.config
        }

class RealTimeAssessmentService:
    """
    Real-time energy assessment service with caching and optimization
    """
    
    def __init__(self):
        self.pipeline = EnergyAssessmentPipeline()
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl_seconds = 3600  # 1 hour
        
        # Performance monitoring
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0.0
        }
    
    async def assess_property_realtime(
        self, 
        property_data: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Perform real-time energy assessment with caching"""
        
        self.metrics['total_requests'] += 1
        start_time = datetime.now()
        
        # Generate cache key
        cache_key = self._generate_cache_key(property_data) if use_cache else None
        
        # Check cache first
        if cache_key and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if datetime.now().timestamp() - cached_result['timestamp'] < self.cache_ttl_seconds:
                self.metrics['cache_hits'] += 1
                logger.debug(f"Cache hit for property {property_data.get('property_id', 'unknown')}")
                
                # Update response time metrics
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_response_time_metric(response_time)
                
                return cached_result['result']
        
        # Cache miss - process through pipeline
        self.metrics['cache_misses'] += 1
        result = await self.pipeline.process_property(property_data)
        
        # Cache result if successful
        if cache_key and result.get('success', True):
            self.cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().timestamp()
            }
        
        # Update metrics
        response_time = (datetime.now() - start_time).total_seconds()
        self._update_response_time_metric(response_time)
        
        return result
    
    def _generate_cache_key(self, property_data: Dict[str, Any]) -> str:
        """Generate cache key from property data"""
        # Use key property characteristics for caching
        key_data = {
            'construction_year': property_data.get('construction_year'),
            'total_area': property_data.get('total_area'),
            'building_type': property_data.get('building_type'),
            'heating_system': property_data.get('heating_system'),
            'location': property_data.get('location', {}).get('region')
        }
        
        # Simple hash-based key
        import hashlib
        import json
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _update_response_time_metric(self, response_time: float):
        """Update average response time metric"""
        total_requests = self.metrics['total_requests']
        current_avg = self.metrics['average_response_time']
        
        # Incremental average update
        self.metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get real-time service performance metrics"""
        cache_hit_rate = (self.metrics['cache_hits'] / 
                         max(self.metrics['total_requests'], 1))
        
        return {
            'total_requests': self.metrics['total_requests'],
            'cache_hit_rate': cache_hit_rate,
            'average_response_time': self.metrics['average_response_time'],
            'cache_size': len(self.cache),
            'pipeline_metrics': self.pipeline.get_pipeline_metrics()
        }
    
    def clear_cache(self):
        """Clear the assessment cache"""
        self.cache.clear()
        logger.info("Real-time assessment cache cleared")

class BatchAssessmentProcessor:
    """
    High-performance batch processor for large-scale energy assessments
    """
    
    def __init__(self):
        self.pipeline = EnergyAssessmentPipeline()
        self.batch_size = 100  # Process in batches of 100
        self.max_concurrent_batches = 5
        
    async def process_large_batch(
        self,
        properties: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process large batch of properties with progress tracking"""
        
        total_properties = len(properties)
        processed_count = 0
        successful_count = 0
        failed_count = 0
        
        start_time = datetime.now()
        batch_id = str(uuid.uuid4())
        
        logger.info(f"Starting batch assessment of {total_properties} properties "
                   f"(batch_id: {batch_id})")
        
        # Split into smaller batches
        batches = [
            properties[i:i + self.batch_size] 
            for i in range(0, total_properties, self.batch_size)
        ]
        
        results = []
        
        # Process batches with limited concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        async def process_batch(batch, batch_num):
            async with semaphore:
                logger.info(f"Processing batch {batch_num + 1}/{len(batches)}")
                batch_results = await self.pipeline.process_batch(batch)
                return batch_results
        
        # Execute all batches
        batch_tasks = [process_batch(batch, i) for i, batch in enumerate(batches)]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Aggregate results
        for batch_result in batch_results:
            for result in batch_result:
                results.append(result)
                processed_count += 1
                
                if result.get('success', True):
                    successful_count += 1
                else:
                    failed_count += 1
                
                # Call progress callback if provided
                if progress_callback:
                    progress = processed_count / total_properties
                    await progress_callback(progress, processed_count, total_properties)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        summary = {
            'batch_id': batch_id,
            'total_properties': total_properties,
            'processed_count': processed_count,
            'successful_count': successful_count,
            'failed_count': failed_count,
            'success_rate': successful_count / max(processed_count, 1),
            'total_processing_time': total_time,
            'properties_per_second': processed_count / max(total_time, 1),
            'completed_at': datetime.now().isoformat(),
            'results': results
        }
        
        logger.info(f"Batch assessment completed: {successful_count}/{total_properties} "
                   f"successful in {total_time:.1f}s "
                   f"({processed_count/total_time:.1f} properties/sec)")
        
        return summary

# Factory functions for different use cases

def create_fast_pipeline() -> EnergyAssessmentPipeline:
    """Create pipeline optimized for speed over accuracy"""
    pipeline = EnergyAssessmentPipeline()
    pipeline.config.update({
        'enable_ml_predictions': True,
        'enable_recommendations': False,  # Skip for speed
        'enable_market_comparison': False,
        'parallel_processing': True,
        'cache_intermediate_results': False  # Reduce memory usage
    })
    return pipeline

def create_comprehensive_pipeline() -> EnergyAssessmentPipeline:
    """Create pipeline optimized for comprehensive analysis"""
    pipeline = EnergyAssessmentPipeline()
    pipeline.config.update({
        'enable_ml_predictions': True,
        'enable_recommendations': True,
        'enable_market_comparison': True,
        'parallel_processing': True,
        'cache_intermediate_results': True
    })
    return pipeline

def create_realtime_service() -> RealTimeAssessmentService:
    """Create optimized real-time assessment service"""
    return RealTimeAssessmentService()

def create_batch_processor() -> BatchAssessmentProcessor:
    """Create high-performance batch processor"""
    return BatchAssessmentProcessor()