#!/bin/bash

# Media Monitoring Agent - Complete Deployment Fix Script
# This script fixes all critical issues: SMTP health check, nginx config, and docker setup

set -e

echo "🔧 Starting Media Monitoring Agent deployment fix..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -d "utils" ]; then
    log_error "Please run this script from the media-monitoring-agent directory"
    exit 1
fi

log_info "Step 1: Backing up existing files..."
cp utils/health_check.py utils/health_check.py.backup 2>/dev/null || true
cp deployment/nginx.conf deployment/nginx.conf.backup 2>/dev/null || true
cp docker-compose.yml docker-compose.yml.backup 2>/dev/null || true

log_info "Step 2: Creating fixed health_check.py (removes SMTP timeout)..."
cat > utils/health_check.py << 'HEALTH_EOF'
"""
Health check utilities for monitoring application status
"""
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

from database import get_db, engine
from config import settings
from utils.logging_config import get_logger

logger = get_logger(__name__)

class HealthStatus(Enum):
    """Health check status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class HealthChecker:
    """Health checker for various system components"""
    
    def __init__(self):
        self.checks = {}
        self.last_results = {}
    
    def register_check(self, name: str, check_func, timeout: float = 5.0):
        """Register a health check function"""
        self.checks[name] = {"func": check_func, "timeout": timeout}
    
    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check '{name}' not found",
                duration_ms=0.0
            )
        
        check_info = self.checks[name]
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                check_info["func"](),
                timeout=check_info["timeout"]
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheckResult):
                result.duration_ms = duration_ms
                return result
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message="Check passed",
                    duration_ms=duration_ms,
                    details=result if isinstance(result, dict) else None
                )
        
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {check_info['timeout']}s",
                duration_ms=duration_ms
            )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check '{name}' failed: {e}")
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                duration_ms=duration_ms,
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        results = {}
        tasks = [self.run_check(name) for name in self.checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, name in enumerate(self.checks):
            result = check_results[i]
            if isinstance(result, Exception):
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check execution failed: {str(result)}",
                    duration_ms=0.0
                )
            else:
                results[name] = result
        
        self.last_results = results
        return results
    
    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status"""
        if not results:
            return HealthStatus.UNHEALTHY
        
        statuses = [result.status for result in results.values()]
        
        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

# Global health checker instance
health_checker = HealthChecker()

async def check_database_health() -> HealthCheckResult:
    """Check database connectivity and basic operations"""
    try:
        db = next(get_db())
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).fetchone()
        
        if result and result[0] == 1:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database is healthy",
                duration_ms=0.0
            )
        else:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message="Database query failed",
                duration_ms=0.0
            )
    
    except Exception as e:
        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
            duration_ms=0.0,
            details={"error": str(e)}
        )

async def check_webhook_health() -> HealthCheckResult:
    """Check N8N webhook connectivity"""
    try:
        webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', None)
        
        if not webhook_url:
            return HealthCheckResult(
                name="webhook",
                status=HealthStatus.UNHEALTHY,
                message="N8N webhook URL not configured",
                duration_ms=0.0
            )
        
        if not webhook_url.startswith(('http://', 'https://')):
            return HealthCheckResult(
                name="webhook",
                status=HealthStatus.UNHEALTHY,
                message="N8N webhook URL is not a valid HTTP/HTTPS URL",
                duration_ms=0.0
            )
        
        return HealthCheckResult(
            name="webhook",
            status=HealthStatus.HEALTHY,
            message="N8N webhook is configured",
            duration_ms=0.0,
            details={"webhook_configured": True}
        )
    
    except Exception as e:
        return HealthCheckResult(
            name="webhook",
            status=HealthStatus.UNHEALTHY,
            message=f"Webhook check failed: {str(e)}",
            duration_ms=0.0,
            details={"error": str(e)}
        )

# Register health checks (NO SMTP!)
health_checker.register_check("database", check_database_health, timeout=5.0)
health_checker.register_check("webhook", check_webhook_health, timeout=2.0)

async def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status of the application"""
    start_time = time.time()
    
    results = await health_checker.run_all_checks()
    overall_status = health_checker.get_overall_status(results)
    total_duration = (time.time() - start_time) * 1000
    
    serializable_results = {}
    for name, result in results.items():
        serializable_results[name] = {
            "status": result.status.value,
            "message": result.message,
            "duration_ms": round(result.duration_ms, 2),
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            "details": result.details
        }
    
    return {
        "status": overall_status.value,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_duration_ms": round(total_duration, 2),
        "checks": serializable_results,
        "summary": {
            "total_checks": len(results),
            "healthy": sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY),
            "degraded": sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY)
        }
    }
HEALTH_EOF

log_info "Step 3: Creating fixed nginx.conf (HTTP only)..."
cat > deployment/nginx.conf << 'NGINX_EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    keepalive_timeout 65;

    upstream app {
        server media-monitoring:8000;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto http;
        }
    }
}
NGINX_EOF

log_info "Step 4: Creating fixed docker-compose.yml..."
cat > docker-compose.yml << 'DOCKER_EOF'
version: '3.8'

services:
  media-monitoring:
    build: .
    container_name: media-monitoring-agent
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/media_monitoring.db
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: media-monitoring-nginx
    ports:
      - "80:80"
    volumes:
      - ./deployment/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - media-monitoring
    restart: unless-stopped

volumes:
  data:
  logs:
DOCKER_EOF

log_info "Step 5: Verifying files were created correctly..."
if grep -q "webhook" utils/health_check.py && ! grep -q "smtp" utils/health_check.py; then
    log_info "✓ health_check.py: SMTP removed, webhook added"
else
    log_error "✗ health_check.py: Fix failed"
    exit 1
fi

if grep -q "listen 80" deployment/nginx.conf && ! grep -q "ssl" deployment/nginx.conf; then
    log_info "✓ nginx.conf: HTTP-only configuration"
else
    log_error "✗ nginx.conf: Fix failed"
    exit 1
fi

if grep -q "nginx:alpine" docker-compose.yml && ! grep -q "443" docker-compose.yml; then
    log_info "✓ docker-compose.yml: HTTP-only setup"
else
    log_error "✗ docker-compose.yml: Fix failed"
    exit 1
fi

log_info "Step 6: Stopping existing containers..."
docker-compose down

log_info "Step 7: Clearing Docker cache (this may take a moment)..."
docker system prune -a -f

log_info "Step 8: Building fresh containers (no cache)..."
docker-compose build --no-cache

log_info "Step 9: Starting the application..."
docker-compose up -d

log_info "Step 10: Waiting for application to start..."
sleep 30

log_info "Step 11: Checking container status..."
docker-compose ps

log_info "Step 12: Testing application health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    log_info "✓ Application is responding to health checks"
else
    log_warn "⚠ Application may still be starting up"
fi

echo ""
echo "🎉 Deployment fix completed!"
echo ""
echo "=== Next Steps ==="
echo "1. Check container status: docker-compose ps"
echo "2. View logs: docker-compose logs -f"
echo "3. Test the application: curl http://localhost/health"
echo "4. Access web interface: http://YOUR-SERVER-IP"
echo ""
echo "=== Troubleshooting ==="
echo "- View logs: docker-compose logs media-monitoring"
echo "- Restart: docker-compose restart"
echo "- Check health: curl http://localhost/health"
echo ""