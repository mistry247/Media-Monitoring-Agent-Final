# Production Deployment Checklist

Use this checklist to ensure a complete and secure production deployment of the Media Monitoring Agent.

## Pre-Deployment

### System Requirements
- [ ] Linux server with Python 3.8+ installed
- [ ] Sufficient disk space (minimum 10GB recommended)
- [ ] Network access to external APIs (Claude, SMTP)
- [ ] Domain name configured (if using SSL)

### Dependencies
- [ ] Python 3.8+ installed
- [ ] pip and venv available
- [ ] nginx installed (if using reverse proxy)
- [ ] certbot installed (if using Let's Encrypt SSL)

## Configuration

### Environment Setup
- [ ] `.env` file created from `.env.example`
- [ ] Claude API key configured and tested
- [ ] SMTP settings configured and tested
- [ ] Email recipients list configured
- [ ] Database URL configured
- [ ] Debug mode disabled (`DEBUG=False`)
- [ ] Appropriate log level set
- [ ] CORS origins configured for production

### Security Configuration
- [ ] Strong API keys generated
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Security headers enabled in nginx
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured

## Deployment

### Application Deployment
- [ ] Application files copied to `/opt/media-monitoring-agent/`
- [ ] Python virtual environment created
- [ ] Production dependencies installed (`requirements-prod.txt`)
- [ ] File permissions set correctly (`www-data` user)
- [ ] Database migrations run successfully
- [ ] Application starts without errors

### Service Configuration
- [ ] systemd service file installed
- [ ] Service enabled and started
- [ ] Service status verified
- [ ] Service logs checked for errors

### Reverse Proxy (if using nginx)
- [ ] nginx configuration installed
- [ ] nginx configuration tested (`nginx -t`)
- [ ] SSL certificates configured
- [ ] nginx restarted successfully
- [ ] HTTPS redirect working

## Testing

### Functional Testing
- [ ] Application accessible via web browser
- [ ] Article submission form works
- [ ] Dashboard displays pending articles
- [ ] Health check endpoint responds correctly
- [ ] API endpoints respond correctly
- [ ] Email functionality tested
- [ ] Claude API integration tested

### Security Testing
- [ ] HTTPS working correctly
- [ ] HTTP redirects to HTTPS
- [ ] Security headers present
- [ ] Rate limiting working
- [ ] No sensitive information exposed in logs
- [ ] File permissions secure

### Performance Testing
- [ ] Application responds within acceptable time
- [ ] Database queries perform well
- [ ] Memory usage within limits
- [ ] CPU usage acceptable under load

## Post-Deployment

### Monitoring Setup
- [ ] Log rotation configured
- [ ] Health monitoring set up
- [ ] Backup script configured
- [ ] Backup schedule created (cron job)
- [ ] Monitoring alerts configured

### Documentation
- [ ] Production configuration documented
- [ ] Access credentials securely stored
- [ ] Recovery procedures documented
- [ ] Team members trained on system

### Maintenance
- [ ] Update schedule planned
- [ ] Backup restoration tested
- [ ] Monitoring dashboard configured
- [ ] Incident response plan created

## Security Hardening

### System Security
- [ ] System packages updated
- [ ] Unnecessary services disabled
- [ ] SSH key-based authentication configured
- [ ] Fail2ban or similar intrusion prevention installed
- [ ] Regular security updates scheduled

### Application Security
- [ ] Input validation tested
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] CSRF protection configured
- [ ] API rate limiting tested
- [ ] Error messages don't expose sensitive information

## Backup and Recovery

### Backup Configuration
- [ ] Automated backup script tested
- [ ] Backup retention policy configured
- [ ] Off-site backup storage configured
- [ ] Backup encryption enabled (if required)

### Recovery Testing
- [ ] Database restoration tested
- [ ] Full system recovery tested
- [ ] Recovery time objectives met
- [ ] Recovery procedures documented

## Final Verification

### Smoke Tests
- [ ] Submit test article via web interface
- [ ] Generate test media report
- [ ] Verify email delivery
- [ ] Check all logs for errors
- [ ] Verify all external integrations working

### Performance Baseline
- [ ] Response time baseline established
- [ ] Resource usage baseline recorded
- [ ] Capacity limits documented

### Sign-off
- [ ] Technical team approval
- [ ] Security team approval (if applicable)
- [ ] Operations team handover complete
- [ ] Go-live approval obtained

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Approved By:** _______________  

## Notes

Use this section to record any deployment-specific notes, deviations from standard procedure, or issues encountered during deployment.