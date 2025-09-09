"""
Secure Input Validation Framework
Addresses critical security vulnerabilities while supporting energy assessment data
Prevents SQL injection, XSS, and path traversal attacks
"""

import re
import html
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_value: Any
    errors: List[str]
    warnings: List[str]


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


class InputValidator:
    """
    Comprehensive input validation and sanitization
    Protects against injection attacks while preserving data integrity
    """
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+\w+\s*=\s*\w+)",
        r"('|\"|;|--|\/\*|\*\/)",
        r"(\bxp_\w+)",
        r"(\bsp_\w+)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe\b[^>]*>",
        r"<object\b[^>]*>",
        r"<embed\b[^>]*>"
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.\/",
        r"\.\.\%2f",
        r"\.\.\%5c",
        r"%2e%2e%2f",
        r"%2e%2e%5c"
    ]
    
    def __init__(self):
        """Initialize validator"""
        self.compiled_sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.compiled_xss_patterns = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        self.compiled_path_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
    
    def validate_property_id(self, value: Any) -> ValidationResult:
        """
        Validate and sanitize property ID
        Critical for preventing injection in database queries
        """
        errors = []
        warnings = []
        
        # Type validation
        if not isinstance(value, (str, int)):
            errors.append("Property ID must be string or integer")
            return ValidationResult(False, None, errors, warnings)
        
        # Convert to string and basic cleanup
        str_value = str(value).strip()
        
        if not str_value:
            errors.append("Property ID cannot be empty")
            return ValidationResult(False, None, errors, warnings)
        
        # Length validation
        if len(str_value) > 100:
            errors.append("Property ID too long (max 100 characters)")
            return ValidationResult(False, None, errors, warnings)
        
        # Check for SQL injection patterns
        if self._contains_sql_injection(str_value):
            errors.append("Property ID contains potentially malicious content")
            return ValidationResult(False, None, errors, warnings)
        
        # Sanitize: allow only alphanumeric, underscores, hyphens
        sanitized = re.sub(r'[^\w\-]', '', str_value)
        
        if sanitized != str_value:
            warnings.append("Property ID was sanitized")
        
        if not sanitized:
            errors.append("Property ID contains no valid characters")
            return ValidationResult(False, None, errors, warnings)
        
        return ValidationResult(True, sanitized, errors, warnings)
    
    def validate_url(self, value: Any) -> ValidationResult:
        """
        Validate and sanitize URLs for property listings
        Prevents XSS and SSRF attacks
        """
        errors = []
        warnings = []
        
        if not isinstance(value, str):
            errors.append("URL must be a string")
            return ValidationResult(False, None, errors, warnings)
        
        str_value = value.strip()
        
        if not str_value:
            errors.append("URL cannot be empty")
            return ValidationResult(False, None, errors, warnings)
        
        # Length validation
        if len(str_value) > 2000:
            errors.append("URL too long (max 2000 characters)")
            return ValidationResult(False, None, errors, warnings)
        
        # Check for XSS patterns
        if self._contains_xss(str_value):
            errors.append("URL contains potentially malicious content")
            return ValidationResult(False, None, errors, warnings)
        
        # Validate URL format
        try:
            parsed = urllib.parse.urlparse(str_value)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                errors.append("Invalid URL format")
                return ValidationResult(False, None, errors, warnings)
            
            # Only allow HTTP/HTTPS
            if parsed.scheme.lower() not in ['http', 'https']:
                errors.append("Only HTTP/HTTPS URLs are allowed")
                return ValidationResult(False, None, errors, warnings)
            
            # Validate domain against allowed domains
            allowed_domains = [
                'spitogatos.gr', 'xe.gr', 'tospitimou.gr', 'plot.gr', 'spiti24.gr'
            ]
            
            domain = parsed.netloc.lower()
            if not any(domain.endswith(allowed) for allowed in allowed_domains):
                warnings.append(f"Domain {domain} not in recognized list")
            
            # Sanitize by reconstructing URL
            sanitized = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                ''  # Remove fragment for security
            ))
            
            return ValidationResult(True, sanitized, errors, warnings)
            
        except Exception as e:
            errors.append(f"URL validation failed: {str(e)}")
            return ValidationResult(False, None, errors, warnings)
    
    def validate_numeric(self, value: Any, field_name: str, 
                        min_value: Optional[float] = None,
                        max_value: Optional[float] = None,
                        allow_decimal: bool = True) -> ValidationResult:
        """
        Validate numeric values (price, size, etc.)
        Prevents injection through numeric fields
        """
        errors = []
        warnings = []
        
        # Handle None
        if value is None:
            errors.append(f"{field_name} cannot be None")
            return ValidationResult(False, None, errors, warnings)
        
        # Convert to appropriate numeric type
        try:
            if allow_decimal:
                numeric_value = float(value)
            else:
                numeric_value = int(value)
        except (ValueError, TypeError):
            errors.append(f"{field_name} must be a number")
            return ValidationResult(False, None, errors, warnings)
        
        # Check for special values
        if not isinstance(numeric_value, (int, float)) or numeric_value != numeric_value:  # NaN check
            errors.append(f"{field_name} contains invalid numeric value")
            return ValidationResult(False, None, errors, warnings)
        
        # Range validation
        if min_value is not None and numeric_value < min_value:
            errors.append(f"{field_name} below minimum value {min_value}")
            return ValidationResult(False, None, errors, warnings)
        
        if max_value is not None and numeric_value > max_value:
            if max_value > 10000000:  # Large values get warnings instead of errors
                warnings.append(f"{field_name} unusually high: {numeric_value}")
            else:
                errors.append(f"{field_name} above maximum value {max_value}")
                return ValidationResult(False, None, errors, warnings)
        
        return ValidationResult(True, numeric_value, errors, warnings)
    
    def validate_date(self, value: Any) -> ValidationResult:
        """
        Validate date values
        Prevents date-based injection attacks
        """
        errors = []
        warnings = []
        
        if value is None:
            errors.append("Date cannot be None")
            return ValidationResult(False, None, errors, warnings)
        
        # Handle string dates
        if isinstance(value, str):
            str_value = value.strip()
            
            # Enhanced security checks for date strings
            if len(str_value) == 0:
                errors.append("Date cannot be empty")
                return ValidationResult(False, None, errors, warnings)
            
            if len(str_value) > 50:  # Prevent buffer overflow attempts
                errors.append("Date string too long")
                return ValidationResult(False, None, errors, warnings)
            
            # Check for dangerous characters and patterns
            dangerous_patterns = [
                r'[<>"\'\\/]',  # HTML/Script injection
                r'\\x[0-9a-fA-F]{2}',  # Hex encoded chars
                r'%[0-9a-fA-F]{2}',  # URL encoded chars
                r'\\u[0-9a-fA-F]{4}',  # Unicode escapes
                r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control characters
                r'javascript:',  # JavaScript protocol
                r'vbscript:',   # VBScript protocol
                r'on\w+\s*=',   # Event handlers
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, str_value, re.IGNORECASE):
                    errors.append("Date contains invalid characters")
                    return ValidationResult(False, None, errors, warnings)
            
            # Check for SQL injection in date strings
            if self._contains_sql_injection(str_value):
                errors.append("Date contains potentially malicious content")
                return ValidationResult(False, None, errors, warnings)
            
            # Strict format validation - only allow expected ISO formats
            valid_formats = [
                r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',  # YYYY-MM-DDTHH:MM:SS
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',  # With Z timezone
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'  # With timezone offset
            ]
            
            format_valid = any(re.match(pattern, str_value) for pattern in valid_formats)
            if not format_valid:
                errors.append("Date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
                return ValidationResult(False, None, errors, warnings)
            
            # Try to parse ISO format
            try:
                # Handle timezone info more securely
                clean_date = str_value
                if clean_date.endswith('Z'):
                    clean_date = clean_date[:-1]  # Remove Z
                elif '+' in clean_date[-6:] or '-' in clean_date[-6:]:
                    # Remove timezone offset for basic parsing
                    if 'T' in clean_date:
                        date_part, time_part = clean_date.split('T')
                        if '+' in time_part:
                            time_part = time_part.split('+')[0]
                        elif '-' in time_part and time_part.count('-') == 1:
                            time_part = time_part.split('-')[0]
                        clean_date = f"{date_part}T{time_part}"
                
                # Parse with explicit format checking
                if 'T' in clean_date:
                    parsed_date = datetime.fromisoformat(clean_date)
                else:
                    parsed_date = datetime.strptime(clean_date, '%Y-%m-%d')
                
                # Enhanced date range validation
                current_date = datetime.now()
                
                # Check for reasonable future dates (max 10 years)
                if parsed_date > current_date + timedelta(days=3650):
                    errors.append("Date too far in the future (max 10 years)")
                    return ValidationResult(False, None, errors, warnings)
                
                # Check for reasonable past dates (min 1900)
                if parsed_date < datetime(1900, 1, 1):
                    errors.append("Date too far in the past (min year 1900)")
                    return ValidationResult(False, None, errors, warnings)
                
                # Validate actual date components
                if parsed_date.month < 1 or parsed_date.month > 12:
                    errors.append(f"Invalid month: {parsed_date.month}")
                    return ValidationResult(False, None, errors, warnings)
                
                if parsed_date.day < 1 or parsed_date.day > 31:
                    errors.append(f"Invalid day: {parsed_date.day}")
                    return ValidationResult(False, None, errors, warnings)
                
                # Verify the date is actually valid (e.g., no Feb 30)
                try:
                    datetime(parsed_date.year, parsed_date.month, parsed_date.day)
                except ValueError:
                    errors.append(f"Invalid date: {str_value}")
                    return ValidationResult(False, None, errors, warnings)
                
                return ValidationResult(True, parsed_date, errors, warnings)
                
            except (ValueError, OverflowError) as e:
                errors.append(f"Invalid date format: {str(e)}")
                return ValidationResult(False, None, errors, warnings)
            except Exception as e:
                errors.append(f"Date validation error: {str(e)}")
                return ValidationResult(False, None, errors, warnings)
        
        # Handle datetime objects
        elif isinstance(value, (datetime, date)):
            return ValidationResult(True, value, errors, warnings)
        
        else:
            errors.append("Date must be string or datetime object")
            return ValidationResult(False, None, errors, warnings)
    
    def validate_text(self, value: Any, field_name: str,
                     max_length: int = 1000,
                     allow_html: bool = False) -> ValidationResult:
        """
        Validate text fields like location, description
        Prevents XSS while preserving legitimate content
        """
        errors = []
        warnings = []
        
        if value is None:
            return ValidationResult(True, "", errors, warnings)
        
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
            return ValidationResult(False, None, errors, warnings)
        
        str_value = value.strip()
        
        # Length validation
        if len(str_value) > max_length:
            errors.append(f"{field_name} too long (max {max_length} characters)")
            return ValidationResult(False, None, errors, warnings)
        
        # Check for SQL injection
        if self._contains_sql_injection(str_value):
            errors.append(f"{field_name} contains potentially malicious SQL content")
            return ValidationResult(False, None, errors, warnings)
        
        # Handle HTML content
        if not allow_html:
            # Check for XSS patterns
            if self._contains_xss(str_value):
                errors.append(f"{field_name} contains potentially malicious HTML content")
                return ValidationResult(False, None, errors, warnings)
            
            # HTML escape for safety
            sanitized = html.escape(str_value)
        else:
            # If HTML is allowed, sanitize it properly
            sanitized = self._sanitize_html(str_value)
        
        if sanitized != str_value and not allow_html:
            warnings.append(f"{field_name} was HTML escaped")
        
        return ValidationResult(True, sanitized, errors, warnings)
    
    def validate_file_path(self, value: Any, base_directory: str) -> ValidationResult:
        """
        Validate file paths to prevent path traversal attacks
        CRITICAL for preventing directory traversal vulnerabilities
        """
        errors = []
        warnings = []
        
        if not isinstance(value, str):
            errors.append("File path must be a string")
            return ValidationResult(False, None, errors, warnings)
        
        str_value = value.strip()
        
        if not str_value:
            errors.append("File path cannot be empty")
            return ValidationResult(False, None, errors, warnings)
        
        # Check for path traversal patterns
        if self._contains_path_traversal(str_value):
            errors.append("File path contains directory traversal attempt")
            return ValidationResult(False, None, errors, warnings)
        
        try:
            # Create safe path
            base_path = Path(base_directory).resolve()
            requested_path = Path(str_value)
            
            # Only use the filename, ignore any directory components
            safe_filename = requested_path.name
            safe_path = base_path / safe_filename
            safe_path = safe_path.resolve()
            
            # Ensure the resolved path is within the base directory
            if not str(safe_path).startswith(str(base_path)):
                errors.append("File path attempts to access outside allowed directory")
                return ValidationResult(False, None, errors, warnings)
            
            # Additional filename validation
            if not self._is_safe_filename(safe_filename):
                errors.append("Filename contains invalid characters")
                return ValidationResult(False, None, errors, warnings)
            
            return ValidationResult(True, safe_path, errors, warnings)
            
        except Exception as e:
            errors.append(f"Path validation failed: {str(e)}")
            return ValidationResult(False, None, errors, warnings)
    
    def validate_energy_data(self, value: Any) -> ValidationResult:
        """
        Validate energy-related data for the energy assessment feature
        Ensures energy calculation inputs are safe and valid
        """
        errors = []
        warnings = []
        
        if not isinstance(value, dict):
            errors.append("Energy data must be a dictionary")
            return ValidationResult(False, None, errors, warnings)
        
        sanitized_data = {}
        
        # Validate energy class
        if 'energy_class' in value:
            energy_class = value['energy_class']
            if isinstance(energy_class, str):
                energy_class = energy_class.strip().upper()
                valid_classes = ['A+', 'A', 'B+', 'B', 'C', 'D', 'E', 'F', 'G']
                if energy_class in valid_classes:
                    sanitized_data['energy_class'] = energy_class
                else:
                    warnings.append(f"Unknown energy class: {energy_class}")
        
        # Validate heating system
        if 'heating_system' in value:
            heating_system = str(value['heating_system']).strip().lower()
            valid_systems = ['oil', 'gas', 'electric', 'heat_pump', 'solar']
            if heating_system in valid_systems:
                sanitized_data['heating_system'] = heating_system
            else:
                warnings.append(f"Unknown heating system: {heating_system}")
        
        # Validate boolean fields
        bool_fields = ['insulation_walls', 'insulation_roof', 'solar_panels']
        for field in bool_fields:
            if field in value:
                if isinstance(value[field], bool):
                    sanitized_data[field] = value[field]
                else:
                    # Try to convert string to boolean
                    str_val = str(value[field]).lower().strip()
                    if str_val in ['true', '1', 'yes']:
                        sanitized_data[field] = True
                    elif str_val in ['false', '0', 'no']:
                        sanitized_data[field] = False
                    else:
                        warnings.append(f"Invalid boolean value for {field}: {value[field]}")
        
        return ValidationResult(True, sanitized_data, errors, warnings)
    
    def validate_property_data(self, property_data: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Comprehensive validation of property data
        Validates all fields with appropriate security measures
        """
        results = {}
        
        # Validate property ID (critical)
        if 'id' in property_data:
            results['id'] = self.validate_property_id(property_data['id'])
        
        # Validate URL
        if 'url' in property_data:
            results['url'] = self.validate_url(property_data['url'])
        
        # Validate numeric fields
        numeric_fields = {
            'price': {'min_value': 1000, 'max_value': 50000000},
            'size': {'min_value': 10, 'max_value': 2000},
            'rooms': {'min_value': 1, 'max_value': 20, 'allow_decimal': False},
            'floor': {'min_value': -5, 'max_value': 50, 'allow_decimal': False},
            'year_built': {'min_value': 1800, 'max_value': 2030, 'allow_decimal': False}
        }
        
        for field, constraints in numeric_fields.items():
            if field in property_data:
                results[field] = self.validate_numeric(
                    property_data[field], field, **constraints
                )
        
        # Validate text fields
        text_fields = ['location', 'description', 'address']
        for field in text_fields:
            if field in property_data:
                results[field] = self.validate_text(property_data[field], field)
        
        # Validate date fields
        if 'listed_date' in property_data:
            results['listed_date'] = self.validate_date(property_data['listed_date'])
        
        # Validate energy data if present
        energy_fields = ['energy_class', 'heating_system', 'insulation_walls', 
                        'insulation_roof', 'solar_panels']
        energy_data = {k: v for k, v in property_data.items() if k in energy_fields}
        if energy_data:
            results['energy_data'] = self.validate_energy_data(energy_data)
        
        return results
    
    def _contains_sql_injection(self, value: str) -> bool:
        """Check if string contains SQL injection patterns"""
        return any(pattern.search(value) for pattern in self.compiled_sql_patterns)
    
    def _contains_xss(self, value: str) -> bool:
        """Check if string contains XSS patterns"""
        return any(pattern.search(value) for pattern in self.compiled_xss_patterns)
    
    def _contains_path_traversal(self, value: str) -> bool:
        """Check if string contains path traversal patterns"""
        return any(pattern.search(value) for pattern in self.compiled_path_patterns)
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""
        if not filename or filename in ['.', '..']:
            return False
        
        # Only allow alphanumeric, dots, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            return False
        
        # Prevent multiple dots (potential bypass)
        if '..' in filename:
            return False
        
        return True
    
    def _sanitize_html(self, html_content: str) -> str:
        """
        Enhanced HTML sanitization using bleach library
        Provides robust protection against XSS attacks
        """
        if BLEACH_AVAILABLE:
            # Use bleach for proper HTML sanitization
            allowed_tags = ['p', 'br', 'strong', 'em', 'u']  # Very restrictive
            allowed_attributes = {}  # No attributes allowed
            allowed_protocols = []  # No protocols allowed
            
            try:
                cleaned = bleach.clean(
                    html_content,
                    tags=allowed_tags,
                    attributes=allowed_attributes,
                    protocols=allowed_protocols,
                    strip=True,  # Strip disallowed tags completely
                    strip_comments=True  # Remove HTML comments
                )
                
                # Additional security check for dangerous patterns
                dangerous_patterns = [
                    r'javascript:',
                    r'vbscript:',
                    r'data:(?!image/)',  # Allow data: only for images
                    r'on\w+\s*=',
                    r'expression\s*\(',
                    r'url\s*\(',
                    r'@import'
                ]
                
                for pattern in dangerous_patterns:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
                
                return cleaned
                
            except Exception:
                # Fallback to HTML escaping if bleach fails
                return html.escape(html_content)
        else:
            # Enhanced manual sanitization fallback
            cleaned = html_content
            
            # Remove dangerous tags completely
            dangerous_tags = [
                r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
                r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>',
                r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>',
                r'<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>',
                r'<embed\b[^>]*>',
                r'<link\b[^>]*>',
                r'<meta\b[^>]*>',
                r'<form\b[^<]*(?:(?!<\/form>)<[^<]*)*<\/form>'
            ]
            
            for pattern in dangerous_tags:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
            # Remove dangerous attributes  
            cleaned = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'src\s*=\s*["\']javascript:[^"\']*["\']', '', cleaned, flags=re.IGNORECASE)
            
            # Remove dangerous protocols
            cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'vbscript:', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'data:(?!image/)', '', cleaned, flags=re.IGNORECASE)
            
            # HTML escape the result for maximum safety
            return html.escape(cleaned)


# Global validator instance
_validator = None


def get_validator() -> InputValidator:
    """Get global validator instance"""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator


def validate_property_data(property_data: Dict[str, Any]) -> Dict[str, ValidationResult]:
    """
    Convenience function for property data validation
    
    Args:
        property_data: Property data dictionary
        
    Returns:
        Validation results for each field
        
    Raises:
        SecurityError: If critical validation fails
    """
    validator = get_validator()
    results = validator.validate_property_data(property_data)
    
    # Check for critical failures
    critical_failures = []
    for field, result in results.items():
        if not result.is_valid and field in ['id', 'url']:  # Critical fields
            critical_failures.append(f"{field}: {', '.join(result.errors)}")
    
    if critical_failures:
        raise SecurityError(f"Critical validation failures: {'; '.join(critical_failures)}")
    
    return results


def sanitize_for_database(value: Any, field_name: str) -> Any:
    """
    Sanitize value for safe database insertion
    
    Args:
        value: Value to sanitize
        field_name: Name of the field (for context)
        
    Returns:
        Sanitized value safe for database insertion
    """
    validator = get_validator()
    
    if isinstance(value, str):
        # Apply appropriate validation based on field name
        if field_name == 'id':
            result = validator.validate_property_id(value)
        elif field_name == 'url':
            result = validator.validate_url(value)
        elif field_name in ['location', 'description', 'address']:
            result = validator.validate_text(value, field_name)
        else:
            result = validator.validate_text(value, field_name, max_length=500)
        
        if not result.is_valid:
            raise SecurityError(f"Cannot sanitize {field_name}: {', '.join(result.errors)}")
        
        return result.sanitized_value
    
    return value