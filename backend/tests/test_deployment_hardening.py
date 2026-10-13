"""
Phase 5 Workstream 3: Deployment Reliability, Configuration Audit, and Hardening Tests.

Validates:
1. Health check endpoints: /health, /api/health, and /api/status.
2. Configuration & secrets hygiene: .env.example contains only safe placeholders; .gitignore blocks .env.
3. Cold-start dependency resilience: auth JWT creation, decoding, expiration, and role permissions.
4. External API resilience: copilot behavior when GEMINI_API_KEY is missing, invalid, or timing out.
5. Robust input validation and HTTP error handling across core endpoints.
"""

import os
import sys
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import app
from engine.auth import (
    create_access_token,
    decode_access_token,
    require_permission,
    ROLE_PERMISSIONS
)
from fastapi import HTTPException

client = TestClient(app)


class TestHealthChecksAndRouting:
    """Verifies that standard and legacy health check routes exist and return healthy status."""

    def test_health_root_endpoint(self):
        """Verify /health returns 200 with 'status': 'healthy'."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "dataset_rows" in data
        assert isinstance(data["columns"], list)

    def test_api_health_endpoint(self):
        """Verify /api/health returns 200 with identical schema for standard ingress/k8s probes."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "dataset_rows" in data

    def test_api_status_backwards_compatibility(self):
        """Verify /api/status continues to function for existing frontend controllers."""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestSecretsAndConfigurationHygiene:
    """Ensures configuration template exists and contains no leaked credentials."""

    def test_env_example_exists_and_clean(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        env_example_path = os.path.join(repo_root, ".env.example")
        assert os.path.exists(env_example_path), ".env.example file must exist in repository root."

        with open(env_example_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Must define essential variables
        required_vars = ["PRAGATI_ENV", "PRAGATI_API_KEY", "JWT_SECRET_KEY", "GEMINI_API_KEY", "DATABASE_URL"]
        for var in required_vars:
            assert var in content, f"{var} must be defined in .env.example"

        # Check for leaked real private keys or tokens
        assert "AIzaSy" not in content, "Real Google API key detected in .env.example"
        assert "sk-" not in content, "Real OpenAI key format detected in .env.example"
        assert "rzp_live_" not in content, "Live Razorpay credential detected in .env.example"

    def test_gitignore_protects_env_files(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        gitignore_path = os.path.join(repo_root, ".gitignore")
        assert os.path.exists(gitignore_path)

        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_content = f.read()

        assert ".env" in gitignore_content, ".env must be ignored by .gitignore"


class TestAuthColdStartResilience:
    """Verifies JWT token mechanics, expiration, tampered token resilience, and RBAC."""

    def test_create_and_decode_valid_token(self):
        payload = {"sub": "user_42", "role": "energy_manager", "tenant_id": "t_steel_1"}
        token = create_access_token(payload, expires_delta=timedelta(minutes=15))
        assert isinstance(token, str)

        decoded = decode_access_token(token)
        assert decoded["sub"] == "user_42"
        assert decoded["role"] == "energy_manager"
        assert "exp" in decoded

    def test_decode_expired_token_raises_401(self):
        payload = {"sub": "user_expired", "role": "operator"}
        token = create_access_token(payload, expires_delta=timedelta(seconds=-10))

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_decode_invalid_tampered_token_raises_401(self):
        tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(tampered_token)
        assert exc_info.value.status_code == 401

    def test_role_permission_hierarchy(self):
        # Admin has all permissions
        admin_perms = ROLE_PERMISSIONS["admin"]
        assert "execute_control" in admin_perms
        assert "manage_tenant" in admin_perms

        # Operator only has read and ack_alert
        operator_perms = ROLE_PERMISSIONS["operator"]
        assert "read" in operator_perms
        assert "ack_alert" in operator_perms
        assert "execute_control" not in operator_perms


class TestExternalApiResilience:
    """Verifies copilot and external integrations fail gracefully without crashing or 500 errors."""

    def test_copilot_without_gemini_key_uses_deterministic_fallback(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            response = client.post("/api/copilot", json={"message": "Where are we wasting energy?"})
            assert response.status_code == 200
            data = response.json()
            assert "reply" in data
            assert len(data["reply"]) > 20
            # Fallback responds with structured advice
            assert "Telemetry" in data["reply"] or "telemetry" in data["reply"] or "waste" in data["reply"].lower()

    def test_copilot_network_timeout_fails_gracefully(self):
        """When Gemini API times out or throws RequestException, Copilot falls back cleanly."""
        import requests
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_test_key_nonexistent"}):
            with patch("requests.post", side_effect=requests.Timeout("Mock Gemini Connection Timeout")):
                response = client.post("/api/copilot", json={"message": "Show me tomorrow's load forecasts."})
                assert response.status_code == 200
                data = response.json()
                assert "reply" in data
                # Handled cleanly without 500 error
                assert "Forecast" in data["reply"] or "forecast" in data["reply"].lower()

    def test_copilot_http_500_upstream_fails_gracefully(self):
        """When Gemini API returns HTTP 500/503 from upstream, Copilot falls back cleanly."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("503 Service Unavailable")
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_test_key_nonexistent"}):
            with patch("requests.post", return_value=mock_resp):
                response = client.post("/api/copilot", json={"message": "What is the ROI of installing solar?"})
                assert response.status_code == 200
                data = response.json()
                assert "reply" in data
                assert "Investment" in data["reply"] or "ROI" in data["reply"] or "solar" in data["reply"].lower()


class TestErrorHandlingAndValidation:
    """Verifies that invalid payloads yield clear client-facing error responses rather than unhandled 500s."""

    def test_scheduler_negative_duration_returns_422(self):
        payload = {
            "tenant_id": "demo_steel",
            "task_load_kw": 100.0,
            "task_duration_h": -4,  # Invalid duration
            "solar_capacity_kw": 150.0
        }
        response = client.post("/api/schedule", json=payload)
        assert response.status_code == 422

    def test_copilot_empty_message_returns_422(self):
        response = client.post("/api/copilot", json={"message": ""})
        assert response.status_code == 422

    def test_cors_headers_present(self):
        """Verify CORS allows browser cross-origin requests for decoupled frontends."""
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        # FastAPI handles OPTIONS or GET with CORS
        get_res = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-origin" in get_res.headers
