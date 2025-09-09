"""
🏗️ Energy Assessment Property Pipeline Integration

This module integrates the energy assessment capabilities with the existing
property validation and processing pipeline, using the secure infrastructure
for all data operations.

Key Features:
✅ Seamless integration with existing PropertyValidator
✅ Secure data operations using SecureDatabase and SecureFileManager
✅ Energy assessment pipeline with validation and audit
✅ ROI calculations for property investment decisions
✅ Comprehensive error handling and logging
✅ Performance monitoring and metrics collection

Integration Flow:
1. Property data validated through secure PropertyValidator
2. Energy assessment performed using EnergyAssessmentEngine
3. Results stored securely in database with audit trail
4. Investment recommendations generated with ROI analysis
5. Reports generated using secure file operations

Usage:
    from integrations.energy_property_integration import EnergyPropertyPipeline
    
    pipeline = EnergyPropertyPipeline()
    result = await pipeline.process_property_with_energy_analysis(property_data)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import time
import traceback

# Import secure infrastructure
from security.secure_database import SecureDatabase, SecurityDatabaseException
from security.secure_file_operations import SecureFileManager, SecureFileException
from security.input_validator import InputValidator, ValidationException

# Import existing components
from validators.property_validator import PropertyValidator, ValidationResult
from energy.energy_assessment import EnergyAssessmentEngine, EnergyAssessment, EnergyClass

# Import monitoring (if available)
try:
    from monitoring.metrics_collector import MetricsCollector
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class EnergyPropertyResult:
    """Complete result of property + energy analysis"""
    property_id: str
    property_validation: ValidationResult
    energy_assessment: Optional[EnergyAssessment]
    investment_metrics: Dict[str, Any]
    processing_time: float
    timestamp: datetime
    success: bool
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        
        # Convert datetime and ValidationResult to dict
        result['timestamp'] = self.timestamp.isoformat()
        result['property_validation'] = self.property_validation.to_dict()
        
        # Convert EnergyAssessment to dict if present
        if self.energy_assessment:
            result['energy_assessment'] = {
                'property_id': self.energy_assessment.property_id,
                'current_energy_class': self.energy_assessment.current_energy_class.value,
                'potential_energy_class': self.energy_assessment.potential_energy_class.value,
                'total_upgrade_cost': self.energy_assessment.total_upgrade_cost,
                'annual_savings': self.energy_assessment.annual_savings,
                'roi_percentage': self.energy_assessment.roi_percentage,
                'payback_years': self.energy_assessment.payback_years,
                'upgrade_recommendations': [
                    {
                        'upgrade_type': rec.upgrade_type.value,
                        'cost': rec.cost,
                        'annual_savings': rec.annual_savings,
                        'roi': rec.roi,
                        'priority': rec.priority.value,
                        'implementation_time': rec.implementation_time,
                        'description': rec.description
                    } for rec in self.energy_assessment.upgrade_recommendations
                ],
                'confidence_score': self.energy_assessment.confidence_score,
                'assessment_date': self.energy_assessment.assessment_date.isoformat()
            }
        
        return result

class EnergyPropertyPipeline:
    """
    Integrated pipeline for property validation and energy assessment
    
    This pipeline processes properties through multiple stages:
    1. Secure input validation and sanitization
    2. Property authenticity validation
    3. Energy efficiency assessment
    4. Investment ROI calculations
    5. Secure data storage with audit trails
    6. Report generation using secure file operations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the integrated energy property pipeline
        
        Args:
            config: Configuration dictionary for pipeline settings
        """
        self.config = config or self._get_default_config()
        
        # Initialize secure components
        self.input_validator = InputValidator()
        self.property_validator = PropertyValidator()
        self.energy_engine = EnergyAssessmentEngine()
        self.secure_db = SecureDatabase()
        self.secure_files = SecureFileManager()
        
        # Initialize monitoring if available
        if MONITORING_AVAILABLE:
            self.metrics = MetricsCollector()
        else:
            self.metrics = None
        
        # Performance tracking
        self.processing_stats = {
            'total_processed': 0,
            'successful_assessments': 0,
            'failed_validations': 0,
            'energy_assessments_completed': 0,
            'average_processing_time': 0.0,
            'start_time': time.time()
        }
        
        logger.info("🏗️ EnergyPropertyPipeline initialized with secure infrastructure")
        logger.info(f"✅ Security features: input validation, secure database, secure file operations")
        logger.info(f"✅ Energy assessment: {len(EnergyClass)} energy classes supported")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default pipeline configuration"""
        return {
            'validation': {
                'enable_multi_factor': True,
                'min_validation_score': 70,
                'enable_energy_assessment': True,
                'energy_assessment_threshold': 50  # Only assess properties with validation score > 50
            },
            'energy_assessment': {
                'enable_upgrade_recommendations': True,
                'max_upgrade_budget': 50000,  # €50,000 max upgrade budget
                'min_roi_threshold': 0.12,    # 12% minimum ROI
                'assessment_confidence_threshold': 0.6
            },
            'storage': {
                'save_property_data': True,
                'save_energy_assessments': True,
                'save_investment_reports': True,
                'audit_all_operations': True
            },
            'performance': {
                'batch_size': 100,
                'max_concurrent': 10,
                'timeout_seconds': 300
            }
        }
    
    async def process_property_with_energy_analysis(
        self,
        property_data: Dict[str, Any],
        user_context: str = "system"
    ) -> EnergyPropertyResult:
        """
        Process a single property through the complete pipeline
        
        Args:
            property_data: Raw property data dictionary
            user_context: User context for security audit
            
        Returns:
            EnergyPropertyResult with complete analysis
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Stage 1: Secure Input Validation and Sanitization
            logger.debug(f"Stage 1: Input validation for property {property_data.get('id', 'unknown')}")
            
            validated_data = await self._validate_and_sanitize_input(property_data, user_context)
            
            if not validated_data:
                return EnergyPropertyResult(
                    property_id=property_data.get('id', 'unknown'),
                    property_validation=None,
                    energy_assessment=None,
                    investment_metrics={},
                    processing_time=time.time() - start_time,
                    timestamp=datetime.now(),
                    success=False,
                    errors=['Input validation failed'],
                    warnings=[]
                )
            
            # Stage 2: Property Authenticity Validation
            logger.debug(f"Stage 2: Property validation for {validated_data.get('id')}")
            
            property_validation = self.property_validator.validate_property(validated_data)
            
            # Check if property meets minimum validation threshold
            if property_validation.score.total_score < self.config['validation']['energy_assessment_threshold']:
                warnings.append(f"Property validation score too low for energy assessment: {property_validation.score.total_score}")
                
                # Still store the property validation result
                if self.config['storage']['save_property_data']:
                    await self._store_property_data(validated_data, property_validation, user_context)
                
                return EnergyPropertyResult(
                    property_id=validated_data['id'],
                    property_validation=property_validation,
                    energy_assessment=None,
                    investment_metrics={},
                    processing_time=time.time() - start_time,
                    timestamp=datetime.now(),
                    success=False,
                    errors=property_validation.errors,
                    warnings=warnings + property_validation.warnings
                )
            
            # Stage 3: Energy Efficiency Assessment
            energy_assessment = None
            if (self.config['validation']['enable_energy_assessment'] and 
                property_validation.is_valid):
                
                logger.debug(f"Stage 3: Energy assessment for {validated_data.get('id')}")
                
                try:
                    energy_assessment = self.energy_engine.assess_property(validated_data)
                    
                    # Verify assessment quality
                    if energy_assessment.confidence_score < self.config['energy_assessment']['assessment_confidence_threshold']:
                        warnings.append(f"Low confidence energy assessment: {energy_assessment.confidence_score:.2f}")
                    
                except Exception as e:
                    logger.warning(f"Energy assessment failed for {validated_data.get('id')}: {str(e)}")
                    errors.append(f"Energy assessment error: {str(e)}")
            
            # Stage 4: Investment Metrics Calculation
            logger.debug(f"Stage 4: Investment metrics for {validated_data.get('id')}")
            
            investment_metrics = self._calculate_investment_metrics(
                validated_data, 
                property_validation, 
                energy_assessment
            )
            
            # Stage 5: Secure Data Storage
            if self.config['storage']['save_property_data']:
                await self._store_property_data(validated_data, property_validation, user_context)
            
            if energy_assessment and self.config['storage']['save_energy_assessments']:
                await self._store_energy_assessment(energy_assessment, user_context)
            
            # Update performance statistics
            self._update_performance_stats(time.time() - start_time, len(errors) == 0, energy_assessment is not None)
            
            # Record metrics if monitoring available
            if self.metrics:
                self.metrics.record_validation({
                    'property_id': validated_data['id'],
                    'validation_score': property_validation.score.total_score,
                    'energy_assessment_completed': energy_assessment is not None,
                    'processing_time': time.time() - start_time,
                    'success': len(errors) == 0
                })
            
            return EnergyPropertyResult(
                property_id=validated_data['id'],
                property_validation=property_validation,
                energy_assessment=energy_assessment,
                investment_metrics=investment_metrics,
                processing_time=time.time() - start_time,
                timestamp=datetime.now(),
                success=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Pipeline error for property {property_data.get('id', 'unknown')}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            return EnergyPropertyResult(
                property_id=property_data.get('id', 'unknown'),
                property_validation=None,
                energy_assessment=None,
                investment_metrics={},
                processing_time=time.time() - start_time,
                timestamp=datetime.now(),
                success=False,
                errors=[f"Pipeline error: {str(e)}"],
                warnings=warnings
            )
    
    async def _validate_and_sanitize_input(
        self, 
        property_data: Dict[str, Any], 
        user_context: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate and sanitize all input data using secure validator
        
        Args:
            property_data: Raw property data
            user_context: User context for audit
            
        Returns:
            Sanitized property data or None if validation fails
        """
        try:
            sanitized_data = {}
            
            # Validate and sanitize each field
            field_validators = {
                'id': lambda x: self.input_validator.validate_property_id(x),
                'url': lambda x: self.input_validator.validate_url(x),
                'price': lambda x: self.input_validator.validate_numeric(x, min_val=0),
                'size': lambda x: self.input_validator.validate_numeric(x, min_val=0),
                'rooms': lambda x: self.input_validator.validate_numeric(x, min_val=0, max_val=20),
                'floor': lambda x: self.input_validator.validate_numeric(x, min_val=-5, max_val=50),
                'year_built': lambda x: self.input_validator.validate_numeric(x, min_val=1800, max_val=datetime.now().year),
                'location': lambda x: self.input_validator.sanitize_text(x),
                'description': lambda x: self.input_validator.sanitize_html(x),
                'energy_class': lambda x: self.input_validator.validate_energy_data({'energy_class': x})['energy_class'],
                'property_type': lambda x: self.input_validator.sanitize_text(x)
            }
            
            for field, value in property_data.items():
                if field in field_validators and value is not None:
                    try:
                        sanitized_data[field] = field_validators[field](value)
                    except ValidationException as e:
                        logger.warning(f"Field validation failed for {field}: {str(e)}")
                        # Skip invalid fields rather than failing entire validation
                        continue
                elif value is not None:
                    # For fields without specific validators, apply basic sanitization
                    if isinstance(value, str):
                        sanitized_data[field] = self.input_validator.sanitize_text(value)
                    else:
                        sanitized_data[field] = value
            
            # Ensure required fields are present
            required_fields = ['id', 'price']
            for field in required_fields:
                if field not in sanitized_data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            logger.debug(f"✅ Input validation successful for property {sanitized_data['id']}")
            return sanitized_data
            
        except Exception as e:
            logger.error(f"Input validation error: {str(e)}")
            return None
    
    def _calculate_investment_metrics(
        self,
        property_data: Dict[str, Any],
        validation_result: ValidationResult,
        energy_assessment: Optional[EnergyAssessment]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive investment metrics
        
        Args:
            property_data: Validated property data
            validation_result: Property validation result
            energy_assessment: Energy assessment result (optional)
            
        Returns:
            Dictionary of investment metrics
        """
        metrics = {
            'base_property_score': validation_result.score.total_score,
            'investment_grade': self._calculate_investment_grade(validation_result.score.total_score),
            'market_position': 'unknown',
            'risk_assessment': 'medium'
        }
        
        # Add energy-related investment metrics
        if energy_assessment:
            metrics.update({
                'energy_upgrade_potential': True,
                'energy_roi': energy_assessment.roi_percentage,
                'energy_payback_years': energy_assessment.payback_years,
                'annual_energy_savings': energy_assessment.annual_savings,
                'total_upgrade_cost': energy_assessment.total_upgrade_cost,
                'post_upgrade_value_increase': self._estimate_value_increase(energy_assessment),
                'energy_investment_grade': self._calculate_energy_investment_grade(energy_assessment),
                'recommended_upgrade_budget': min(
                    energy_assessment.total_upgrade_cost,
                    self.config['energy_assessment']['max_upgrade_budget']
                )
            })
        else:
            metrics.update({
                'energy_upgrade_potential': False,
                'energy_roi': 0,
                'energy_payback_years': 0,
                'annual_energy_savings': 0,
                'total_upgrade_cost': 0,
                'energy_investment_grade': 'N/A'
            })
        
        # Calculate combined investment score
        base_score = validation_result.score.total_score
        energy_bonus = 0
        
        if energy_assessment and energy_assessment.roi_percentage > self.config['energy_assessment']['min_roi_threshold']:
            energy_bonus = min(20, energy_assessment.roi_percentage * 100)  # Max 20 point bonus
        
        metrics['combined_investment_score'] = min(100, base_score + energy_bonus)
        metrics['investment_recommendation'] = self._generate_investment_recommendation(metrics)
        
        return metrics
    
    def _calculate_investment_grade(self, score: float) -> str:
        """Calculate investment grade based on validation score"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        else:
            return 'D'
    
    def _calculate_energy_investment_grade(self, energy_assessment: EnergyAssessment) -> str:
        """Calculate energy investment grade based on ROI and payback"""
        roi = energy_assessment.roi_percentage
        payback = energy_assessment.payback_years
        
        if roi >= 0.20 and payback <= 5:
            return 'A+'
        elif roi >= 0.15 and payback <= 7:
            return 'A'
        elif roi >= 0.12 and payback <= 10:
            return 'B+'
        elif roi >= 0.08 and payback <= 12:
            return 'B'
        elif roi >= 0.05 and payback <= 15:
            return 'C'
        else:
            return 'D'
    
    def _estimate_value_increase(self, energy_assessment: EnergyAssessment) -> float:
        """Estimate property value increase from energy upgrades"""
        # Conservative estimate: 1-3% property value increase per energy class improvement
        current_class = energy_assessment.current_energy_class.numeric_value
        potential_class = energy_assessment.potential_energy_class.numeric_value
        class_improvement = current_class - potential_class  # Lower is better
        
        if class_improvement > 0:
            # Estimate 2% value increase per class improvement
            return class_improvement * 0.02
        else:
            return 0.0
    
    def _generate_investment_recommendation(self, metrics: Dict[str, Any]) -> str:
        """Generate human-readable investment recommendation"""
        combined_score = metrics['combined_investment_score']
        energy_roi = metrics.get('energy_roi', 0)
        
        if combined_score >= 85 and energy_roi >= 0.15:
            return "STRONG BUY - Excellent property with high-ROI energy upgrade potential"
        elif combined_score >= 75 and energy_roi >= 0.12:
            return "BUY - Good property with solid energy upgrade opportunities"
        elif combined_score >= 65:
            return "CONSIDER - Decent property, evaluate energy upgrades carefully"
        elif combined_score >= 50:
            return "HOLD - Below-average property, significant energy upgrades may improve value"
        else:
            return "AVOID - Low-quality property with poor investment potential"
    
    async def _store_property_data(
        self,
        property_data: Dict[str, Any],
        validation_result: ValidationResult,
        user_context: str
    ):
        """Store property data using secure database operations"""
        try:
            # Prepare property data for storage
            storage_data = property_data.copy()
            storage_data.update({
                'validation_score': validation_result.score.total_score,
                'validation_errors': json.dumps(validation_result.errors),
                'validation_warnings': json.dumps(validation_result.warnings),
                'validation_timestamp': validation_result.timestamp.isoformat(),
                'last_updated': datetime.now().isoformat()
            })
            
            # Use secure database operations
            with SecureDatabase() as db:
                # Check if property already exists
                existing = db.select_properties(
                    filters={'id': property_data['id']}, 
                    limit=1,
                    user_context=user_context
                )
                
                if existing:
                    # Update existing property
                    db.update_property(
                        property_data['id'],
                        storage_data,
                        user_context=user_context
                    )
                    logger.debug(f"✅ Property updated: {property_data['id']}")
                else:
                    # Insert new property
                    db.insert_property(
                        storage_data,
                        user_context=user_context
                    )
                    logger.debug(f"✅ Property inserted: {property_data['id']}")
                    
        except SecurityDatabaseException as e:
            logger.error(f"Secure database error storing property {property_data.get('id')}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error storing property data: {str(e)}")
            raise
    
    async def _store_energy_assessment(
        self,
        energy_assessment: EnergyAssessment,
        user_context: str
    ):
        """Store energy assessment using secure database operations"""
        try:
            # Prepare energy assessment data
            assessment_data = {
                'current_energy_class': energy_assessment.current_energy_class.value,
                'potential_energy_class': energy_assessment.potential_energy_class.value,
                'total_upgrade_cost': energy_assessment.total_upgrade_cost,
                'annual_savings': energy_assessment.annual_savings,
                'roi_percentage': energy_assessment.roi_percentage,
                'payback_years': energy_assessment.payback_years,
                'confidence_score': energy_assessment.confidence_score,
                'upgrade_recommendations': [
                    {
                        'upgrade_type': rec.upgrade_type.value,
                        'cost': rec.cost,
                        'annual_savings': rec.annual_savings,
                        'roi': rec.roi,
                        'priority': rec.priority.value,
                        'implementation_time': rec.implementation_time,
                        'description': rec.description
                    } for rec in energy_assessment.upgrade_recommendations
                ]
            }
            
            # Use secure database operations
            with SecureDatabase() as db:
                assessment_id = db.insert_energy_assessment(
                    energy_assessment.property_id,
                    assessment_data,
                    user_context=user_context
                )
                
                logger.debug(f"✅ Energy assessment stored: {assessment_id}")
                
        except SecurityDatabaseException as e:
            logger.error(f"Secure database error storing energy assessment: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error storing energy assessment: {str(e)}")
            raise
    
    def _update_performance_stats(self, processing_time: float, success: bool, energy_completed: bool):
        """Update pipeline performance statistics"""
        self.processing_stats['total_processed'] += 1
        
        if success:
            self.processing_stats['successful_assessments'] += 1
        else:
            self.processing_stats['failed_validations'] += 1
        
        if energy_completed:
            self.processing_stats['energy_assessments_completed'] += 1
        
        # Update average processing time
        total_time = (self.processing_stats['average_processing_time'] * 
                     (self.processing_stats['total_processed'] - 1) + processing_time)
        self.processing_stats['average_processing_time'] = total_time / self.processing_stats['total_processed']
    
    async def process_batch(
        self,
        properties: List[Dict[str, Any]],
        user_context: str = "system"
    ) -> List[EnergyPropertyResult]:
        """
        Process multiple properties in batches with concurrency control
        
        Args:
            properties: List of property data dictionaries
            user_context: User context for security audit
            
        Returns:
            List of EnergyPropertyResult objects
        """
        batch_size = self.config['performance']['batch_size']
        max_concurrent = self.config['performance']['max_concurrent']
        
        results = []
        
        # Process in batches
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} properties")
            
            # Create semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_with_semaphore(prop_data):
                async with semaphore:
                    return await self.process_property_with_energy_analysis(prop_data, user_context)
            
            # Process batch concurrently
            batch_results = await asyncio.gather(
                *[process_with_semaphore(prop) for prop in batch],
                return_exceptions=True
            )
            
            # Handle any exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error for property {batch[j].get('id', 'unknown')}: {result}")
                    # Create error result
                    error_result = EnergyPropertyResult(
                        property_id=batch[j].get('id', 'unknown'),
                        property_validation=None,
                        energy_assessment=None,
                        investment_metrics={},
                        processing_time=0.0,
                        timestamp=datetime.now(),
                        success=False,
                        errors=[f"Batch processing error: {str(result)}"],
                        warnings=[]
                    )
                    results.append(error_result)
                else:
                    results.append(result)
        
        logger.info(f"✅ Batch processing complete: {len(results)} properties processed")
        return results
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get pipeline performance statistics"""
        uptime = time.time() - self.processing_stats['start_time']
        
        stats = self.processing_stats.copy()
        stats.update({
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'properties_per_hour': (stats['total_processed'] / uptime) * 3600 if uptime > 0 else 0,
            'success_rate': (stats['successful_assessments'] / stats['total_processed']) * 100 if stats['total_processed'] > 0 else 0,
            'energy_completion_rate': (stats['energy_assessments_completed'] / stats['total_processed']) * 100 if stats['total_processed'] > 0 else 0
        })
        
        return stats
    
    async def generate_investment_report(
        self,
        results: List[EnergyPropertyResult],
        report_path: str = "reports/energy_investment_analysis.json",
        user_context: str = "system"
    ) -> str:
        """
        Generate comprehensive investment report using secure file operations
        
        Args:
            results: List of property analysis results
            report_path: Path for report file
            user_context: User context for security audit
            
        Returns:
            Path to generated report
        """
        try:
            # Compile report data
            report_data = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'generated_by': user_context,
                    'total_properties_analyzed': len(results),
                    'analysis_version': '2.0.0',
                    'pipeline_statistics': self.get_performance_statistics()
                },
                'executive_summary': self._generate_executive_summary(results),
                'property_analyses': [result.to_dict() for result in results],
                'investment_recommendations': self._generate_investment_recommendations(results),
                'energy_upgrade_summary': self._generate_energy_upgrade_summary(results)
            }
            
            # Convert to JSON
            report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
            
            # Use secure file operations
            with SecureFileManager() as fm:
                bytes_written = fm.write_file(
                    report_path,
                    report_json,
                    user_context=user_context,
                    encoding='utf-8'
                )
                
                logger.info(f"✅ Investment report generated: {report_path} ({bytes_written} bytes)")
                return report_path
                
        except SecureFileException as e:
            logger.error(f"Secure file error generating report: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating investment report: {str(e)}")
            raise
    
    def _generate_executive_summary(self, results: List[EnergyPropertyResult]) -> Dict[str, Any]:
        """Generate executive summary from analysis results"""
        successful_results = [r for r in results if r.success]
        energy_results = [r for r in successful_results if r.energy_assessment is not None]
        
        if not successful_results:
            return {'message': 'No successful property analyses to summarize'}
        
        # Calculate summary statistics
        avg_validation_score = sum(r.property_validation.score.total_score for r in successful_results) / len(successful_results)
        avg_energy_roi = sum(r.energy_assessment.roi_percentage for r in energy_results) / len(energy_results) if energy_results else 0
        
        total_investment_potential = sum(
            r.investment_metrics.get('total_upgrade_cost', 0) 
            for r in successful_results
        )
        
        return {
            'total_properties': len(results),
            'successful_analyses': len(successful_results),
            'energy_assessments_completed': len(energy_results),
            'average_property_score': round(avg_validation_score, 1),
            'average_energy_roi': round(avg_energy_roi * 100, 1),
            'total_investment_potential': total_investment_potential,
            'recommended_properties': len([r for r in successful_results if 'BUY' in r.investment_metrics.get('investment_recommendation', '')]),
            'high_energy_potential': len([r for r in energy_results if r.energy_assessment.roi_percentage >= 0.15])
        }
    
    def _generate_investment_recommendations(self, results: List[EnergyPropertyResult]) -> List[Dict[str, Any]]:
        """Generate top investment recommendations"""
        successful_results = [r for r in results if r.success and r.property_validation]
        
        # Sort by combined investment score
        sorted_results = sorted(
            successful_results,
            key=lambda r: r.investment_metrics.get('combined_investment_score', 0),
            reverse=True
        )
        
        # Return top 10 recommendations
        recommendations = []
        for result in sorted_results[:10]:
            recommendations.append({
                'property_id': result.property_id,
                'investment_score': result.investment_metrics.get('combined_investment_score', 0),
                'investment_grade': result.investment_metrics.get('investment_grade', 'N/A'),
                'recommendation': result.investment_metrics.get('investment_recommendation', 'N/A'),
                'energy_roi': result.investment_metrics.get('energy_roi', 0),
                'total_upgrade_cost': result.investment_metrics.get('total_upgrade_cost', 0),
                'annual_savings': result.investment_metrics.get('annual_energy_savings', 0)
            })
        
        return recommendations
    
    def _generate_energy_upgrade_summary(self, results: List[EnergyPropertyResult]) -> Dict[str, Any]:
        """Generate energy upgrade portfolio summary"""
        energy_results = [r for r in results if r.success and r.energy_assessment]
        
        if not energy_results:
            return {'message': 'No energy assessments available for summary'}
        
        # Aggregate energy statistics
        total_upgrade_cost = sum(r.energy_assessment.total_upgrade_cost for r in energy_results)
        total_annual_savings = sum(r.energy_assessment.annual_savings for r in energy_results)
        
        # Calculate energy class distribution
        current_classes = {}
        potential_classes = {}
        
        for result in energy_results:
            current_class = result.energy_assessment.current_energy_class.value
            potential_class = result.energy_assessment.potential_energy_class.value
            
            current_classes[current_class] = current_classes.get(current_class, 0) + 1
            potential_classes[potential_class] = potential_classes.get(potential_class, 0) + 1
        
        return {
            'total_properties_assessed': len(energy_results),
            'total_upgrade_investment': total_upgrade_cost,
            'total_annual_savings': total_annual_savings,
            'portfolio_roi': (total_annual_savings / total_upgrade_cost) * 100 if total_upgrade_cost > 0 else 0,
            'current_energy_distribution': current_classes,
            'potential_energy_distribution': potential_classes,
            'high_roi_properties': len([r for r in energy_results if r.energy_assessment.roi_percentage >= 0.15]),
            'recommended_total_investment': min(total_upgrade_cost, len(energy_results) * self.config['energy_assessment']['max_upgrade_budget'])
        }

# Convenience functions for easy integration

async def analyze_property_with_energy(property_data: Dict[str, Any], user_context: str = "system") -> EnergyPropertyResult:
    """Convenience function for single property analysis"""
    pipeline = EnergyPropertyPipeline()
    return await pipeline.process_property_with_energy_analysis(property_data, user_context)

async def analyze_property_batch(properties: List[Dict[str, Any]], user_context: str = "system") -> List[EnergyPropertyResult]:
    """Convenience function for batch property analysis"""
    pipeline = EnergyPropertyPipeline()
    return await pipeline.process_batch(properties, user_context)

if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    
    async def test_pipeline():
        """Test the energy property pipeline"""
        # Sample property data
        test_property = {
            'id': 'TEST-001',
            'url': 'https://spitogatos.gr/test-property',
            'price': 250000,
            'size': 85,
            'rooms': 3,
            'floor': 2,
            'year_built': 1995,
            'location': 'Koukaki',
            'description': 'Beautiful apartment in historic neighborhood',
            'energy_class': 'D',
            'property_type': 'apartment'
        }
        
        pipeline = EnergyPropertyPipeline()
        result = await pipeline.process_property_with_energy_analysis(test_property, "test_user")
        
        print("🧪 Pipeline Test Results:")
        print(f"   Success: {result.success}")
        print(f"   Property Score: {result.property_validation.score.total_score if result.property_validation else 'N/A'}")
        print(f"   Energy Assessment: {'✅' if result.energy_assessment else '❌'}")
        print(f"   Processing Time: {result.processing_time:.2f}s")
        print(f"   Investment Grade: {result.investment_metrics.get('investment_grade', 'N/A')}")
        
        if result.energy_assessment:
            print(f"   Energy ROI: {result.energy_assessment.roi_percentage:.1%}")
            print(f"   Payback: {result.energy_assessment.payback_years:.1f} years")
        
        return result
    
    # Run test if script is executed directly
    asyncio.run(test_pipeline())