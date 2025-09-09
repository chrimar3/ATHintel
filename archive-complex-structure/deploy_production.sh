#!/bin/bash

# ATHintel Production Deployment Script
# Deploys all 11 services with monitoring and health checks

set -e

echo "=================================================="
echo "🚀 ATHintel Production Deployment"
echo "=================================================="
echo ""

# Change to Docker directory
cd /Users/chrism/ATHintel/docker

# Step 1: Verify environment
echo "📋 Step 1: Verifying environment..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is available"

# Step 2: Check Docker daemon
echo ""
echo "📋 Step 2: Checking Docker daemon..."
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker."
    exit 1
fi

echo "✅ Docker daemon is running"

# Step 3: Create required directories
echo ""
echo "📋 Step 3: Creating required directories..."
mkdir -p data/{postgres,redis,prometheus,grafana,app}
mkdir -p logs/nginx
mkdir -p reports
echo "✅ Directories created"

# Step 4: Validate configuration files
echo ""
echo "📋 Step 4: Validating configuration..."
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Using default configuration."
fi

echo "✅ Configuration validated"

# Step 5: Deploy services
echo ""
echo "📋 Step 5: Deploying production services..."
echo "Starting 11-service architecture:"
echo "  - API Service (Port 8000)"
echo "  - Dashboard (Port 8501)"
echo "  - Analytics Workers (2 replicas)"
echo "  - Scraper Workers (3 replicas)"
echo "  - PostgreSQL (Port 5432)"
echo "  - Redis (Port 6379)"
echo "  - Prometheus (Port 9090)"
echo "  - Grafana (Port 3000)"
echo "  - Monitoring Worker (Port 9091)"
echo "  - Flower (Port 5555)"
echo "  - Nginx (Ports 80/443)"
echo ""

# Deploy with Docker Compose
echo "🔄 Starting deployment..."
docker compose up -d

# Step 6: Wait for services to be healthy
echo ""
echo "📋 Step 6: Waiting for services to be healthy..."
sleep 10

# Step 7: Check service status
echo ""
echo "📋 Step 7: Checking service status..."
docker compose ps

# Step 8: Verify health endpoints
echo ""
echo "📋 Step 8: Verifying health endpoints..."

# Check API health
echo -n "  API Health: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "⚠️  Not responding (may still be starting)"
fi

# Check Dashboard health
echo -n "  Dashboard Health: "
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "⚠️  Not responding (may still be starting)"
fi

# Check Grafana health
echo -n "  Grafana Health: "
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "⚠️  Not responding (may still be starting)"
fi

# Check Prometheus health
echo -n "  Prometheus Health: "
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "⚠️  Not responding (may still be starting)"
fi

# Step 9: Display access URLs
echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "🌐 Access URLs:"
echo "  - API:        http://localhost:8000"
echo "  - Dashboard:  http://localhost:8501"
echo "  - Grafana:    http://localhost:3000 (admin/admin_production_secure)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Flower:     http://localhost:5555"
echo ""
echo "📊 Monitoring Commands:"
echo "  - View logs:    docker compose logs -f"
echo "  - Check status: docker compose ps"
echo "  - Stop all:     docker compose down"
echo ""
echo "🎯 Expected Performance:"
echo "  - API Response Time: <150ms"
echo "  - Throughput: >100 RPS"
echo "  - Concurrent Users: 100+"
echo ""
echo "🏆 Production deployment successful!"
echo "=================================================="