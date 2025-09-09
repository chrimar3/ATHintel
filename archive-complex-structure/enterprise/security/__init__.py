"""
Enterprise Security Framework
============================

Comprehensive enterprise-grade security and compliance features including:
- Multi-factor authentication and SSO integration
- Role-based access control (RBAC) with fine-grained permissions
- End-to-end data encryption for data in transit and at rest
- Comprehensive audit logging and compliance monitoring
- Real-time threat detection and security monitoring
- GDPR, ISO 27001, and SOC 2 compliance frameworks
"""

from .authentication import AuthenticationEngine
from .authorization import AuthorizationEngine
from .data_encryption import DataEncryptionEngine
from .audit_logging import AuditLoggingEngine
from .compliance_monitoring import ComplianceMonitoringEngine
from .threat_detection import ThreatDetectionEngine

class EnterpriseSecurityFramework:
    """
    Main orchestrator for all enterprise security and compliance features.
    """
    
    def __init__(self):
        self.authentication = AuthenticationEngine()
        self.authorization = AuthorizationEngine()
        self.data_encryption = DataEncryptionEngine()
        self.audit_logging = AuditLoggingEngine()
        self.compliance_monitoring = ComplianceMonitoringEngine()
        self.threat_detection = ThreatDetectionEngine()
    
    def initialize_security_framework(self, security_config):
        """Initialize complete enterprise security framework."""
        
        results = {
            'authentication_setup': self.authentication.setup_authentication(security_config),
            'authorization_setup': self.authorization.setup_rbac(security_config),
            'encryption_setup': self.data_encryption.setup_encryption(security_config),
            'audit_setup': self.audit_logging.setup_audit_logging(security_config),
            'compliance_setup': self.compliance_monitoring.setup_compliance_monitoring(security_config),
            'threat_detection_setup': self.threat_detection.setup_threat_detection(security_config)
        }
        
        return results

__all__ = [
    'EnterpriseSecurityFramework',
    'AuthenticationEngine',
    'AuthorizationEngine',
    'DataEncryptionEngine',
    'AuditLoggingEngine',
    'ComplianceMonitoringEngine',
    'ThreatDetectionEngine'
]