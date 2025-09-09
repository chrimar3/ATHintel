"""
Adapters Layer - Hexagonal Architecture External Integrations

This layer implements the ports (interfaces) defined in the core layer,
connecting our business logic to external systems and services.
"""

from .scrapers import *
# from .repositories import *  # Not implemented yet
# from .services import *  # Not implemented yet

__all__ = [
    "CrawleePropertyScraper",
    "PlaywrightAdvancedScraper",
    "PostgreSQLPropertyRepository",
    "RedisCache",
    "PrometheusMonitoring",
]