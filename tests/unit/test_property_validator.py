"""
Unit Tests for Property Validator
Story 1.1: Data Authenticity Validator
Target Coverage: 90%
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from validators.property_validator import PropertyValidator, ValidationResult, ValidationScore
from config.feature_flags import get_feature_flags


class TestPropertyValidator:
    """Test suite for PropertyValidator"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return PropertyValidator()
    
    @pytest.fixture
    def valid_property(self):
        """Valid property for testing"""
        return {
            'id': 'test_001',
            'url': 'https://spitogatos.gr/property/12345',
            'price': 350000,
            'size': 120,
            'rooms': 3,
            'floor': 2,
            'location': 'Kolonaki',
            'listed_date': datetime.now().isoformat(),
            'images': ['img1.jpg', 'img2.jpg', 'img3.jpg'],
            'year_built': 2010
        }
    
    # ==================== URL Validation Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_url_validation_valid(self, validator, valid_property):
        """Test URL validation with valid URL"""
        result = validator.validate_property(valid_property)
        assert result.score.url_score == 100
        assert len(result.errors) == 0
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_url_validation_missing(self, validator, valid_property):
        """Test URL validation with missing URL"""
        valid_property['url'] = ''
        result = validator.validate_property(valid_property)
        assert result.score.url_score == 0
        assert 'Missing property URL' in result.errors
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_url_validation_invalid_domain(self, validator, valid_property):
        """Test URL validation with invalid domain"""
        valid_property['url'] = 'https://fake-site.com/property/123'
        result = validator.validate_property(valid_property)
        assert result.score.url_score == 50
        assert any('unrecognized domain' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_url_validation_malformed(self, validator, valid_property):
        """Test URL validation with malformed URL"""
        valid_property['url'] = 'not-a-url'
        result = validator.validate_property(valid_property)
        assert result.score.url_score == 0
        assert any('Invalid URL format' in e for e in result.errors)
    
    # ==================== Price Validation Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_price_validation_valid(self, validator, valid_property):
        """Test price validation with valid price"""
        result = validator.validate_property(valid_property)
        assert result.score.price_score > 0
        assert not any('Invalid price' in e for e in result.errors)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_price_validation_negative(self, validator, valid_property):
        """Test price validation with negative price"""
        valid_property['price'] = -100000
        result = validator.validate_property(valid_property)
        assert result.score.price_score == 0
        assert any('Invalid price' in e for e in result.errors)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_price_validation_zero(self, validator, valid_property):
        """Test price validation with zero price"""
        valid_property['price'] = 0
        result = validator.validate_property(valid_property)
        assert result.score.price_score == 0
        assert any('Invalid price' in e for e in result.errors)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_price_validation_excessive(self, validator, valid_property):
        """Test price validation with excessive price"""
        valid_property['price'] = 15000000  # €15M
        result = validator.validate_property(valid_property)
        assert result.score.price_score == 50
        assert any('Unusually high price' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_price_deviation_from_market(self, validator, valid_property):
        """Test price deviation from market average"""
        # Kolonaki average is €4500/m², this property would be €2916/m²
        # Deviation is (4500-2916)/4500 = 35%, above 30% threshold
        result = validator.validate_property(valid_property)
        # Should get a warning about deviation
        assert any('deviates' in w for w in result.warnings)
    
    # ==================== Attribute Validation Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_attributes_validation_valid(self, validator, valid_property):
        """Test attributes validation with valid attributes"""
        result = validator.validate_property(valid_property)
        assert result.score.attributes_score > 80
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_attributes_size_too_small(self, validator, valid_property):
        """Test attributes validation with size too small"""
        valid_property['size'] = 10  # Below 20m² minimum
        result = validator.validate_property(valid_property)
        assert result.score.attributes_score < 100
        assert any('Size too small' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_attributes_size_too_large(self, validator, valid_property):
        """Test attributes validation with size too large"""
        valid_property['size'] = 600  # Above 500m² maximum
        result = validator.validate_property(valid_property)
        assert result.score.attributes_score < 100
        assert any('Size unusually large' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_attributes_invalid_room_count(self, validator, valid_property):
        """Test attributes validation with invalid room count"""
        valid_property['rooms'] = 15  # Above 10 room maximum
        result = validator.validate_property(valid_property)
        assert result.score.attributes_score < 100
        assert any('Unusual room count' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_attributes_suspicious_room_ratio(self, validator, valid_property):
        """Test suspicious room to size ratio"""
        valid_property['size'] = 30
        valid_property['rooms'] = 5  # 6m² per room - suspicious
        result = validator.validate_property(valid_property)
        assert result.score.attributes_score < 100
        assert any('Suspicious room/size ratio' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_attributes_invalid_year(self, validator, valid_property):
        """Test attributes validation with invalid year"""
        valid_property['year_built'] = 2030  # Future year
        result = validator.validate_property(valid_property)
        assert any('Invalid construction year' in e for e in result.errors)
    
    # ==================== Market Validation Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_market_validation_with_data(self, validator, valid_property):
        """Test market validation with available data"""
        result = validator.validate_property(valid_property)
        assert result.score.market_score > 0
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_market_validation_no_location(self, validator, valid_property):
        """Test market validation without location"""
        valid_property['location'] = ''
        result = validator.validate_property(valid_property)
        assert result.score.market_score == 50
        assert any('No location' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_market_validation_unknown_location(self, validator, valid_property):
        """Test market validation with unknown location"""
        valid_property['location'] = 'Unknown Area'
        result = validator.validate_property(valid_property)
        assert result.score.market_score == 60
        assert any('No market data' in w for w in result.warnings)
    
    # ==================== Temporal Validation Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_temporal_validation_recent(self, validator, valid_property):
        """Test temporal validation with recent listing"""
        valid_property['listed_date'] = datetime.now().isoformat()
        result = validator.validate_property(valid_property)
        assert result.score.temporal_score == 100
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_temporal_validation_old(self, validator, valid_property):
        """Test temporal validation with old listing"""
        old_date = datetime.now() - timedelta(days=200)
        valid_property['listed_date'] = old_date.isoformat()
        result = validator.validate_property(valid_property)
        assert result.score.temporal_score == 20
        assert any('Stale listing' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_temporal_validation_future(self, validator, valid_property):
        """Test temporal validation with future date"""
        future_date = datetime.now() + timedelta(days=30)
        valid_property['listed_date'] = future_date.isoformat()
        result = validator.validate_property(valid_property)
        assert result.score.temporal_score == 0
        assert any('Future listing date' in e for e in result.errors)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_temporal_validation_invalid_format(self, validator, valid_property):
        """Test temporal validation with invalid date format"""
        valid_property['listed_date'] = 'not-a-date'
        result = validator.validate_property(valid_property)
        assert result.score.temporal_score == 0
        assert any('Invalid date format' in e for e in result.errors)
    
    # ==================== Image Validation Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_image_validation_valid(self, validator, valid_property):
        """Test image validation with valid images"""
        result = validator.validate_property(valid_property)
        assert result.score.image_score == 100
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_image_validation_no_images(self, validator, valid_property):
        """Test image validation with no images"""
        valid_property['images'] = []
        result = validator.validate_property(valid_property)
        assert result.score.image_score == 50
        assert any('No images' in w for w in result.warnings)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_image_validation_few_images(self, validator, valid_property):
        """Test image validation with few images"""
        valid_property['images'] = ['img1.jpg']
        result = validator.validate_property(valid_property)
        assert result.score.image_score == 70
        assert any('Few images' in w for w in result.warnings)
    
    # ==================== Total Score Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_total_score_calculation(self, validator, valid_property):
        """Test total score calculation"""
        result = validator.validate_property(valid_property)
        assert 0 <= result.score.total_score <= 100
        assert result.is_valid == (result.score.total_score >= 70)
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_validation_result_serialization(self, validator, valid_property):
        """Test ValidationResult serialization"""
        result = validator.validate_property(valid_property)
        data = result.to_dict()
        
        assert 'property_id' in data
        assert 'is_valid' in data
        assert 'total_score' in data
        assert 'score_breakdown' in data
        assert 'errors' in data
        assert 'warnings' in data
        assert 'validation_time_ms' in data
        assert 'timestamp' in data
    
    # ==================== Batch Validation Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_batch_validation(self, validator, valid_property):
        """Test batch validation"""
        properties = [valid_property.copy() for _ in range(10)]
        results = validator.validate_batch(properties)
        
        assert len(results) == 10
        assert all(isinstance(r, ValidationResult) for r in results)
    
    # ==================== Configuration Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_config_loading(self, tmp_path):
        """Test configuration loading from file"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
thresholds:
  min_score: 80
weights:
  url: 0.5
  price: 0.5
  attributes: 0.0
  market: 0.0
  temporal: 0.0
  images: 0.0
""")
        
        validator = PropertyValidator(str(config_file))
        assert validator.config['thresholds']['min_score'] == 80
        assert validator.config['weights']['url'] == 0.5
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_save_config(self, validator, tmp_path):
        """Test saving configuration"""
        config_file = tmp_path / "saved_config.yaml"
        validator.save_config(str(config_file))
        
        assert config_file.exists()
        # Verify file can be loaded
        new_validator = PropertyValidator(str(config_file))
        assert new_validator.config == validator.config
    
    # ==================== Statistics Tests ====================
    
    @pytest.mark.story_1_1
    @pytest.mark.unit
    def test_statistics(self, validator, valid_property):
        """Test validation statistics"""
        # Validate some properties
        for _ in range(5):
            validator.validate_property(valid_property)
        
        stats = validator.get_statistics()
        assert stats['total_validated'] == 5
        assert stats['elapsed_time'] > 0
        assert stats['properties_per_minute'] > 0


# ==================== Performance Tests ====================

@pytest.mark.story_1_1
@pytest.mark.performance
class TestPropertyValidatorPerformance:
    """Performance tests for PropertyValidator"""
    
    @pytest.mark.slow
    def test_throughput_100_properties(self, performance_timer):
        """Test validation throughput for 100 properties"""
        validator = PropertyValidator()
        properties = [
            {
                'id': f'perf_{i}',
                'url': f'https://spitogatos.gr/property/{i}',
                'price': 200000 + i * 1000,
                'size': 80 + i % 40,
                'rooms': 2 + i % 3,
                'location': 'Kolonaki',
                'listed_date': datetime.now().isoformat()
            }
            for i in range(100)
        ]
        
        performance_timer.start()
        results = validator.validate_batch(properties)
        performance_timer.stop()
        
        assert len(results) == 100
        # Should process 100 properties in less than 60 seconds
        performance_timer.assert_under(60)
        
        # Calculate throughput
        props_per_minute = (100 / performance_timer.duration) * 60
        assert props_per_minute >= 100, f"Throughput {props_per_minute:.0f} < 100 props/min"