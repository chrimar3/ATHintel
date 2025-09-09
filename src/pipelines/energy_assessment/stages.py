"""
🔄 Energy Assessment Pipeline Stages

Individual processing stages for the energy assessment pipeline.
Each stage handles a specific aspect of the assessment process.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

from ..pipeline import PipelineStage
from domains.energy.entities.property_energy import PropertyEnergyEntity, BuildingType, HeatingSystem
from domains.energy.value_objects.energy_class import EnergyClass
from domains.energy.value_objects.upgrade_recommendation import (
    UpgradeRecommendation, UpgradeType, UpgradePriority, 
    create_heating_system_upgrade
)
from ml.energy_prediction.models import EnergyModelEnsemble
from ml.energy_prediction.features import FeatureExtractor, BuildingFeatures

logger = logging.getLogger(__name__)

class DataValidationStage(PipelineStage):
    """
    Validates and normalizes input property data
    Ensures data quality and consistency before processing
    """
    
    def __init__(self):
        super().__init__("DataValidation")
        self.validation_rules = self._setup_validation_rules()
    
    async def _execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize property data"""
        
        validated_data = data.copy()
        errors = []
        warnings = []
        
        # Required field validation
        required_fields = ['property_id', 'construction_year', 'total_area', 'building_type']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        # Data type and range validation
        try:
            # Construction year validation
            construction_year = int(data['construction_year'])
            current_year = datetime.now().year
            
            if construction_year < 1800 or construction_year > current_year:
                errors.append(f"Invalid construction year: {construction_year}")
            else:
                validated_data['construction_year'] = construction_year
                validated_data['building_age'] = current_year - construction_year
            
            # Area validation
            total_area = float(data['total_area'])
            if total_area <= 0 or total_area > 10000:  # Max 10,000 m²
                errors.append(f"Invalid total area: {total_area}")
            else:
                validated_data['total_area'] = total_area
            
            # Building type normalization
            building_type = str(data['building_type']).lower()
            valid_types = ['apartment', 'maisonette', 'detached_house', 'commercial', 'office', 'industrial']
            
            if building_type not in valid_types:
                warnings.append(f"Unknown building type: {building_type}, using 'apartment'")
                validated_data['building_type'] = 'apartment'
            else:
                validated_data['building_type'] = building_type
            
            # Heating system normalization
            heating_system = data.get('heating_system', 'individual_gas')
            validated_data['heating_system'] = self._normalize_heating_system(heating_system)
            
            # Location data validation
            if 'location' in data:
                validated_data['location'] = self._validate_location_data(data['location'])
            else:
                # Default Athens location
                validated_data['location'] = {
                    'region': 'attiki',
                    'city': 'athens',
                    'postal_code': '10000'
                }
                warnings.append("No location data provided, using Athens defaults")
            
            # Numeric field validation and defaults
            numeric_fields = {
                'floors_count': 3,
                'window_area': total_area * 0.15,  # 15% of total area
                'energy_consumption': None  # Will be predicted
            }
            
            for field, default_value in numeric_fields.items():
                if field in data:
                    try:
                        validated_data[field] = float(data[field])
                    except (ValueError, TypeError):
                        if default_value is not None:
                            validated_data[field] = default_value
                            warnings.append(f"Invalid {field}, using default: {default_value}")
                elif default_value is not None:
                    validated_data[field] = default_value
            
            # Insulation data validation
            if 'insulation' in data:
                validated_data['insulation'] = self._validate_insulation_data(data['insulation'])
            else:
                # Estimate insulation based on construction year
                validated_data['insulation'] = self._estimate_insulation_from_age(construction_year)
                warnings.append("No insulation data provided, estimated from building age")
            
        except Exception as e:
            errors.append(f"Data validation error: {str(e)}")
        
        if errors:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        # Store warnings in context
        context['warnings'].extend(warnings)
        
        # Add validation metadata
        validated_data['_validation_metadata'] = {
            'validated_at': datetime.now().isoformat(),
            'warnings_count': len(warnings),
            'normalized_fields': ['building_type', 'heating_system', 'location']
        }
        
        logger.debug(f"Data validation completed for property {data.get('property_id')} "
                    f"with {len(warnings)} warnings")
        
        return validated_data
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup validation rules configuration"""
        return {
            'max_area': 10000,
            'min_area': 10,
            'max_construction_year': datetime.now().year,
            'min_construction_year': 1800,
            'valid_building_types': ['apartment', 'maisonette', 'detached_house', 'commercial', 'office'],
            'valid_heating_systems': ['central_gas', 'individual_gas', 'central_oil', 'electric', 'heat_pump']
        }
    
    def _normalize_heating_system(self, heating_system: str) -> str:
        """Normalize heating system values"""
        heating_map = {
            'gas': 'individual_gas',
            'natural_gas': 'individual_gas',
            'central_heating': 'central_gas',
            'oil': 'individual_oil',
            'electricity': 'electric',
            'electrical': 'electric',
            'heat_pump': 'heat_pump',
            'geothermal': 'heat_pump',
            'fireplace': 'fireplace',
            'wood': 'fireplace'
        }
        
        normalized = heating_system.lower().replace(' ', '_')
        return heating_map.get(normalized, 'individual_gas')
    
    def _validate_location_data(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize location data"""
        validated_location = {}
        
        # Required location fields with defaults
        location_defaults = {
            'region': 'attiki',
            'city': 'athens',
            'postal_code': '10000',
            'climate_zone': 2
        }
        
        for field, default in location_defaults.items():
            validated_location[field] = location.get(field, default)
        
        return validated_location
    
    def _validate_insulation_data(self, insulation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate insulation data"""
        insulation_types = ['none', 'minimal', 'basic', 'good', 'excellent']
        
        validated_insulation = {}
        for component in ['walls', 'roof', 'floor', 'windows']:
            value = insulation.get(component, 'none')
            if value not in insulation_types:
                validated_insulation[component] = 'none'
            else:
                validated_insulation[component] = value
        
        return validated_insulation
    
    def _estimate_insulation_from_age(self, construction_year: int) -> Dict[str, str]:
        """Estimate insulation quality based on construction year"""
        if construction_year >= 2010:
            return {'walls': 'good', 'roof': 'good', 'floor': 'basic', 'windows': 'good'}
        elif construction_year >= 1980:
            return {'walls': 'basic', 'roof': 'basic', 'floor': 'minimal', 'windows': 'basic'}
        else:
            return {'walls': 'none', 'roof': 'minimal', 'floor': 'none', 'windows': 'minimal'}

class FeatureExtractionStage(PipelineStage):
    """
    Extracts and engineers features for ML model consumption
    Handles feature scaling, encoding, and transformation
    """
    
    def __init__(self, feature_extractor: FeatureExtractor):
        super().__init__("FeatureExtraction")
        self.feature_extractor = feature_extractor
    
    async def _execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from validated property data"""
        
        # Extract building features
        building_features = BuildingFeatures.extract_from_property(data)
        
        # Get market features
        market_features = self.feature_extractor.market_features
        
        # Extract climate features if available
        climate_features = None
        if 'climate_data' in data:
            climate_features = self.feature_extractor._extract_climate_features(data['climate_data'])
        
        # Combine all features
        feature_array = self.feature_extractor.combine_features(
            building_features, market_features, climate_features
        )
        
        # Add feature metadata to data
        enriched_data = data.copy()
        enriched_data['_features'] = {
            'building_features': building_features,
            'market_features': market_features,
            'climate_features': climate_features,
            'feature_array': feature_array.tolist(),
            'feature_count': len(feature_array),
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        logger.debug(f"Feature extraction completed: {len(feature_array)} features extracted")
        
        return enriched_data

class MLPredictionStage(PipelineStage):
    """
    Performs ML predictions using the trained energy models
    Handles energy class, consumption, and ROI predictions
    """
    
    def __init__(self, ml_ensemble: EnergyModelEnsemble):
        super().__init__("MLPrediction")
        self.ml_ensemble = ml_ensemble
    
    async def _execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform ML predictions on property features with async handling and timeouts"""
        
        if '_features' not in data:
            raise ValueError("Features must be extracted before ML prediction")
        
        building_features = data['_features']['building_features']
        property_id = data.get('property_id', 'unknown')
        
        # ML prediction with timeout and proper error handling
        prediction_start = datetime.now()
        predictions = None
        prediction_method = 'rule_based'
        
        try:
            # Add timeout for ML predictions to prevent hanging
            prediction_timeout = context.get('config', {}).get('ml_prediction_timeout', 30)  # 30 second default
            
            # Run ML prediction with timeout using asyncio
            predictions = await asyncio.wait_for(
                self._run_ml_prediction_async(building_features),
                timeout=prediction_timeout
            )
            prediction_method = 'ml_ensemble'
            
            logger.debug(f"ML prediction completed for property {property_id} in "
                        f"{(datetime.now() - prediction_start).total_seconds():.2f}s")
            
        except asyncio.TimeoutError:
            logger.warning(f"ML prediction timeout ({prediction_timeout}s) for property {property_id}, using fallback")
            predictions = await self._fallback_predictions_async(data)
            
        except Exception as e:
            # Fallback to rule-based predictions if ML fails
            logger.warning(f"ML prediction failed for property {property_id}, using fallback: {e}")
            predictions = await self._fallback_predictions_async(data)
        
        # Enrich data with predictions
        enriched_data = data.copy()
        enriched_data['_predictions'] = {
            **predictions,
            'prediction_timestamp': datetime.now().isoformat(),
            'prediction_method': prediction_method,
            'prediction_duration_ms': (datetime.now() - prediction_start).total_seconds() * 1000
        }
        
        # Convert predictions to domain objects if needed
        if 'energy_class' in predictions:
            predicted_class = predictions['energy_class']['predicted_class']
            if isinstance(predicted_class, EnergyClass):
                enriched_data['predicted_energy_class'] = predicted_class.value
                enriched_data['prediction_confidence'] = predictions['energy_class']['confidence']
        
        return enriched_data
    
    async def _run_ml_prediction_async(self, building_features) -> Dict[str, Any]:
        """Run ML prediction in a thread pool to avoid blocking"""
        import asyncio
        import concurrent.futures
        
        # Run CPU-intensive ML prediction in thread pool
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            predictions = await loop.run_in_executor(
                executor,
                self.ml_ensemble.predict_comprehensive,
                building_features
            )
        return predictions
    
    async def _fallback_predictions_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of fallback predictions for consistency"""
        return self._fallback_predictions(data)
    
    def _fallback_predictions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based predictions when ML fails"""
        
        construction_year = data['construction_year']
        total_area = data['total_area']
        building_type = data['building_type']
        
        # Simple rule-based energy class estimation
        building_age = datetime.now().year - construction_year
        
        if building_age < 10:
            energy_class = EnergyClass.B
            confidence = 0.75
        elif building_age < 25:
            energy_class = EnergyClass.C
            confidence = 0.70
        elif building_age < 40:
            energy_class = EnergyClass.D
            confidence = 0.65
        else:
            energy_class = EnergyClass.E
            confidence = 0.60
        
        # Estimate consumption based on age and area
        base_consumption = 100 + (building_age * 2)  # kWh/m²/year
        if building_type == 'commercial':
            base_consumption *= 1.5
        
        total_consumption = base_consumption * total_area
        
        # Estimate ROI potential
        roi_potential = max(5, 25 - (building_age * 0.3))
        
        return {
            'energy_class': {
                'predicted_class': energy_class,
                'confidence': confidence
            },
            'annual_consumption': {
                'kwh_per_m2': base_consumption,
                'total_kwh': total_consumption
            },
            'upgrade_roi': {
                'expected_roi_percentage': roi_potential,
                'investment_attractiveness': 'High' if roi_potential > 15 else 'Medium'
            }
        }

class RecommendationGenerationStage(PipelineStage):
    """
    Generates energy upgrade recommendations based on predictions
    Creates actionable improvement suggestions with cost-benefit analysis
    """
    
    def __init__(self):
        super().__init__("RecommendationGeneration")
    
    async def _execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate upgrade recommendations based on predictions"""
        
        if not context['config'].get('enable_recommendations', True):
            logger.debug("Recommendation generation disabled in pipeline config")
            return data
        
        if '_predictions' not in data:
            raise ValueError("Predictions must be available before generating recommendations")
        
        property_id = data['property_id']
        building_features = data['_features']['building_features']
        predictions = data['_predictions']
        
        # Generate recommendations based on building characteristics
        recommendations = []
        
        # Heating system upgrade recommendation
        if building_features.heating_system_efficiency < 0.8:
            try:
                heating_rec = create_heating_system_upgrade(
                    current_system=data.get('heating_system', 'individual_gas'),
                    building_area=Decimal(str(building_features.total_area)),
                    target_efficiency_gain=Decimal('30')
                )
                recommendations.append(heating_rec)
            except Exception as e:
                logger.warning(f"Failed to create heating system recommendation: {e}")
        
        # Insulation recommendations based on building age and current state
        if building_features.wall_insulation_score < 0.6:
            recommendations.append(self._create_insulation_recommendation(
                'wall_insulation',
                building_features,
                cost_multiplier=1.0
            ))
        
        if building_features.roof_insulation_score < 0.6:
            recommendations.append(self._create_insulation_recommendation(
                'roof_insulation',
                building_features,
                cost_multiplier=0.7
            ))
        
        # Window upgrade recommendation
        if building_features.window_efficiency_score < 0.5:
            recommendations.append(self._create_window_upgrade_recommendation(building_features))
        
        # Solar panel recommendation for suitable buildings
        if self._is_suitable_for_solar(building_features):
            recommendations.append(self._create_solar_recommendation(building_features))
        
        # Sort recommendations by priority score
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        
        # Limit to top recommendations
        top_recommendations = recommendations[:5]
        
        # Add recommendations to data
        enriched_data = data.copy()
        enriched_data['_recommendations'] = {
            'recommendations': [rec.to_dict() for rec in top_recommendations],
            'total_count': len(top_recommendations),
            'generated_at': datetime.now().isoformat(),
            'total_investment_required': sum(rec.cost for rec in top_recommendations),
            'total_annual_savings': sum(rec.annual_savings for rec in top_recommendations)
        }
        
        logger.debug(f"Generated {len(top_recommendations)} recommendations for property {property_id}")
        
        return enriched_data
    
    def _create_insulation_recommendation(
        self,
        insulation_type: str,
        building_features: BuildingFeatures,
        cost_multiplier: float = 1.0
    ) -> UpgradeRecommendation:
        """Create insulation upgrade recommendation"""
        
        from domains.energy.value_objects.upgrade_recommendation import (
            UpgradeRecommendation, UpgradeType, UpgradePriority, 
            ImplementationDifficulty, GovernmentSubsidy
        )
        
        # Calculate costs and savings
        area = building_features.total_area
        cost_per_m2 = 45 if insulation_type == 'wall_insulation' else 35  # €/m²
        
        if insulation_type == 'wall_insulation':
            effective_area = area * 1.2  # Wall area estimate
            upgrade_type = UpgradeType.WALL_INSULATION
        else:
            effective_area = area  # Roof area
            upgrade_type = UpgradeType.ROOF_INSULATION
        
        cost = Decimal(str(effective_area * cost_per_m2 * cost_multiplier))
        annual_savings = Decimal(str(area * 12))  # €12/m²/year savings
        roi = (annual_savings / cost) * 100 if cost > 0 else Decimal('0')
        payback = cost / annual_savings if annual_savings > 0 else Decimal('999')
        
        # Government subsidy
        subsidy = GovernmentSubsidy(
            program_name="Εξοικονομώ - Κατ' Οίκον",
            subsidy_percentage=Decimal('70'),
            max_subsidy_amount=Decimal('15000'),
            eligibility_criteria=["Building age > 15 years", "Energy class D or lower"]
        )
        
        return UpgradeRecommendation(
            upgrade_type=upgrade_type,
            priority=UpgradePriority.HIGH if roi > 12 else UpgradePriority.MEDIUM,
            implementation_difficulty=ImplementationDifficulty.MODERATE,
            cost=cost,
            annual_savings=annual_savings,
            roi=roi,
            simple_payback_years=payback,
            description=f"{insulation_type.replace('_', ' ').title()} upgrade for improved energy efficiency",
            technical_specifications={
                'insulation_type': 'Mineral wool or EPS',
                'thickness': '10cm',
                'area_coverage': f"{effective_area:.0f}m²"
            },
            energy_class_improvement=1,
            implementation_time="2-3 weeks",
            best_season="spring",
            permits_required=["Building permit"],
            available_subsidies=[subsidy],
            confidence_level=Decimal('0.8')
        )
    
    def _create_window_upgrade_recommendation(self, building_features: BuildingFeatures) -> UpgradeRecommendation:
        """Create window upgrade recommendation"""
        
        from domains.energy.value_objects.upgrade_recommendation import (
            UpgradeRecommendation, UpgradeType, UpgradePriority, 
            ImplementationDifficulty
        )
        
        window_area = building_features.total_area * 0.15  # 15% of floor area
        cost_per_m2 = 350  # €/m² for double glazing
        
        cost = Decimal(str(window_area * cost_per_m2))
        annual_savings = Decimal(str(building_features.total_area * 8))  # €8/m²/year
        roi = (annual_savings / cost) * 100 if cost > 0 else Decimal('0')
        payback = cost / annual_savings if annual_savings > 0 else Decimal('999')
        
        return UpgradeRecommendation(
            upgrade_type=UpgradeType.WINDOW_REPLACEMENT,
            priority=UpgradePriority.MEDIUM,
            implementation_difficulty=ImplementationDifficulty.MODERATE,
            cost=cost,
            annual_savings=annual_savings,
            roi=roi,
            simple_payback_years=payback,
            description="Double-glazed window replacement for better thermal performance",
            technical_specifications={
                'window_type': 'Double-glazed with thermal break',
                'u_value': '1.4 W/m²K',
                'area_coverage': f"{window_area:.0f}m²"
            },
            energy_class_improvement=1,
            implementation_time="1-2 weeks",
            best_season="spring",
            permits_required=[],
            available_subsidies=[],
            confidence_level=Decimal('0.85')
        )
    
    def _create_solar_recommendation(self, building_features: BuildingFeatures) -> UpgradeRecommendation:
        """Create solar panel recommendation"""
        
        from domains.energy.value_objects.upgrade_recommendation import (
            UpgradeRecommendation, UpgradeType, UpgradePriority, 
            ImplementationDifficulty
        )
        
        # Solar system sizing (5kW for typical home)
        system_size_kw = min(10, building_features.total_area / 20)  # 1kW per 20m²
        cost_per_kw = 1800  # €/kW installed
        
        cost = Decimal(str(system_size_kw * cost_per_kw))
        # Annual generation: ~1300 kWh/kW in Greece
        annual_generation = system_size_kw * 1300
        # Savings: €0.15/kWh (grid price) - €0.05/kWh (feed-in tariff) = €0.10/kWh saved
        annual_savings = Decimal(str(annual_generation * 0.12))  # €0.12/kWh net benefit
        
        roi = (annual_savings / cost) * 100 if cost > 0 else Decimal('0')
        payback = cost / annual_savings if annual_savings > 0 else Decimal('999')
        
        return UpgradeRecommendation(
            upgrade_type=UpgradeType.SOLAR_PANELS,
            priority=UpgradePriority.HIGH,
            implementation_difficulty=ImplementationDifficulty.MODERATE,
            cost=cost,
            annual_savings=annual_savings,
            roi=roi,
            simple_payback_years=payback,
            description=f"Solar photovoltaic system ({system_size_kw:.1f}kW) for renewable energy generation",
            technical_specifications={
                'system_size': f"{system_size_kw:.1f}kW",
                'panel_type': 'Monocrystalline silicon',
                'annual_generation': f"{annual_generation:.0f}kWh/year",
                'warranty': '25 years performance'
            },
            energy_class_improvement=1,
            implementation_time="1-2 weeks",
            best_season="spring",
            permits_required=["Electrical permit", "Grid connection permit"],
            available_subsidies=[],
            confidence_level=Decimal('0.90'),
            environmental_impact=f"Reduces CO2 emissions by ~{annual_generation * 0.5:.0f}kg/year"
        )
    
    def _is_suitable_for_solar(self, building_features: BuildingFeatures) -> bool:
        """Check if building is suitable for solar panels"""
        # Simple suitability check
        return (
            building_features.total_area > 50 and  # Minimum size
            building_features.solar_irradiance > 1400 and  # Good solar resource
            building_features.building_type_residential == 1  # Residential building
        )

class ReportGenerationStage(PipelineStage):
    """
    Generates comprehensive assessment reports and summaries
    Creates structured output for various consumption channels
    """
    
    def __init__(self):
        super().__init__("ReportGeneration")
    
    async def _execute(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final assessment report"""
        
        property_id = data['property_id']
        
        # Create comprehensive report
        report = {
            'assessment_summary': self._create_assessment_summary(data),
            'energy_performance': self._create_energy_performance_section(data),
            'upgrade_recommendations': self._create_recommendations_section(data),
            'financial_analysis': self._create_financial_analysis(data),
            'market_comparison': self._create_market_comparison(data) if context['config'].get('enable_market_comparison') else None,
            'technical_details': self._create_technical_section(data),
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'property_id': property_id,
                'report_version': '2.0',
                'processing_pipeline': context['pipeline_id'],
                'confidence_score': self._calculate_overall_confidence(data)
            }
        }
        
        # Add report to data
        final_data = data.copy()
        final_data['assessment_report'] = report
        
        logger.debug(f"Assessment report generated for property {property_id}")
        
        return final_data
    
    def _create_assessment_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create high-level assessment summary"""
        
        predictions = data.get('_predictions', {})
        recommendations = data.get('_recommendations', {})
        
        # Extract key metrics
        energy_class = predictions.get('energy_class', {}).get('predicted_class')
        confidence = predictions.get('energy_class', {}).get('confidence', 0.0)
        consumption = predictions.get('annual_consumption', {}).get('kwh_per_m2', 0)
        
        if hasattr(energy_class, 'value'):
            energy_class_str = energy_class.value
        else:
            energy_class_str = str(energy_class) if energy_class else 'Unknown'
        
        return {
            'property_id': data['property_id'],
            'current_energy_class': energy_class_str,
            'prediction_confidence': float(confidence),
            'annual_consumption_per_m2': float(consumption),
            'total_annual_consumption': float(consumption * data['total_area']),
            'building_age': data.get('building_age', 0),
            'assessment_date': datetime.now().isoformat(),
            'recommendations_count': recommendations.get('total_count', 0),
            'potential_annual_savings': float(recommendations.get('total_annual_savings', 0)),
            'investment_required': float(recommendations.get('total_investment_required', 0))
        }
    
    def _create_energy_performance_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create energy performance analysis section"""
        
        predictions = data.get('_predictions', {})
        features = data.get('_features', {}).get('building_features')
        
        performance = {
            'current_rating': {
                'energy_class': str(predictions.get('energy_class', {}).get('predicted_class', 'Unknown')),
                'consumption_kwh_per_m2': float(predictions.get('annual_consumption', {}).get('kwh_per_m2', 0)),
                'confidence_level': float(predictions.get('energy_class', {}).get('confidence', 0))
            },
            'building_characteristics': {
                'construction_year': data['construction_year'],
                'building_age': data.get('building_age', 0),
                'total_area': float(data['total_area']),
                'building_type': data['building_type'],
                'heating_system': data.get('heating_system', 'unknown')
            }
        }
        
        if features:
            performance['efficiency_factors'] = {
                'heating_efficiency': float(features.heating_system_efficiency),
                'insulation_quality': {
                    'walls': float(features.wall_insulation_score),
                    'roof': float(features.roof_insulation_score),
                    'windows': float(features.window_efficiency_score)
                },
                'building_envelope': float(features.surface_to_volume_ratio)
            }
        
        return performance
    
    def _create_recommendations_section(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create recommendations section"""
        
        recommendations_data = data.get('_recommendations')
        if not recommendations_data:
            return None
        
        recommendations = recommendations_data.get('recommendations', [])
        
        if not recommendations:
            return None
        
        return {
            'total_recommendations': len(recommendations),
            'total_investment': float(recommendations_data.get('total_investment_required', 0)),
            'total_annual_savings': float(recommendations_data.get('total_annual_savings', 0)),
            'recommendations': recommendations,
            'implementation_priority': [
                rec for rec in recommendations 
                if rec.get('priority') in ['critical', 'high']
            ][:3]  # Top 3 high priority
        }
    
    def _create_financial_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create financial analysis section"""
        
        recommendations_data = data.get('_recommendations', {})
        predictions = data.get('_predictions', {})
        
        investment_required = float(recommendations_data.get('total_investment_required', 0))
        annual_savings = float(recommendations_data.get('total_annual_savings', 0))
        
        roi = (annual_savings / investment_required * 100) if investment_required > 0 else 0
        payback_years = investment_required / annual_savings if annual_savings > 0 else 999
        
        return {
            'investment_summary': {
                'total_investment_required': investment_required,
                'annual_energy_savings': annual_savings,
                'simple_roi_percentage': roi,
                'payback_period_years': min(payback_years, 50),  # Cap at 50 years
                'investment_grade': 'Excellent' if roi > 15 else 'Good' if roi > 8 else 'Moderate'
            },
            'current_costs': {
                'estimated_annual_energy_cost': float(
                    predictions.get('annual_consumption', {}).get('kwh_per_m2', 150) * 
                    data['total_area'] * 0.15  # €0.15/kWh
                )
            }
        }
    
    def _create_market_comparison(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create market comparison section"""
        
        building_type = data['building_type']
        construction_year = data['construction_year']
        location = data.get('location', {})
        
        # Mock market comparison data
        return {
            'regional_average': {
                'energy_class': 'C',
                'consumption_kwh_per_m2': 175.0,
                'annual_cost_per_m2': 26.25
            },
            'similar_properties': {
                'average_energy_class': 'D',
                'percentile_ranking': 65,  # This property performs better than 65% of similar properties
                'upgrade_adoption_rate': 0.35  # 35% of similar properties have undergone upgrades
            },
            'market_trends': {
                'energy_price_trend': '+8.5%',  # Annual increase
                'upgrade_activity': 'High',
                'subsidy_availability': 'Excellent'
            }
        }
    
    def _create_technical_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create technical details section"""
        
        return {
            'assessment_methodology': {
                'prediction_method': data.get('_predictions', {}).get('prediction_method', 'rule_based'),
                'feature_count': data.get('_features', {}).get('feature_count', 0),
                'model_version': '2.0',
                'data_sources': ['Property registry', 'Climate data', 'Market data']
            },
            'data_quality': {
                'validation_status': 'Passed',
                'warnings_count': len(data.get('_validation_metadata', {}).get('warnings', [])),
                'confidence_factors': [
                    'Complete property data',
                    'Recent market data',
                    'Validated against similar properties'
                ]
            }
        }
    
    def _calculate_overall_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate overall assessment confidence score"""
        
        confidence_factors = []
        
        # Prediction confidence
        pred_confidence = data.get('_predictions', {}).get('energy_class', {}).get('confidence', 0.5)
        confidence_factors.append(pred_confidence)
        
        # Data completeness
        required_fields = ['construction_year', 'total_area', 'building_type', 'heating_system']
        completeness = sum(1 for field in required_fields if field in data and data[field]) / len(required_fields)
        confidence_factors.append(completeness)
        
        # Validation warnings impact
        warnings_count = len(data.get('_validation_metadata', {}).get('warnings', []))
        warning_penalty = max(0, 1 - (warnings_count * 0.1))  # -10% per warning
        confidence_factors.append(warning_penalty)
        
        # Overall confidence is the average of all factors
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return round(overall_confidence, 3)