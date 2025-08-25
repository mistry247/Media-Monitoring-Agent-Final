"""
Configuration management for Media Monitoring Agent
"""
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required values"""
    pass

class Settings:
    """Application settings and configuration with validation"""
    
    def __init__(self):
        """Initialize settings with validation"""
        self._validate_configuration()
    
    # Database Configuration
    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///media_monitoring.db")
    
    # Gemini API Configuration (using CLAUDE_API_KEY for backward compatibility)
    @property
    def GEMINI_API_KEY(self) -> str:
        # Check for GEMINI_API_KEY first, then fall back to CLAUDE_API_KEY for compatibility
        key = os.getenv("GEMINI_API_KEY") or os.getenv("CLAUDE_API_KEY", "")
        if not key:
            logger.warning("GEMINI_API_KEY (or CLAUDE_API_KEY) not set - AI summarization will not work")
        return key
    
    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    @property
    def GEMINI_MAX_TOKENS(self) -> int:
        try:
            return int(os.getenv("GEMINI_MAX_TOKENS", "8000"))
        except ValueError:
            logger.warning("Invalid GEMINI_MAX_TOKENS value, using default 8000")
            return 8000
    
    # Legacy Claude properties for backward compatibility
    @property
    def CLAUDE_API_KEY(self) -> str:
        return self.GEMINI_API_KEY
    
    @property
    def CLAUDE_API_URL(self) -> str:
        return "https://generativelanguage.googleapis.com/v1beta/models"
    
    @property
    def CLAUDE_MODEL(self) -> str:
        return self.GEMINI_MODEL
    
    @property
    def CLAUDE_MAX_TOKENS(self) -> int:
        return self.GEMINI_MAX_TOKENS
    
    # Email Configuration
    @property
    def EMAIL_PROVIDER(self) -> str:
        return os.getenv("EMAIL_PROVIDER", "smtp").lower()
    
    @property
    def SENDGRID_API_KEY(self) -> str:
        key = os.getenv("SENDGRID_API_KEY", "")
        if not key and self.EMAIL_PROVIDER == "sendgrid":
            logger.warning("SENDGRID_API_KEY not set - email functionality will not work")
        return key
    
    @property
    def SMTP_HOST(self) -> str:
        return os.getenv("SMTP_HOST", "smtp.gmail.com")
    
    @property
    def SMTP_PORT(self) -> int:
        try:
            return int(os.getenv("SMTP_PORT", "587"))
        except ValueError:
            logger.warning("Invalid SMTP_PORT value, using default 587")
            return 587
    
    @property
    def SMTP_USERNAME(self) -> str:
        return os.getenv("SMTP_USERNAME", "")
    
    @property
    def SMTP_PASSWORD(self) -> str:
        return os.getenv("SMTP_PASSWORD", "")
    
    @property
    def SMTP_USE_TLS(self) -> bool:
        return os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    
    @property
    def EMAIL_FROM(self) -> str:
        return os.getenv("EMAIL_FROM", self.SMTP_USERNAME)
    
    @property
    def EMAIL_RECIPIENTS(self) -> List[str]:
        recipients_str = os.getenv("EMAIL_RECIPIENTS", "")
        if not recipients_str:
            logger.warning("EMAIL_RECIPIENTS not set - reports will not be sent")
            return []
        return [email.strip() for email in recipients_str.split(",") if email.strip()]
    
    # Web Scraping Configuration
    @property
    def SCRAPING_TIMEOUT(self) -> int:
        try:
            return int(os.getenv("SCRAPING_TIMEOUT", "30"))
        except ValueError:
            logger.warning("Invalid SCRAPING_TIMEOUT value, using default 30")
            return 30
    
    @property
    def SCRAPING_USER_AGENT(self) -> str:
        return os.getenv("SCRAPING_USER_AGENT", "Media Monitoring Agent/1.0")
    
    @property
    def SCRAPING_MAX_RETRIES(self) -> int:
        try:
            return int(os.getenv("SCRAPING_MAX_RETRIES", "3"))
        except ValueError:
            logger.warning("Invalid SCRAPING_MAX_RETRIES value, using default 3")
            return 3
    
    # Application Configuration
    @property
    def DEBUG(self) -> bool:
        return os.getenv("DEBUG", "False").lower() == "true"
    
    @property
    def LOG_LEVEL(self) -> str:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level not in valid_levels:
            logger.warning(f"Invalid LOG_LEVEL '{level}', using default INFO")
            return "INFO"
        return level
    
    @property
    def LOG_FILE(self) -> Optional[str]:
        return os.getenv("LOG_FILE")
    
    @property
    def ENABLE_JSON_LOGGING(self) -> bool:
        return os.getenv("ENABLE_JSON_LOGGING", "False").lower() == "true"
    
    @property
    def HOST(self) -> str:
        return os.getenv("HOST", "0.0.0.0")
    
    @property
    def PORT(self) -> int:
        try:
            return int(os.getenv("PORT", "8000"))
        except ValueError:
            logger.warning("Invalid PORT value, using default 8000")
            return 8000
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        origins_str = os.getenv("CORS_ORIGINS", "*")
        if origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    # Rate Limiting Configuration
    @property
    def RATE_LIMIT_REQUESTS(self) -> int:
        try:
            return int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        except ValueError:
            logger.warning("Invalid RATE_LIMIT_REQUESTS value, using default 100")
            return 100
    
    @property
    def RATE_LIMIT_WINDOW(self) -> int:
        try:
            return int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
        except ValueError:
            logger.warning("Invalid RATE_LIMIT_WINDOW value, using default 3600")
            return 3600
    
    # Local/Mock Mode Configuration
    @property
    def LOCAL_MODE(self) -> bool:
        return os.getenv("LOCAL_MODE", "False").lower() == "true"
    
    # N8N Webhook Configuration
    @property
    def N8N_WEBHOOK_URL(self) -> str:
        return os.getenv("N8N_WEBHOOK_URL", "https://mistry247.app.n8n.cloud/webhook/ee237986-ca83-4bfa-bfc4-74a297f49450")
    
    def _validate_configuration(self):
        errors = []
        email_provider = self.EMAIL_PROVIDER.lower() if self.EMAIL_PROVIDER else 'smtp'
        
        if email_provider == 'sendgrid':
            if not self.SENDGRID_API_KEY:
                errors.append('SENDGRID_API_KEY is required when EMAIL_PROVIDER is set to sendgrid')
        elif email_provider == 'smtp':
            if not self.SMTP_USERNAME:
                errors.append('SMTP_USERNAME is required when EMAIL_PROVIDER is set to smtp')
            if not self.SMTP_PASSWORD:
                errors.append('SMTP_PASSWORD is required when EMAIL_PROVIDER is set to smtp')
            # Only validate SMTP port when using SMTP
            if not (1 <= self.SMTP_PORT <= 65535):
                errors.append(f"SMTP_PORT must be between 1 and 65535, got {self.SMTP_PORT}")
        
        # Check database URL format
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL cannot be empty")
        
        # Validate Gemini API configuration if key is set
        if self.GEMINI_API_KEY:
            # Gemini API doesn't require URL configuration like Claude did
            pass
        
        # Validate application port range
        if not (1 <= self.PORT <= 65535):
            errors.append(f"PORT must be between 1 and 65535, got {self.PORT}")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ConfigurationError(error_msg)
    
    def get_masked_config(self) -> dict:
        """Get configuration with sensitive values masked for logging"""
        return {
            "DATABASE_URL": self.DATABASE_URL,
            "GEMINI_API_KEY": "***" if self.GEMINI_API_KEY else "",
            "GEMINI_MODEL": self.GEMINI_MODEL,
            "GEMINI_MAX_TOKENS": self.GEMINI_MAX_TOKENS,
            "EMAIL_PROVIDER": self.EMAIL_PROVIDER,
            "SENDGRID_API_KEY": "***" if self.SENDGRID_API_KEY else "",
            "SMTP_HOST": self.SMTP_HOST,
            "SMTP_PORT": self.SMTP_PORT,
            "SMTP_USERNAME": self.SMTP_USERNAME,
            "SMTP_PASSWORD": "***" if self.SMTP_PASSWORD else "",
            "SMTP_USE_TLS": self.SMTP_USE_TLS,
            "EMAIL_FROM": self.EMAIL_FROM,
            "EMAIL_RECIPIENTS": self.EMAIL_RECIPIENTS,
            "SCRAPING_TIMEOUT": self.SCRAPING_TIMEOUT,
            "SCRAPING_USER_AGENT": self.SCRAPING_USER_AGENT,
            "SCRAPING_MAX_RETRIES": self.SCRAPING_MAX_RETRIES,
            "DEBUG": self.DEBUG,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_FILE": self.LOG_FILE,
            "ENABLE_JSON_LOGGING": self.ENABLE_JSON_LOGGING,
            "HOST": self.HOST,
            "PORT": self.PORT,
            "CORS_ORIGINS": self.CORS_ORIGINS,
            "RATE_LIMIT_REQUESTS": self.RATE_LIMIT_REQUESTS,
            "RATE_LIMIT_WINDOW": self.RATE_LIMIT_WINDOW,
            "LOCAL_MODE": self.LOCAL_MODE,
            "N8N_WEBHOOK_URL": self.N8N_WEBHOOK_URL,
        }

# Global settings instance
try:
    settings = Settings()
    logger.info("Configuration loaded successfully")
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    raise