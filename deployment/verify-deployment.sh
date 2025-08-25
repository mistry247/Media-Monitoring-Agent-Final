#!/bin/bash

# Deployment Verification Script
# Tests that the Media Monitoring Agent is properly deployed and functional

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000"
TEST_ARTICLE_URL="https://www.bbc.com/news"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

test_health_endpoint() {
    log_test "Testing health endpoint..."
    
    if curl -f -s "$BASE_URL/health" > /dev/null; then
        log_info "✅ Health endpoint responding"
        return 0
    else
        log_error "❌ Health endpoint not responding"
        return 1
    fi
}

test_web_interface() {
    log_test "Testing web interface..."
    
    if curl -f -s "$BASE_URL/" > /dev/null; then
        log_info "✅ Web interface accessible"
        return 0
    else
        log_error "❌ Web interface not accessible"
        return 1
    fi
}

test_api_endpoints() {
    log_test "Testing API endpoints..."
    
    # Test articles endpoint
    if curl -f -s "$BASE_URL/api/articles/" > /dev/null; then
        log_info "✅ Articles API responding"
    else
        log_error "❌ Articles API not responding"
        return 1
    fi
    
    # Test reports endpoint
    if curl -f -s "$BASE_URL/api/reports/" > /dev/null; then
        log_info "✅ Reports API responding"
    else
        log_error "❌ Reports API not responding"
        return 1
    fi
    
    return 0
}

test_docker_containers() {
    log_test "Testing Docker containers..."
    
    if command -v docker-compose &> /dev/null; then
        if docker-compose ps | grep -q "Up"; then
            log_info "✅ Docker containers running"
            return 0
        else
            log_error "❌ Docker containers not running properly"
            docker-compose ps
            return 1
        fi
    else
        log_warn "⚠️  Docker Compose not found, skipping container check"
        return 0
    fi
}

test_file_permissions() {
    log_test "Testing file permissions..."
    
    # Check if logs directory is writable
    if [[ -w "logs" ]]; then
        log_info "✅ Logs directory writable"
    else
        log_error "❌ Logs directory not writable"
        return 1
    fi
    
    # Check if data directory is writable
    if [[ -w "data" ]]; then
        log_info "✅ Data directory writable"
    else
        log_error "❌ Data directory not writable"
        return 1
    fi
    
    return 0
}

test_environment_config() {
    log_test "Testing environment configuration..."
    
    if [[ -f ".env" ]]; then
        log_info "✅ Environment file exists"
        
        # Check for required variables
        if grep -q "CLAUDE_API_KEY" .env && ! grep -q "your_gemini_api_key_here" .env; then
            log_info "✅ API key configured"
        else
            log_warn "⚠️  API key not configured or using default value"
        fi
        
        if grep -q "SMTP_USERNAME" .env && ! grep -q "your_email@gmail.com" .env; then
            log_info "✅ Email configuration appears set"
        else
            log_warn "⚠️  Email configuration not set or using default values"
        fi
        
        return 0
    else
        log_error "❌ Environment file (.env) not found"
        return 1
    fi
}

test_ssl_setup() {
    log_test "Testing SSL setup..."
    
    if [[ -d "ssl" && -f "ssl/fullchain.pem" && -f "ssl/privkey.pem" ]]; then
        log_info "✅ SSL certificates found"
        return 0
    else
        log_warn "⚠️  SSL certificates not found (OK for HTTP-only deployment)"
        return 0
    fi
}

run_functional_test() {
    log_test "Running functional test..."
    
    # Test article submission
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/articles/submit" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$TEST_ARTICLE_URL\", \"submitted_by\": \"deployment-test\"}" \
        -o /tmp/test_response.json)
    
    if [[ "$response" == "200" ]]; then
        log_info "✅ Article submission test passed"
        return 0
    else
        log_error "❌ Article submission test failed (HTTP $response)"
        if [[ -f /tmp/test_response.json ]]; then
            cat /tmp/test_response.json
        fi
        return 1
    fi
}

show_summary() {
    echo
    echo "=== Deployment Verification Summary ==="
    echo "Application URL: $BASE_URL"
    echo "Test Article URL: $TEST_ARTICLE_URL"
    echo
    
    if [[ $OVERALL_STATUS -eq 0 ]]; then
        log_info "🎉 All tests passed! Deployment appears to be working correctly."
        echo
        echo "Next steps:"
        echo "1. Access the web interface at $BASE_URL"
        echo "2. Submit a real article to test end-to-end functionality"
        echo "3. Check email delivery by generating a report"
        echo "4. Monitor logs for any issues: docker-compose logs -f"
    else
        log_error "❌ Some tests failed. Please review the errors above."
        echo
        echo "Common fixes:"
        echo "1. Check .env configuration"
        echo "2. Verify Docker containers are running: docker-compose ps"
        echo "3. Check logs: docker-compose logs"
        echo "4. Ensure firewall allows traffic on port 8000"
    fi
}

# Main verification function
main() {
    echo "Media Monitoring Agent - Deployment Verification"
    echo "================================================"
    echo
    
    OVERALL_STATUS=0
    
    # Change to application directory if it exists
    if [[ -d "/opt/media-monitoring-agent" ]]; then
        cd "/opt/media-monitoring-agent"
        log_info "Running from /opt/media-monitoring-agent"
    elif [[ -f "docker-compose.yml" ]]; then
        log_info "Running from current directory"
    else
        log_error "Cannot find application directory or docker-compose.yml"
        exit 1
    fi
    
    # Run tests
    test_docker_containers || OVERALL_STATUS=1
    test_file_permissions || OVERALL_STATUS=1
    test_environment_config || OVERALL_STATUS=1
    test_ssl_setup || OVERALL_STATUS=1
    
    # Wait a moment for services to be ready
    sleep 5
    
    test_health_endpoint || OVERALL_STATUS=1
    test_web_interface || OVERALL_STATUS=1
    test_api_endpoints || OVERALL_STATUS=1
    
    # Only run functional test if basic tests pass
    if [[ $OVERALL_STATUS -eq 0 ]]; then
        run_functional_test || OVERALL_STATUS=1
    fi
    
    show_summary
    
    exit $OVERALL_STATUS
}

# Usage information
usage() {
    echo "Usage: $0 [BASE_URL]"
    echo ""
    echo "Verifies that the Media Monitoring Agent deployment is working correctly."
    echo ""
    echo "Arguments:"
    echo "  BASE_URL    Base URL of the application (default: http://localhost:8000)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Test localhost"
    echo "  $0 http://your-server-ip:8000        # Test remote server"
    echo "  $0 https://yourdomain.com            # Test with SSL"
}

# Parse command line arguments
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ -n "${1:-}" ]]; then
    BASE_URL="$1"
fi

# Run verification
main