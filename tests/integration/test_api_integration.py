"""
API Integration Testing Suite for ATHintel Platform
Tests API endpoints, data flow, and system integration
"""

import pytest
import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.secure_energy_endpoints import EnergyAssessmentAPI
from src.api.investment_endpoints import InvestmentAPI
from src.api.property_endpoints import PropertyAPI
from src.core.domain.entities import Property, PropertyType, EnergyClass, ListingType, Location


class APITestClient:
    """Test client for API integration testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with API and store token"""
        async with self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data.get("access_token")
                return True
            return False
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> aiohttp.ClientResponse:
        """Make GET request"""
        return await self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self.auth_headers
        )
    
    async def post(self, endpoint: str, data: Optional[Dict] = None) -> aiohttp.ClientResponse:
        """Make POST request"""
        return await self.session.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=self.auth_headers
        )
    
    async def put(self, endpoint: str, data: Optional[Dict] = None) -> aiohttp.ClientResponse:
        """Make PUT request"""
        return await self.session.put(
            f"{self.base_url}{endpoint}",
            json=data,
            headers=self.auth_headers
        )
    
    async def delete(self, endpoint: str) -> aiohttp.ClientResponse:
        """Make DELETE request"""
        return await self.session.delete(
            f"{self.base_url}{endpoint}",
            headers=self.auth_headers
        )


class TestPropertyAPIIntegration:
    """Integration tests for Property API endpoints"""

    @pytest.fixture
    async def api_client(self):
        """API test client"""
        async with APITestClient() as client:
            # Mock authentication for testing
            client.auth_token = "test_token_12345"
            yield client

    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for API testing"""
        return {
            "property_id": "test_prop_123",
            "url": "https://spitogatos.gr/property/123",
            "title": "Beautiful Apartment in Kolonaki",
            "property_type": "apartment",
            "listing_type": "sale",
            "location": {
                "neighborhood": "Kolonaki",
                "district": "Athens Center",
                "municipality": "Athens"
            },
            "price": 350000,
            "sqm": 85.0,
            "rooms": 3,
            "floor": 2,
            "energy_class": "B",
            "year_built": 2010,
            "description": "Modern apartment with excellent location"
        }

    async def test_create_property_endpoint(self, api_client, sample_property_data):
        """Test property creation endpoint"""
        
        # Mock the API endpoint
        with patch('src.api.property_endpoints.PropertyAPI.create_property') as mock_create:
            mock_create.return_value = {
                **sample_property_data,
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            
            response = await api_client.post("/api/v1/properties", sample_property_data)
            
            assert response.status == 201
            
            data = await response.json()
            assert data["property_id"] == sample_property_data["property_id"]
            assert data["status"] == "created"
            assert "created_at" in data

    async def test_get_property_endpoint(self, api_client, sample_property_data):
        """Test property retrieval endpoint"""
        
        property_id = sample_property_data["property_id"]
        
        with patch('src.api.property_endpoints.PropertyAPI.get_property') as mock_get:
            mock_get.return_value = sample_property_data
            
            response = await api_client.get(f"/api/v1/properties/{property_id}")
            
            assert response.status == 200
            
            data = await response.json()
            assert data["property_id"] == property_id
            assert data["title"] == sample_property_data["title"]

    async def test_search_properties_endpoint(self, api_client):
        """Test property search endpoint"""
        
        search_params = {
            "neighborhood": "Kolonaki",
            "min_price": 200000,
            "max_price": 500000,
            "property_type": "apartment"
        }
        
        mock_results = [
            {
                "property_id": "prop_1",
                "title": "Property 1",
                "price": 300000,
                "location": {"neighborhood": "Kolonaki"}
            },
            {
                "property_id": "prop_2", 
                "title": "Property 2",
                "price": 400000,
                "location": {"neighborhood": "Kolonaki"}
            }
        ]
        
        with patch('src.api.property_endpoints.PropertyAPI.search_properties') as mock_search:
            mock_search.return_value = {
                "results": mock_results,
                "total_count": len(mock_results),
                "page": 1,
                "page_size": 20
            }
            
            response = await api_client.get("/api/v1/properties/search", search_params)
            
            assert response.status == 200
            
            data = await response.json()
            assert len(data["results"]) == 2
            assert data["total_count"] == 2
            
            # Verify results match search criteria
            for result in data["results"]:
                assert result["location"]["neighborhood"] == "Kolonaki"
                assert search_params["min_price"] <= result["price"] <= search_params["max_price"]

    async def test_update_property_endpoint(self, api_client, sample_property_data):
        """Test property update endpoint"""
        
        property_id = sample_property_data["property_id"]
        update_data = {
            "price": 375000,
            "description": "Updated description with new features"
        }
        
        with patch('src.api.property_endpoints.PropertyAPI.update_property') as mock_update:
            updated_property = {**sample_property_data, **update_data}
            updated_property["updated_at"] = datetime.now().isoformat()
            mock_update.return_value = updated_property
            
            response = await api_client.put(f"/api/v1/properties/{property_id}", update_data)
            
            assert response.status == 200
            
            data = await response.json()
            assert data["price"] == update_data["price"]
            assert data["description"] == update_data["description"]
            assert "updated_at" in data

    async def test_delete_property_endpoint(self, api_client, sample_property_data):
        """Test property deletion endpoint"""
        
        property_id = sample_property_data["property_id"]
        
        with patch('src.api.property_endpoints.PropertyAPI.delete_property') as mock_delete:
            mock_delete.return_value = {"status": "deleted", "property_id": property_id}
            
            response = await api_client.delete(f"/api/v1/properties/{property_id}")
            
            assert response.status == 200
            
            data = await response.json()
            assert data["status"] == "deleted"
            assert data["property_id"] == property_id

    async def test_property_validation_errors(self, api_client):
        """Test property API validation error handling"""
        
        invalid_property_data = {
            "property_id": "",  # Empty ID
            "price": -1000,     # Negative price
            "sqm": "not_a_number",  # Invalid type
            "url": "not_a_valid_url"  # Invalid URL
        }
        
        response = await api_client.post("/api/v1/properties", invalid_property_data)
        
        # Should return validation error
        assert response.status == 400
        
        error_data = await response.json()
        assert "error" in error_data
        assert "validation" in error_data["error"]["message"].lower()

    async def test_property_not_found_error(self, api_client):
        """Test property not found error handling"""
        
        non_existent_id = "non_existent_property_123"
        
        with patch('src.api.property_endpoints.PropertyAPI.get_property') as mock_get:
            mock_get.return_value = None
            
            response = await api_client.get(f"/api/v1/properties/{non_existent_id}")
            
            assert response.status == 404
            
            error_data = await response.json()
            assert "error" in error_data
            assert "not found" in error_data["error"]["message"].lower()

    async def test_property_api_authentication(self, api_client):
        """Test property API authentication requirements"""
        
        # Remove auth token
        api_client.auth_token = None
        
        response = await api_client.get("/api/v1/properties/test_123")
        
        # Should require authentication
        assert response.status == 401
        
        error_data = await response.json()
        assert "error" in error_data
        assert "authentication" in error_data["error"]["message"].lower()

    async def test_property_batch_operations(self, api_client):
        """Test property batch operations"""
        
        batch_property_data = [
            {"property_id": "batch_1", "title": "Batch Property 1", "price": 200000},
            {"property_id": "batch_2", "title": "Batch Property 2", "price": 300000},
            {"property_id": "batch_3", "title": "Batch Property 3", "price": 250000}
        ]
        
        with patch('src.api.property_endpoints.PropertyAPI.create_properties_batch') as mock_batch:
            mock_batch.return_value = {
                "created_count": len(batch_property_data),
                "properties": [
                    {**prop, "status": "created", "created_at": datetime.now().isoformat()}
                    for prop in batch_property_data
                ]
            }
            
            response = await api_client.post("/api/v1/properties/batch", {
                "properties": batch_property_data
            })
            
            assert response.status == 201
            
            data = await response.json()
            assert data["created_count"] == 3
            assert len(data["properties"]) == 3


class TestEnergyAssessmentAPIIntegration:
    """Integration tests for Energy Assessment API endpoints"""

    @pytest.fixture
    async def api_client(self):
        """API test client"""
        async with APITestClient() as client:
            client.auth_token = "test_token_12345"
            yield client

    @pytest.fixture
    def sample_energy_assessment_request(self):
        """Sample energy assessment request"""
        return {
            "property_id": "test_prop_123",
            "property_data": {
                "sqm": 85.0,
                "year_built": 2010,
                "energy_class": "C",
                "heating_system": "gas",
                "insulation_walls": False,
                "insulation_roof": True,
                "solar_panels": False,
                "windows_type": "double_glazed",
                "orientation": "south",
                "floor": 3
            }
        }

    async def test_energy_assessment_endpoint(self, api_client, sample_energy_assessment_request):
        """Test energy assessment endpoint"""
        
        mock_assessment_result = {
            "property_id": sample_energy_assessment_request["property_id"],
            "current_energy_class": "C",
            "efficiency_score": 65.5,
            "annual_energy_cost": 1200,
            "co2_emissions": 2.8,
            "assessment_date": datetime.now().isoformat(),
            "recommendations": [
                {
                    "improvement_type": "wall_insulation",
                    "estimated_cost": 8000,
                    "annual_savings": 300,
                    "payback_period": 26.7,
                    "energy_class_improvement": "B"
                }
            ]
        }
        
        with patch('src.api.secure_energy_endpoints.EnergyAssessmentAPI.assess_property_energy') as mock_assess:
            mock_assess.return_value = mock_assessment_result
            
            response = await api_client.post(
                "/api/v1/energy/assess",
                sample_energy_assessment_request
            )
            
            assert response.status == 200
            
            data = await response.json()
            assert data["property_id"] == sample_energy_assessment_request["property_id"]
            assert data["current_energy_class"] == "C"
            assert data["efficiency_score"] == 65.5
            assert len(data["recommendations"]) > 0

    async def test_energy_certificate_generation(self, api_client, sample_energy_assessment_request):
        """Test energy certificate generation endpoint"""
        
        mock_certificate = {
            "certificate_id": "cert_123456",
            "property_id": sample_energy_assessment_request["property_id"],
            "energy_class": "C",
            "efficiency_rating": 65.5,
            "annual_consumption": 180.5,  # kWh/m²
            "co2_emissions": 2.8,
            "certificate_date": datetime.now().isoformat(),
            "valid_until": "2034-01-01T00:00:00",
            "assessor_id": "assessor_001",
            "certificate_url": "https://certificates.athintel.com/cert_123456.pdf"
        }
        
        with patch('src.api.secure_energy_endpoints.EnergyAssessmentAPI.generate_certificate') as mock_cert:
            mock_cert.return_value = mock_certificate
            
            response = await api_client.post(
                "/api/v1/energy/certificate",
                sample_energy_assessment_request
            )
            
            assert response.status == 201
            
            data = await response.json()
            assert data["certificate_id"] == "cert_123456"
            assert data["property_id"] == sample_energy_assessment_request["property_id"]
            assert data["valid_until"] == "2034-01-01T00:00:00"
            assert "certificate_url" in data

    async def test_energy_improvement_recommendations(self, api_client):
        """Test energy improvement recommendations endpoint"""
        
        property_id = "test_prop_123"
        
        mock_recommendations = [
            {
                "improvement_type": "wall_insulation",
                "priority": "high",
                "estimated_cost": 8000,
                "annual_savings": 300,
                "payback_period": 26.7,
                "energy_class_improvement": "B",
                "co2_reduction": 0.8,
                "description": "Install wall insulation to improve energy efficiency"
            },
            {
                "improvement_type": "solar_panels",
                "priority": "medium",
                "estimated_cost": 12000,
                "annual_savings": 500,
                "payback_period": 24.0,
                "energy_class_improvement": "A",
                "co2_reduction": 1.2,
                "description": "Install solar panel system for renewable energy"
            }
        ]
        
        with patch('src.api.secure_energy_endpoints.EnergyAssessmentAPI.get_improvement_recommendations') as mock_recs:
            mock_recs.return_value = {
                "property_id": property_id,
                "recommendations": mock_recommendations,
                "total_improvements": len(mock_recommendations)
            }
            
            response = await api_client.get(f"/api/v1/energy/recommendations/{property_id}")
            
            assert response.status == 200
            
            data = await response.json()
            assert len(data["recommendations"]) == 2
            assert data["total_improvements"] == 2
            
            # Verify recommendations are sorted by priority/payback period
            first_rec = data["recommendations"][0]
            assert first_rec["priority"] == "high"
            assert first_rec["payback_period"] < 30

    async def test_energy_comparison_endpoint(self, api_client):
        """Test energy comparison between properties"""
        
        comparison_request = {
            "properties": [
                {
                    "property_id": "prop_1",
                    "sqm": 85,
                    "energy_class": "C",
                    "year_built": 2010
                },
                {
                    "property_id": "prop_2", 
                    "sqm": 90,
                    "energy_class": "B",
                    "year_built": 2015
                }
            ]
        }
        
        mock_comparison = {
            "comparison_id": "comp_123",
            "properties": [
                {
                    "property_id": "prop_1",
                    "efficiency_score": 65.5,
                    "annual_cost": 1200,
                    "ranking": 2
                },
                {
                    "property_id": "prop_2",
                    "efficiency_score": 78.2,
                    "annual_cost": 950,
                    "ranking": 1
                }
            ],
            "winner": "prop_2",
            "cost_difference": 250,
            "efficiency_difference": 12.7
        }
        
        with patch('src.api.secure_energy_endpoints.EnergyAssessmentAPI.compare_properties') as mock_compare:
            mock_compare.return_value = mock_comparison
            
            response = await api_client.post("/api/v1/energy/compare", comparison_request)
            
            assert response.status == 200
            
            data = await response.json()
            assert data["winner"] == "prop_2"
            assert data["cost_difference"] == 250
            assert len(data["properties"]) == 2

    async def test_energy_assessment_validation(self, api_client):
        """Test energy assessment input validation"""
        
        invalid_request = {
            "property_id": "",  # Empty ID
            "property_data": {
                "sqm": -50,  # Negative area
                "year_built": 1800,  # Too old
                "energy_class": "Z",  # Invalid class
                "heating_system": "invalid_system"
            }
        }
        
        response = await api_client.post("/api/v1/energy/assess", invalid_request)
        
        assert response.status == 400
        
        error_data = await response.json()
        assert "error" in error_data
        assert "validation" in error_data["error"]["category"]

    async def test_energy_assessment_security(self, api_client):
        """Test energy assessment API security"""
        
        # Test without authentication
        api_client.auth_token = None
        
        response = await api_client.post("/api/v1/energy/assess", {})
        
        assert response.status == 401
        
        # Test with malicious input
        api_client.auth_token = "test_token_12345"
        
        malicious_request = {
            "property_id": "'; DROP TABLE properties; --",
            "property_data": {
                "sqm": "<script>alert('xss')</script>",
                "description": "../../etc/passwd"
            }
        }
        
        response = await api_client.post("/api/v1/energy/assess", malicious_request)
        
        # Should reject malicious input
        assert response.status == 400
        
        error_data = await response.json()
        assert "error" in error_data


class TestInvestmentAPIIntegration:
    """Integration tests for Investment API endpoints"""

    @pytest.fixture
    async def api_client(self):
        """API test client"""
        async with APITestClient() as client:
            client.auth_token = "test_token_12345"
            yield client

    @pytest.fixture
    def sample_investment_request(self):
        """Sample investment analysis request"""
        return {
            "property_id": "test_prop_123",
            "analysis_type": "comprehensive",
            "investment_parameters": {
                "down_payment_percent": 20,
                "loan_term_years": 25,
                "interest_rate": 3.5,
                "target_yield": 5.0,
                "holding_period": 10
            }
        }

    async def test_investment_analysis_endpoint(self, api_client, sample_investment_request):
        """Test investment analysis endpoint"""
        
        mock_analysis = {
            "property_id": sample_investment_request["property_id"],
            "investment_score": 78.5,
            "estimated_rental_yield": 4.2,
            "roi_projection_5y": 45.8,
            "risk_level": "medium",
            "total_investment_needed": 385000,
            "cash_flow_projection": [5000, 5200, 5400, 5600, 5800],
            "strengths": ["Good location", "Strong rental demand"],
            "weaknesses": ["Older building", "Higher maintenance costs"],
            "recommendation": "Consider purchase with energy improvements"
        }
        
        with patch('src.api.investment_endpoints.InvestmentAPI.analyze_investment') as mock_analyze:
            mock_analyze.return_value = mock_analysis
            
            response = await api_client.post(
                "/api/v1/investment/analyze",
                sample_investment_request
            )
            
            assert response.status == 200
            
            data = await response.json()
            assert data["property_id"] == sample_investment_request["property_id"]
            assert data["investment_score"] == 78.5
            assert len(data["cash_flow_projection"]) == 5
            assert len(data["strengths"]) > 0

    async def test_portfolio_optimization_endpoint(self, api_client):
        """Test portfolio optimization endpoint"""
        
        optimization_request = {
            "budget": 1000000,
            "max_properties": 5,
            "risk_tolerance": "moderate",
            "target_return": 6.0,
            "diversification_requirements": {
                "max_per_neighborhood": 0.4,
                "min_property_types": 2
            },
            "candidate_properties": ["prop_1", "prop_2", "prop_3", "prop_4", "prop_5", "prop_6"]
        }
        
        mock_optimized_portfolio = {
            "portfolio_id": "port_123",
            "total_value": 950000,
            "selected_properties": [
                {
                    "property_id": "prop_1",
                    "investment_score": 85.2,
                    "allocation_percent": 30.0,
                    "expected_yield": 5.8
                },
                {
                    "property_id": "prop_3",
                    "investment_score": 78.9,
                    "allocation_percent": 35.0,
                    "expected_yield": 6.2
                },
                {
                    "property_id": "prop_5",
                    "investment_score": 72.1,
                    "allocation_percent": 35.0,
                    "expected_yield": 5.5
                }
            ],
            "portfolio_metrics": {
                "weighted_avg_yield": 5.8,
                "portfolio_risk_score": 65.2,
                "diversification_score": 0.82,
                "expected_annual_return": 58000
            }
        }
        
        with patch('src.api.investment_endpoints.InvestmentAPI.optimize_portfolio') as mock_optimize:
            mock_optimize.return_value = mock_optimized_portfolio
            
            response = await api_client.post(
                "/api/v1/investment/portfolio/optimize",
                optimization_request
            )
            
            assert response.status == 200
            
            data = await response.json()
            assert data["total_value"] <= optimization_request["budget"]
            assert len(data["selected_properties"]) <= optimization_request["max_properties"]
            assert data["portfolio_metrics"]["weighted_avg_yield"] >= optimization_request["target_return"]

    async def test_investment_comparison_endpoint(self, api_client):
        """Test investment comparison endpoint"""
        
        comparison_request = {
            "properties": ["prop_1", "prop_2"],
            "comparison_criteria": [
                "investment_score",
                "rental_yield",
                "roi_projection",
                "risk_level"
            ]
        }
        
        mock_comparison = {
            "comparison_id": "comp_inv_123",
            "properties": [
                {
                    "property_id": "prop_1",
                    "investment_score": 78.5,
                    "rental_yield": 4.2,
                    "roi_projection_5y": 45.8,
                    "risk_level": "medium",
                    "ranking": 1
                },
                {
                    "property_id": "prop_2",
                    "investment_score": 72.1,
                    "rental_yield": 3.8,
                    "roi_projection_5y": 38.2,
                    "risk_level": "low",
                    "ranking": 2
                }
            ],
            "winner": "prop_1",
            "win_factors": ["Higher investment score", "Better rental yield"],
            "summary": "Property 1 offers better returns despite slightly higher risk"
        }
        
        with patch('src.api.investment_endpoints.InvestmentAPI.compare_investments') as mock_compare:
            mock_compare.return_value = mock_comparison
            
            response = await api_client.post(
                "/api/v1/investment/compare",
                comparison_request
            )
            
            assert response.status == 200
            
            data = await response.json()
            assert data["winner"] == "prop_1"
            assert len(data["properties"]) == 2
            assert len(data["win_factors"]) > 0

    async def test_investment_report_generation(self, api_client):
        """Test investment report generation endpoint"""
        
        report_request = {
            "property_id": "test_prop_123",
            "report_type": "detailed",
            "include_sections": [
                "executive_summary",
                "financial_analysis",
                "market_analysis",
                "risk_assessment",
                "recommendations"
            ]
        }
        
        mock_report = {
            "report_id": "report_123",
            "property_id": report_request["property_id"],
            "generated_at": datetime.now().isoformat(),
            "report_url": "https://reports.athintel.com/report_123.pdf",
            "sections": {
                "executive_summary": "Strong investment opportunity with moderate risk...",
                "financial_analysis": "Expected ROI of 45.8% over 5 years...",
                "market_analysis": "Kolonaki market shows strong fundamentals...",
                "risk_assessment": "Medium risk profile with main concerns...",
                "recommendations": "Proceed with investment, consider energy improvements..."
            }
        }
        
        with patch('src.api.investment_endpoints.InvestmentAPI.generate_report') as mock_report_gen:
            mock_report_gen.return_value = mock_report
            
            response = await api_client.post(
                "/api/v1/investment/report",
                report_request
            )
            
            assert response.status == 201
            
            data = await response.json()
            assert data["report_id"] == "report_123"
            assert "report_url" in data
            assert len(data["sections"]) == len(report_request["include_sections"])

    async def test_investment_api_rate_limiting(self, api_client):
        """Test investment API rate limiting"""
        
        # Make multiple rapid requests
        requests_made = 0
        rate_limited_responses = 0
        
        for i in range(20):  # Exceed rate limit
            response = await api_client.post("/api/v1/investment/analyze", {
                "property_id": f"test_{i}",
                "analysis_type": "basic"
            })
            
            requests_made += 1
            
            if response.status == 429:  # Too Many Requests
                rate_limited_responses += 1
        
        # Should have some rate limited responses
        assert rate_limited_responses > 0, "Rate limiting should be enforced"
        
        # Rate limit response should include retry information
        if rate_limited_responses > 0:
            # Make one more request to test rate limit response
            response = await api_client.post("/api/v1/investment/analyze", {"property_id": "test"})
            if response.status == 429:
                headers = response.headers
                assert "Retry-After" in headers or "X-RateLimit-Reset" in headers


class TestAPIErrorHandling:
    """Test API error handling and resilience"""

    @pytest.fixture
    async def api_client(self):
        """API test client"""
        async with APITestClient() as client:
            client.auth_token = "test_token_12345"
            yield client

    async def test_api_timeout_handling(self, api_client):
        """Test API timeout handling"""
        
        # Mock a slow service that times out
        with patch('src.api.property_endpoints.PropertyAPI.get_property') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Request timeout")
            
            response = await api_client.get("/api/v1/properties/slow_prop_123")
            
            assert response.status == 504  # Gateway Timeout
            
            error_data = await response.json()
            assert "error" in error_data
            assert "timeout" in error_data["error"]["message"].lower()

    async def test_api_service_unavailable_handling(self, api_client):
        """Test API service unavailable handling"""
        
        with patch('src.api.property_endpoints.PropertyAPI.search_properties') as mock_search:
            mock_search.side_effect = ConnectionError("Service unavailable")
            
            response = await api_client.get("/api/v1/properties/search")
            
            assert response.status == 503  # Service Unavailable
            
            error_data = await response.json()
            assert "error" in error_data
            assert "temporarily unavailable" in error_data["error"]["message"].lower()

    async def test_api_circuit_breaker_integration(self, api_client):
        """Test API integration with circuit breaker patterns"""
        
        # Simulate service failures to trigger circuit breaker
        failure_responses = []
        
        with patch('src.api.investment_endpoints.InvestmentAPI.analyze_investment') as mock_analyze:
            mock_analyze.side_effect = Exception("Service failure")
            
            # Make multiple requests to trigger circuit breaker
            for i in range(5):
                response = await api_client.post("/api/v1/investment/analyze", {
                    "property_id": f"test_{i}"
                })
                failure_responses.append(response.status)
            
            # Should eventually return circuit breaker error (503)
            assert 503 in failure_responses, "Circuit breaker should eventually open"

    async def test_api_graceful_degradation(self, api_client):
        """Test API graceful degradation when services are down"""
        
        # Mock primary service failure but fallback success
        with patch('src.api.property_endpoints.PropertyAPI.get_property') as mock_get:
            # Primary service fails
            mock_get.side_effect = Exception("Primary service down")
            
            # But API returns cached/fallback data
            with patch('src.api.property_endpoints.PropertyAPI.get_property_fallback') as mock_fallback:
                mock_fallback.return_value = {
                    "property_id": "test_123",
                    "title": "Cached Property Data",
                    "status": "limited_data",
                    "data_source": "cache"
                }
                
                response = await api_client.get("/api/v1/properties/test_123")
                
                # Should succeed with degraded data
                assert response.status == 200
                
                data = await response.json()
                assert data["status"] == "limited_data"
                assert data["data_source"] == "cache"

    async def test_api_data_consistency_validation(self, api_client):
        """Test API data consistency validation"""
        
        inconsistent_data = {
            "property_id": "test_123",
            "price": 300000,
            "sqm": 85,
            "rooms": 3,
            # Inconsistent: luxury neighborhood but low price per sqm
            "location": {"neighborhood": "Kolonaki"},  # Premium area
            "price_per_sqm": 1000  # Very low for Kolonaki
        }
        
        response = await api_client.post("/api/v1/properties", inconsistent_data)
        
        # Should flag data consistency issues
        if response.status == 200:
            data = await response.json()
            # Should include warnings about data consistency
            assert "warnings" in data or "data_quality_flags" in data
        else:
            # Or reject with validation error
            assert response.status == 400


class TestAPIPerformance:
    """Test API performance characteristics"""

    @pytest.fixture
    async def api_client(self):
        """API test client"""
        async with APITestClient() as client:
            client.auth_token = "test_token_12345"
            yield client

    async def test_api_response_times(self, api_client):
        """Test API response time requirements"""
        
        import time
        
        endpoints_to_test = [
            ("/api/v1/properties/test_123", "GET"),
            ("/api/v1/energy/assess", "POST"),
            ("/api/v1/investment/analyze", "POST")
        ]
        
        for endpoint, method in endpoints_to_test:
            start_time = time.perf_counter()
            
            if method == "GET":
                response = await api_client.get(endpoint)
            else:
                response = await api_client.post(endpoint, {"property_id": "test_123"})
            
            elapsed = time.perf_counter() - start_time
            
            # API responses should be fast (under 2 seconds)
            assert elapsed < 2.0, f"API response too slow: {endpoint} took {elapsed:.3f}s"
            
            # Status should be reasonable (not necessarily 200 due to mocking)
            assert response.status < 500, f"Server error for {endpoint}: {response.status}"

    async def test_api_concurrent_requests(self, api_client):
        """Test API handling of concurrent requests"""
        
        import asyncio
        
        async def make_request(request_id: int):
            """Make a single API request"""
            response = await api_client.get(f"/api/v1/properties/concurrent_test_{request_id}")
            return response.status
        
        # Make 10 concurrent requests
        concurrent_requests = 10
        tasks = [make_request(i) for i in range(concurrent_requests)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.perf_counter() - start_time
        
        # Should handle concurrent requests efficiently
        assert elapsed < 5.0, f"Concurrent requests took too long: {elapsed:.3f}s"
        
        # Most requests should succeed (or fail gracefully)
        success_count = sum(1 for r in results if not isinstance(r, Exception) and r < 500)
        success_rate = (success_count / concurrent_requests) * 100
        
        assert success_rate > 80, f"Low success rate for concurrent requests: {success_rate:.1f}%"

    @pytest.mark.slow
    async def test_api_sustained_load(self, api_client):
        """Test API under sustained load"""
        
        import time
        
        # Run for 30 seconds
        test_duration = 30
        start_time = time.time()
        request_count = 0
        error_count = 0
        
        while time.time() - start_time < test_duration:
            try:
                response = await api_client.get(f"/api/v1/properties/load_test_{request_count}")
                request_count += 1
                
                if response.status >= 500:
                    error_count += 1
                    
            except Exception:
                error_count += 1
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        # Calculate metrics
        requests_per_second = request_count / test_duration
        error_rate = (error_count / request_count) * 100 if request_count > 0 else 100
        
        # Performance assertions
        assert requests_per_second > 5, f"Low throughput: {requests_per_second:.2f} req/sec"
        assert error_rate < 10, f"High error rate under load: {error_rate:.1f}%"