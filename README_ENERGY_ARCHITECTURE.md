# 🏗️ Energy Assessment Architecture Documentation

## Phase 2: Advanced Energy Data Pipeline & ML Integration

This document provides comprehensive technical documentation for the Phase 2 implementation of the ATHintel Energy Assessment System, specifically optimized for the Greek energy market.

## 📋 System Overview

The energy assessment system provides enterprise-grade property energy analysis with:

- **Domain-Driven Design (DDD)** architecture with clear bounded contexts
- **CQRS (Command Query Responsibility Segregation)** for scalable read/write operations
- **ML-enhanced predictions** with Greek building characteristics
- **Real-time processing pipeline** with comprehensive error handling
- **Production-ready security** with authentication and authorization
- **Advanced financial analysis** with Greek subsidy integration

## 🏛️ Architecture Components

### Domain Layer (`src/domains/energy/`)

#### Entities
- **`PropertyEnergyEntity`**: Core business entity with energy assessment logic
- Rich business methods for subsidy eligibility, upgrade priorities, and investment analysis

#### Value Objects
- **`EnergyClass`**: EU energy classes (A+ to G) with Greek market context
- **`FinancialMetrics`**: Comprehensive financial analysis (NPV, IRR, sensitivity)
- **`UpgradeRecommendation`**: Immutable upgrade suggestions with cost-benefit

#### Domain Events
- **`PropertyEnergyAssessed`**: Fired when assessment completes
- **`UpgradeRecommendationGenerated`**: Fired when recommendations created
- **`EnergyMarketDataUpdated`**: Market data change notifications

### Infrastructure Layer (`src/infrastructure/`)

#### CQRS Implementation (`src/infrastructure/cqrs/`)
- **Command Bus**: Handles write operations with security middleware
- **Query Bus**: Handles read operations with caching and performance optimization
- **Comprehensive validation** and error handling for all operations

#### Persistence (`src/infrastructure/persistence/`)
- **Database Manager**: PostgreSQL with connection pooling and query optimization
- **Redis Caching**: Advanced caching with TTL management and performance monitoring

### ML Prediction System (`src/ml/energy_prediction/`)

#### Models
- **`EnergyClassPredictor`**: Multi-class classification for EU energy classes
- **`ConsumptionPredictor`**: Regression for annual energy consumption
- **`ROIPredictor`**: Investment return prediction
- **`ModelEnsemble`**: Combines multiple models for robust predictions

#### Features
- **`BuildingFeatures`**: 33 engineered features for Greek buildings
- **`MarketFeatures`**: Current Greek energy market conditions
- **Comprehensive feature engineering** with normalization and encoding

### Processing Pipeline (`src/pipelines/energy_assessment/`)

#### Pipeline Stages
1. **Data Validation**: Input validation and normalization
2. **Feature Extraction**: ML feature engineering
3. **ML Prediction**: Async prediction with timeout handling
4. **Recommendation Generation**: Upgrade suggestions with Greek subsidies
5. **Report Generation**: Comprehensive assessment reports

#### Real-time Processing
- **`RealTimeAssessmentService`**: Cached assessment service
- **`BatchAssessmentProcessor`**: High-performance batch processing
- **Comprehensive error handling** and performance monitoring

## 🔒 Security Implementation

### Authentication & Authorization
- **JWT-based authentication** with configurable secrets
- **Role-based authorization** for sensitive operations
- **Environment-specific security** (development vs production)

### Security Middleware
- **Command Security**: Validates user authentication for write operations
- **Query Security**: Protects sensitive data access
- **Rate Limiting**: Prevents abuse and ensures fair usage

### Production Security
- **Secure configuration management** with environment variables
- **Database connection security** with SSL support
- **Comprehensive audit logging** for security events

## 📊 Performance & Scalability

### Async Processing
- **Non-blocking ML predictions** using thread pools
- **Concurrent processing** with configurable limits
- **Timeout handling** to prevent resource exhaustion

### Caching Strategy
- **Multi-level caching** with Redis and in-memory caches
- **Smart cache invalidation** based on data freshness
- **Performance monitoring** with detailed metrics

### Database Optimization
- **Connection pooling** with configurable limits
- **Optimized queries** with prepared statements
- **Query performance monitoring** with slow query detection

## 🇬🇷 Greek Market Integration

### Energy Classes
- **EU standard implementation** with Greek building characteristics
- **Local climate zones** (4 zones across Greece)
- **Market context** including typical heating costs and property premiums

### Government Subsidies
- **Εξοικονομώ - Κατ' Οίκον** program integration
- **EU Renovation Wave** eligibility checks
- **Local municipality** subsidy programs

### Market Data
- **Greek energy pricing** (electricity, gas, oil)
- **Regional variations** (Athens, Thessaloniki, islands)
- **Market trend analysis** with forecasting

## 🧪 Testing Strategy

### Unit Tests
- **Domain logic testing** with comprehensive edge cases
- **CQRS infrastructure testing** including security validation
- **Performance testing** with concurrent operations

### Integration Tests
- **End-to-end workflows** from command to query
- **Security enforcement** across all system boundaries
- **Error handling** and recovery scenarios

## 📈 Configuration Management

### Environment Configuration
- **Development**: Relaxed security, enhanced logging
- **Production**: Strict security, performance optimization
- **Configurable limits** for all system resources

### Feature Flags
- **ML predictions**: Enable/disable machine learning
- **Caching**: Control caching behavior
- **Security headers**: Configure security policies

## 🚀 Production Deployment

### Requirements
- **PostgreSQL 12+** with connection pooling
- **Redis 6+** for caching
- **Python 3.11+** with async support
- **Environment variables** for secure configuration

### Monitoring
- **Structured JSON logging** with performance metrics
- **Health check endpoints** for load balancer integration
- **Error tracking** with detailed stack traces

### Performance Targets
- **Assessment latency**: < 2 seconds for real-time requests
- **Batch processing**: > 100 properties/minute
- **Cache hit rate**: > 80% for repeated queries
- **Uptime**: 99.9% availability target

## 📝 API Usage Examples

### Command Execution
```python
from infrastructure.cqrs import get_command_bus, AssessPropertyEnergyCommand
from domains.energy.entities.property_energy import BuildingType, HeatingSystem

# Create assessment command
command = AssessPropertyEnergyCommand(
    property_id="PROP_001",
    building_type=BuildingType.APARTMENT,
    construction_year=1990,
    total_area=Decimal('85'),
    heating_system=HeatingSystem.INDIVIDUAL_GAS,
    use_ml_prediction=True,
    generate_recommendations=True
)
command.issued_by = "user_123"

# Execute command
command_bus = get_command_bus()
result = await command_bus.execute(command)
```

### Query Execution
```python
from infrastructure.cqrs import get_query_bus, GetPropertyEnergyAssessmentQuery

# Create query
query = GetPropertyEnergyAssessmentQuery(
    property_id="PROP_001",
    include_recommendations=True,
    include_market_comparison=True
)
query.requested_by = "user_123"

# Execute query with caching
query_bus = get_query_bus()
result = await query_bus.execute(query, use_cache=True)
```

### Real-time Assessment
```python
from pipelines.energy_assessment import create_realtime_service

# Create service
service = create_realtime_service()

# Assess property
property_data = {
    'property_id': 'PROP_001',
    'construction_year': 1995,
    'total_area': 90.5,
    'building_type': 'apartment',
    'heating_system': 'individual_gas',
    'location': {'region': 'attiki', 'city': 'athens'}
}

result = await service.assess_property_realtime(property_data)
```

## 🔧 Development Setup

### Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: Copy `.env.example` to `.env`
3. Setup database: `python scripts/setup_db.py`
4. Run tests: `pytest tests/ -v`

### Docker Development
```bash
docker-compose up -d postgres redis
python -m pytest tests/ -v
python main.py --environment=development
```

## 📊 Metrics & Monitoring

### Key Metrics
- **Assessment accuracy**: ML prediction confidence scores
- **Processing performance**: Latency percentiles and throughput
- **Error rates**: By component and operation type
- **Cache performance**: Hit rates and memory usage

### Alerting
- **High error rates** (>5% failure rate)
- **Slow responses** (>5 second latency)
- **Resource exhaustion** (CPU/memory/database connections)
- **Security events** (authentication failures, unauthorized access)

## 🔄 Maintenance & Operations

### Regular Tasks
- **Model retraining**: Monthly with latest property data
- **Cache warming**: Pre-populate common queries
- **Performance tuning**: Query optimization and index maintenance
- **Security updates**: Dependencies and configuration review

### Troubleshooting
- **High latency**: Check database connection pool and ML prediction timeout
- **Cache misses**: Verify Redis connectivity and TTL configuration
- **Authentication errors**: Validate JWT configuration and user permissions
- **ML prediction failures**: Check model files and fallback mechanisms

---

*This documentation covers the core Phase 2 implementation. For deployment guides, see `DEPLOYMENT.md`. For API reference, see `API_REFERENCE.md`.*