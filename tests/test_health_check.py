"""
Tests for health check utilities
"""
import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from utils.health_check import (
    HealthStatus,
    HealthCheckResult,
    HealthChecker,
    health_checker,
    check_database_health,
    check_claude_api_health,
    check_smtp_health,
    check_disk_space,
    check_memory_usage,
    get_health_status
)

class TestHealthStatus:
    """Test HealthStatus enum"""
    
    def test_health_status_values(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

class TestHealthCheckResult:
    """Test HealthCheckResult dataclass"""
    
    def test_health_check_result_creation(self):
        """Test HealthCheckResult creation"""
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="All good",
            duration_ms=123.45,
            details={"key": "value"}
        )
        
        assert result.name == "test_check"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"
        assert result.duration_ms == 123.45
        assert result.details == {"key": "value"}
        assert isinstance(result.timestamp, datetime)
    
    def test_health_check_result_defaults(self):
        """Test HealthCheckResult with defaults"""
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="All good",
            duration_ms=123.45
        )
        
        assert result.details is None
        assert isinstance(result.timestamp, datetime)

class TestHealthChecker:
    """Test HealthChecker class"""
    
    def test_register_check(self):
        """Test registering a health check"""
        checker = HealthChecker()
        
        async def test_check():
            return {"status": "ok"}
        
        checker.register_check("test", test_check, timeout=10.0)
        
        assert "test" in checker.checks
        assert checker.checks["test"]["func"] == test_check
        assert checker.checks["test"]["timeout"] == 10.0
    
    @pytest.mark.asyncio
    async def test_run_check_success(self):
        """Test running a successful health check"""
        checker = HealthChecker()
        
        async def test_check():
            return {"status": "ok"}
        
        checker.register_check("test", test_check)
        result = await checker.run_check("test")
        
        assert isinstance(result, HealthCheckResult)
        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Check passed"
        assert result.details == {"status": "ok"}
        assert result.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_run_check_returns_health_check_result(self):
        """Test running a check that returns HealthCheckResult"""
        checker = HealthChecker()
        
        async def test_check():
            return HealthCheckResult(
                name="test",
                status=HealthStatus.DEGRADED,
                message="Partially working",
                duration_ms=0.0
            )
        
        checker.register_check("test", test_check)
        result = await checker.run_check("test")
        
        assert result.name == "test"
        assert result.status == HealthStatus.DEGRADED
        assert result.message == "Partially working"
        assert result.duration_ms > 0  # Should be updated
    
    @pytest.mark.asyncio
    async def test_run_check_timeout(self):
        """Test running a health check that times out"""
        checker = HealthChecker()
        
        async def slow_check():
            await asyncio.sleep(2)
            return {"status": "ok"}
        
        checker.register_check("slow", slow_check, timeout=0.1)
        result = await checker.run_check("slow")
        
        assert result.name == "slow"
        assert result.status == HealthStatus.UNHEALTHY
        assert "timed out" in result.message
        assert result.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_run_check_exception(self):
        """Test running a health check that raises an exception"""
        checker = HealthChecker()
        
        async def failing_check():
            raise ValueError("Check failed")
        
        checker.register_check("failing", failing_check)
        result = await checker.run_check("failing")
        
        assert result.name == "failing"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Check failed" in result.message
        assert result.details["error"] == "Check failed"
        assert result.details["error_type"] == "ValueError"
    
    @pytest.mark.asyncio
    async def test_run_check_not_found(self):
        """Test running a non-existent health check"""
        checker = HealthChecker()
        result = await checker.run_check("nonexistent")
        
        assert result.name == "nonexistent"
        assert result.status == HealthStatus.UNHEALTHY
        assert "not found" in result.message
        assert result.duration_ms == 0.0
    
    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """Test running all registered health checks"""
        checker = HealthChecker()
        
        async def check1():
            return {"status": "ok"}
        
        async def check2():
            return HealthCheckResult(
                name="check2",
                status=HealthStatus.DEGRADED,
                message="Warning",
                duration_ms=0.0
            )
        
        checker.register_check("check1", check1)
        checker.register_check("check2", check2)
        
        results = await checker.run_all_checks()
        
        assert len(results) == 2
        assert "check1" in results
        assert "check2" in results
        assert results["check1"].status == HealthStatus.HEALTHY
        assert results["check2"].status == HealthStatus.DEGRADED
    
    def test_get_overall_status_all_healthy(self):
        """Test overall status when all checks are healthy"""
        checker = HealthChecker()
        
        results = {
            "check1": HealthCheckResult("check1", HealthStatus.HEALTHY, "OK", 0.0),
            "check2": HealthCheckResult("check2", HealthStatus.HEALTHY, "OK", 0.0)
        }
        
        status = checker.get_overall_status(results)
        assert status == HealthStatus.HEALTHY
    
    def test_get_overall_status_some_degraded(self):
        """Test overall status when some checks are degraded"""
        checker = HealthChecker()
        
        results = {
            "check1": HealthCheckResult("check1", HealthStatus.HEALTHY, "OK", 0.0),
            "check2": HealthCheckResult("check2", HealthStatus.DEGRADED, "Warning", 0.0)
        }
        
        status = checker.get_overall_status(results)
        assert status == HealthStatus.DEGRADED
    
    def test_get_overall_status_some_unhealthy(self):
        """Test overall status when some checks are unhealthy"""
        checker = HealthChecker()
        
        results = {
            "check1": HealthCheckResult("check1", HealthStatus.HEALTHY, "OK", 0.0),
            "check2": HealthCheckResult("check2", HealthStatus.UNHEALTHY, "Failed", 0.0)
        }
        
        status = checker.get_overall_status(results)
        assert status == HealthStatus.UNHEALTHY
    
    def test_get_overall_status_empty(self):
        """Test overall status with no checks"""
        checker = HealthChecker()
        
        status = checker.get_overall_status({})
        assert status == HealthStatus.UNHEALTHY

class TestDatabaseHealthCheck:
    """Test database health check"""
    
    @pytest.mark.asyncio
    @patch('utils.health_check.get_db')
    async def test_check_database_health_success(self, mock_get_db):
        """Test successful database health check"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = (1,)
        mock_db.execute.return_value.fetchall.return_value = [
            ("pending_articles",),
            ("processed_archive",),
            ("hansard_questions",)
        ]
        mock_get_db.return_value = mock_db
        
        result = await check_database_health()
        
        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY
        assert "healthy" in result.message
        assert result.details["tables"] == ["pending_articles", "processed_archive", "hansard_questions"]
    
    @pytest.mark.asyncio
    @patch('utils.health_check.get_db')
    async def test_check_database_health_missing_tables(self, mock_get_db):
        """Test database health check with missing tables"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = (1,)
        mock_db.execute.return_value.fetchall.return_value = [
            ("pending_articles",)
        ]
        mock_get_db.return_value = mock_db
        
        result = await check_database_health()
        
        assert result.name == "database"
        assert result.status == HealthStatus.DEGRADED
        assert "missing tables" in result.message
        assert "processed_archive" in result.details["missing_tables"]
        assert "hansard_questions" in result.details["missing_tables"]
    
    @pytest.mark.asyncio
    @patch('utils.health_check.get_db')
    async def test_check_database_health_connection_failed(self, mock_get_db):
        """Test database health check with connection failure"""
        mock_get_db.side_effect = Exception("Connection failed")
        
        result = await check_database_health()
        
        assert result.name == "database"
        assert result.status == HealthStatus.UNHEALTHY
        assert "connection failed" in result.message.lower()
        assert result.details["error"] == "Connection failed"

class TestClaudeAPIHealthCheck:
    """Test Claude API health check"""
    
    @pytest.mark.asyncio
    @patch('utils.health_check.settings')
    @patch('utils.health_check.aiohttp.ClientSession')
    async def test_check_claude_api_health_success(self, mock_session_class, mock_settings):
        """Test successful Claude API health check"""
        mock_settings.CLAUDE_API_KEY = "test-key"
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post.return_value = mock_response
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        mock_session_class.return_value = mock_session
        
        result = await check_claude_api_health()
        
        assert result.name == "claude_api"
        assert result.status == HealthStatus.HEALTHY
        assert "accessible" in result.message
    
    @pytest.mark.asyncio
    @patch('utils.health_check.settings')
    async def test_check_claude_api_health_no_key(self, mock_settings):
        """Test Claude API health check with no API key"""
        mock_settings.CLAUDE_API_KEY = None
        
        result = await check_claude_api_health()
        
        assert result.name == "claude_api"
        assert result.status == HealthStatus.UNHEALTHY
        assert "not configured" in result.message

class TestGetHealthStatus:
    """Test get_health_status function"""
    
    @pytest.mark.asyncio
    @patch('utils.health_check.health_checker')
    async def test_get_health_status_all_healthy(self, mock_health_checker):
        """Test get_health_status with all healthy checks"""
        mock_results = {
            "database": HealthCheckResult("database", HealthStatus.HEALTHY, "OK", 10.0),
            "claude_api": HealthCheckResult("claude_api", HealthStatus.HEALTHY, "OK", 20.0)
        }
        
        mock_health_checker.run_all_checks = AsyncMock(return_value=mock_results)
        mock_health_checker.get_overall_status.return_value = HealthStatus.HEALTHY
        
        status = await get_health_status()
        
        assert status["status"] == "healthy"
        assert status["summary"]["total_checks"] == 2
        assert status["summary"]["healthy"] == 2
        assert status["summary"]["degraded"] == 0
        assert status["summary"]["unhealthy"] == 0
        assert "checks" in status
        assert "database" in status["checks"]
        assert "claude_api" in status["checks"]
    
    @pytest.mark.asyncio
    @patch('utils.health_check.health_checker')
    async def test_get_health_status_mixed(self, mock_health_checker):
        """Test get_health_status with mixed check results"""
        mock_results = {
            "database": HealthCheckResult("database", HealthStatus.HEALTHY, "OK", 10.0),
            "claude_api": HealthCheckResult("claude_api", HealthStatus.DEGRADED, "Slow", 50.0),
            "smtp": HealthCheckResult("smtp", HealthStatus.UNHEALTHY, "Failed", 5.0)
        }
        
        mock_health_checker.run_all_checks = AsyncMock(return_value=mock_results)
        mock_health_checker.get_overall_status.return_value = HealthStatus.UNHEALTHY
        
        status = await get_health_status()
        
        assert status["status"] == "unhealthy"
        assert status["summary"]["total_checks"] == 3
        assert status["summary"]["healthy"] == 1
        assert status["summary"]["degraded"] == 1
        assert status["summary"]["unhealthy"] == 1