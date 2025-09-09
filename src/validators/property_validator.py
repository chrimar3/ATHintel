"""
Property Data Authenticity Validator
Implements 6-factor validation for real estate properties
Story 1.1: Data Authenticity Validator Implementation
"""

import re
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import yaml
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.feature_flags import feature_flag, get_feature_flags
from security.input_validator import InputValidator, ValidationException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationScore:
    """Detailed validation score breakdown"""
    url_score: float = 0.0
    price_score: float = 0.0
    attributes_score: float = 0.0
    market_score: float = 0.0
    temporal_score: float = 0.0
    image_score: float = 0.0
    total_score: float = 0.0
    
    def calculate_total(self, weights: Dict[str, float]) -> float:
        """Calculate weighted total score"""
        self.total_score = (
            self.url_score * weights.get('url', 0.3) +
            self.price_score * weights.get('price', 0.2) +
            self.attributes_score * weights.get('attributes', 0.2) +
            self.market_score * weights.get('market', 0.15) +
            self.temporal_score * weights.get('temporal', 0.1) +
            self.image_score * weights.get('images', 0.05)
        )
        return self.total_score


@dataclass
class ValidationResult:
    """Complete validation result for a property"""
    property_id: str
    is_valid: bool
    score: ValidationScore
    errors: List[str]
    warnings: List[str]
    validation_time: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'property_id': self.property_id,
            'is_valid': self.is_valid,
            'total_score': self.score.total_score,
            'score_breakdown': {
                'url': self.score.url_score,
                'price': self.score.price_score,
                'attributes': self.score.attributes_score,
                'market': self.score.market_score,
                'temporal': self.score.temporal_score,
                'images': self.score.image_score
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'validation_time_ms': self.validation_time * 1000,
            'timestamp': self.timestamp.isoformat()
        }


class PropertyValidator:
    """
    Multi-factor property data validator
    Validates property authenticity across 6 dimensions
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'thresholds': {
            'min_score': 70,  # Minimum score to pass validation
            'price_deviation': 0.3,  # 30% price deviation allowed
            'size_min': 20,  # Minimum size in m²
            'size_max': 500,  # Maximum size in m²
            'rooms_min': 1,
            'rooms_max': 10,
            'floor_min': -1,
            'floor_max': 20,
            'year_min': 1800,
            'year_max': 2025,
            'listing_age_days': 180  # Maximum age of listing
        },
        'weights': {
            'url': 0.3,
            'price': 0.2,
            'attributes': 0.2,
            'market': 0.15,
            'temporal': 0.1,
            'images': 0.05
        },
        'valid_domains': [
            'spitogatos.gr',
            'xe.gr',
            'tospitimou.gr',
            'plot.gr'
        ]
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize validator with configuration
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config = self._load_config(config_file)
        self.ff = get_feature_flags()
        self.validation_count = 0
        self.start_time = time.time()
        
        # Initialize secure input validator
        self.input_validator = InputValidator()
        
        # Load market data for comparison
        self.market_data = self._load_market_data()
        
        logger.info("PropertyValidator initialized with secure validation enabled")
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file or use defaults"""
        config = self.DEFAULT_CONFIG.copy()
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge user config with defaults
                    for key, value in user_config.items():
                        if isinstance(value, dict):
                            config[key].update(value)
                        else:
                            config[key] = value
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
        
        return config
    
    def _load_market_data(self) -> Dict[str, Any]:
        """Load market data for comparison"""
        # In production, this would load from database or API
        # For now, using static neighborhood averages
        return {
            'Kolonaki': {'avg_price': 4500, 'avg_size': 85, 'properties': 150},
            'Exarchia': {'avg_price': 2800, 'avg_size': 75, 'properties': 200},
            'Koukaki': {'avg_price': 3200, 'avg_size': 80, 'properties': 180},
            'Pagkrati': {'avg_price': 3000, 'avg_size': 82, 'properties': 160},
            'Neos Kosmos': {'avg_price': 2900, 'avg_size': 78, 'properties': 140},
            'Kypseli': {'avg_price': 2400, 'avg_size': 70, 'properties': 210},
            'Glyfada': {'avg_price': 4200, 'avg_size': 95, 'properties': 120},
            'Marousi': {'avg_price': 3800, 'avg_size': 90, 'properties': 130}
        }
    
    @feature_flag("data_validation_enabled")
    def validate_property(self, property_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single property across all factors with security checks
        
        Args:
            property_data: Property data dictionary
            
        Returns:
            ValidationResult with scores and errors
        """
        start_time = time.time()
        property_id = property_data.get('id', 'unknown')
        errors = []
        warnings = []
        
        # SECURITY: First perform input validation and sanitization
        try:
            # Validate and sanitize all inputs
            if 'id' in property_data:
                property_data['id'] = self.input_validator.validate_property_id(property_data['id'])
            if 'url' in property_data:
                property_data['url'] = self.input_validator.validate_url(property_data['url'])
            if 'price' in property_data:
                property_data['price'] = self.input_validator.validate_numeric(property_data['price'], min_val=0)
            if 'size' in property_data:
                property_data['size'] = self.input_validator.validate_numeric(property_data['size'], min_val=0)
            if 'location' in property_data:
                property_data['location'] = self.input_validator.sanitize_text(property_data['location'])
            if 'description' in property_data:
                property_data['description'] = self.input_validator.sanitize_html(property_data['description'])
            
        except ValidationException as e:
            errors.append(f"Security validation failed: {str(e)}")
            logger.warning(f"Security validation failed for property {property_id}: {str(e)}")
            
            # Return invalid result for security violations
            return ValidationResult(
                property_id=property_id,
                is_valid=False,
                score=ValidationScore(),  # All zeros
                errors=errors,
                warnings=warnings,
                validation_time=time.time() - start_time,
                timestamp=datetime.now()
            )
        
        # Initialize score
        score = ValidationScore()
        
        # Enable multi-factor validation if flag is set
        if self.ff.is_enabled("multi_factor_validation"):
            # Factor 1: URL Verification
            score.url_score = self._validate_url(property_data, errors, warnings)
            
            # Factor 2: Price Consistency
            score.price_score = self._validate_price(property_data, errors, warnings)
            
            # Factor 3: Property Attributes
            score.attributes_score = self._validate_attributes(property_data, errors, warnings)
            
            # Factor 4: Market Cross-Reference
            score.market_score = self._validate_market(property_data, errors, warnings)
            
            # Factor 5: Temporal Validation
            score.temporal_score = self._validate_temporal(property_data, errors, warnings)
            
            # Factor 6: Image Analysis (optional)
            score.image_score = self._validate_images(property_data, errors, warnings)
        else:
            # Basic validation only
            score.url_score = self._validate_url(property_data, errors, warnings)
            score.price_score = 100 if property_data.get('price', 0) > 0 else 0
            score.attributes_score = 100
            score.market_score = 100
            score.temporal_score = 100
            score.image_score = 100
        
        # Calculate total score
        total = score.calculate_total(self.config['weights'])
        
        # Determine if valid
        is_valid = (
            total >= self.config['thresholds']['min_score'] and
            len(errors) == 0
        )
        
        # Log validation
        validation_time = time.time() - start_time
        self.validation_count += 1
        
        if self.ff.is_enabled("validation_logging"):
            self._log_validation(property_id, total, is_valid, errors, warnings)
        
        result = ValidationResult(
            property_id=property_id,
            is_valid=is_valid,
            score=score,
            errors=errors,
            warnings=warnings,
            validation_time=validation_time,
            timestamp=datetime.now()
        )
        
        # Record to monitoring dashboard if enabled
        if self.ff.is_enabled("monitoring_enabled"):
            try:
                from ..monitoring.metrics_collector import record_validation
                record_validation(result.to_dict())
            except ImportError:
                pass  # Monitoring not available
        
        return result
    
    def _validate_url(self, property_data: Dict[str, Any], 
                     errors: List[str], warnings: List[str]) -> float:
        """Validate property URL with security checks"""
        url = property_data.get('url', '')
        
        if not url:
            errors.append("Missing property URL")
            return 0
        
        # SECURITY: URL has already been validated by input_validator
        # Additional business logic validation
        
        # Check if URL is from valid domain
        valid_domain = any(domain in url for domain in self.config['valid_domains'])
        
        if not valid_domain:
            warnings.append(f"URL from unrecognized domain: {url}")
            return 50
        
        # Additional suspicious URL pattern checks
        suspicious_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'\b(?:admin|api|test|dev)\b',
            r'[<>"\']'  # HTML/script injection attempts
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                warnings.append(f"Suspicious URL pattern detected: {pattern}")
                return 30
        
        # In production, would verify URL exists (network request)
        # For now, assume valid if format is correct and secure
        return 100
    
    def _validate_price(self, property_data: Dict[str, Any],
                       errors: List[str], warnings: List[str]) -> float:
        """Validate price consistency with security checks"""
        price = property_data.get('price', 0)
        location = property_data.get('location', '')
        size = property_data.get('size', 0)
        
        # SECURITY: Numeric values have already been validated by input_validator
        # Additional business logic validation
        
        if price <= 0:
            errors.append(f"Invalid price: {price}")
            return 0
        
        # Check for price manipulation attempts
        if isinstance(price, str):
            # This shouldn't happen after input validation, but extra safety
            errors.append("Price must be numeric")
            return 0
        
        if price > 10000000:  # €10M upper limit
            warnings.append(f"Unusually high price: €{price:,.0f}")
            return 50
        
        # Check price per m² if size available
        if size > 0:
            price_per_m2 = price / size
            
            # Get neighborhood average if available
            if location in self.market_data:
                avg_price_m2 = self.market_data[location]['avg_price']
                deviation = abs(price_per_m2 - avg_price_m2) / avg_price_m2
                
                if deviation > self.config['thresholds']['price_deviation']:
                    warnings.append(
                        f"Price €{price_per_m2:.0f}/m² deviates {deviation:.0%} "
                        f"from {location} average €{avg_price_m2:.0f}/m²"
                    )
                    
                    # Score based on deviation
                    if deviation < 0.5:
                        return 70
                    elif deviation < 1.0:
                        return 40
                    else:
                        return 20
                
                return 100
        
        # No size or location data, basic validation passed
        return 80
    
    def _validate_attributes(self, property_data: Dict[str, Any],
                            errors: List[str], warnings: List[str]) -> float:
        """Validate property attributes"""
        score = 100
        thresholds = self.config['thresholds']
        
        # Validate size
        size = property_data.get('size', 0)
        if size > 0:
            if size < thresholds['size_min']:
                warnings.append(f"Size too small: {size}m²")
                score -= 20
            elif size > thresholds['size_max']:
                warnings.append(f"Size unusually large: {size}m²")
                score -= 10
        
        # Validate rooms
        rooms = property_data.get('rooms', 0)
        if rooms > 0:
            if rooms < thresholds['rooms_min'] or rooms > thresholds['rooms_max']:
                warnings.append(f"Unusual room count: {rooms}")
                score -= 15
            
            # Check room/size ratio if both available
            if size > 0:
                m2_per_room = size / rooms
                if m2_per_room < 10:  # Less than 10m² per room
                    warnings.append(f"Suspicious room/size ratio: {m2_per_room:.1f}m²/room")
                    score -= 25
                elif m2_per_room > 100:  # More than 100m² per room
                    warnings.append(f"Unusual room/size ratio: {m2_per_room:.1f}m²/room")
                    score -= 15
        
        # Validate floor
        floor = property_data.get('floor')
        if floor is not None:
            if floor < thresholds['floor_min'] or floor > thresholds['floor_max']:
                warnings.append(f"Unusual floor: {floor}")
                score -= 10
        
        # Validate year
        year = property_data.get('year_built')
        if year:
            current_year = datetime.now().year
            if year < thresholds['year_min'] or year > current_year:
                errors.append(f"Invalid construction year: {year}")
                return 0
        
        return max(score, 0)
    
    def _validate_market(self, property_data: Dict[str, Any],
                        errors: List[str], warnings: List[str]) -> float:
        """Validate against market data"""
        location = property_data.get('location', '')
        
        if not location:
            warnings.append("No location for market validation")
            return 50
        
        if location not in self.market_data:
            warnings.append(f"No market data for location: {location}")
            return 60
        
        market = self.market_data[location]
        score = 100
        
        # Compare size if available
        size = property_data.get('size', 0)
        if size > 0:
            avg_size = market['avg_size']
            size_deviation = abs(size - avg_size) / avg_size
            
            if size_deviation > 0.5:  # More than 50% deviation
                warnings.append(
                    f"Size {size}m² deviates significantly from "
                    f"{location} average {avg_size}m²"
                )
                score -= 20
        
        # Could add more market comparisons here
        # - Property type distribution
        # - Features comparison
        # - Historical price trends
        
        return max(score, 0)
    
    def _validate_temporal(self, property_data: Dict[str, Any],
                          errors: List[str], warnings: List[str]) -> float:
        """Validate temporal aspects (listing age)"""
        listed_date_str = property_data.get('listed_date', '')
        
        if not listed_date_str:
            warnings.append("No listing date available")
            return 50
        
        try:
            # Parse listing date
            listed_date = datetime.fromisoformat(listed_date_str.replace('Z', '+00:00'))
            
            # Check if future date
            if listed_date > datetime.now():
                errors.append(f"Future listing date: {listed_date_str}")
                return 0
            
            # Calculate age
            age_days = (datetime.now() - listed_date).days
            max_age = self.config['thresholds']['listing_age_days']
            
            if age_days < 0:
                errors.append(f"Invalid listing date: {listed_date_str}")
                return 0
            elif age_days <= 30:
                return 100
            elif age_days <= 90:
                return 70
            elif age_days <= max_age:
                return 40
            else:
                warnings.append(f"Stale listing: {age_days} days old")
                return 20
                
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid date format: {listed_date_str}")
            return 0
    
    def _validate_images(self, property_data: Dict[str, Any],
                        errors: List[str], warnings: List[str]) -> float:
        """Validate image data (optional factor)"""
        images = property_data.get('images', [])
        
        if not images:
            warnings.append("No images provided")
            return 50
        
        if len(images) < 3:
            warnings.append(f"Few images: {len(images)}")
            return 70
        
        if len(images) > 50:
            warnings.append(f"Excessive images: {len(images)}")
            return 80
        
        # In production, would check for:
        # - Duplicate images
        # - Stock photos
        # - Image quality
        # - EXIF data
        
        return 100
    
    def validate_batch(self, properties: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        Validate multiple properties
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            List of ValidationResults
        """
        results = []
        batch_start = time.time()
        
        for prop in properties:
            result = self.validate_property(prop)
            results.append(result)
        
        batch_time = time.time() - batch_start
        properties_per_minute = (len(properties) / batch_time) * 60
        
        logger.info(
            f"Validated {len(properties)} properties in {batch_time:.2f}s "
            f"({properties_per_minute:.0f} props/min)"
        )
        
        # Check performance benchmark
        if properties_per_minute < 100:
            logger.warning(
                f"Performance below target: {properties_per_minute:.0f} < 100 props/min"
            )
        
        return results
    
    def _log_validation(self, property_id: str, score: float, is_valid: bool,
                       errors: List[str], warnings: List[str]):
        """Log validation result"""
        log_entry = {
            'property_id': property_id,
            'score': score,
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
        
        # In production, would write to audit log
        if is_valid:
            logger.info(f"✅ Property {property_id} validated (score: {score:.1f})")
        else:
            logger.warning(f"❌ Property {property_id} failed validation: {errors}")
        
        # Save to audit file if enabled
        if self.ff.is_enabled("audit_logging"):
            self._save_audit_log(log_entry)
    
    def _save_audit_log(self, log_entry: Dict[str, Any]):
        """Save audit log entry"""
        audit_file = Path("logs/validation_audit.jsonl")
        audit_file.parent.mkdir(exist_ok=True)
        
        with open(audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        elapsed = time.time() - self.start_time
        
        return {
            'total_validated': self.validation_count,
            'elapsed_time': elapsed,
            'properties_per_minute': (self.validation_count / elapsed) * 60 if elapsed > 0 else 0,
            'uptime': elapsed
        }
    
    def save_config(self, filepath: str):
        """Save current configuration to YAML file"""
        with open(filepath, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        logger.info(f"Configuration saved to {filepath}")