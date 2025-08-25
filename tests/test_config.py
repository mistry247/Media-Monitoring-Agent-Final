"""
Tests for configuration management
"""
import os
import pytest
from unittest.mock import patch
from config import Settings, ConfigurationError


class TestSettings:
    """Test configuration settings and validation"""
    
    def test_default_configuration(self):
        """Test that default configuration values are set correctly"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            
            assert settings.DATABASE_URL == "sqlite:///media_monitoring.db"
            assert settings.CLAUDE_API_URL == "https://api.anthropic.com/v1/messages"
            assert settings.CLAUDE_MODEL == "claude-3-sonnet-20240229"
            assert settings.CLAUDE_MAX_TOKENS == 4000
            assert settings.SMTP_HOST == "smtp.gmail.com"
            assert settings.SMTP_PORT == 587
            assert settings.SMTP_USE_TLS is True
            assert settings.SCRAPING_TIMEOUT == 30
            assert settings.SCRAPING_USER_AGENT == "Media Monitoring Agent/1.0"
            assert settings.SCRAPING_MAX_RETRIES == 3
            assert settings.DEBUG is False
            assert settings.LOG_LEVEL == "INFO"
            assert settings.HOST == "0.0.0.0"
            assert settings.PORT == 8000
            assert settings.CORS_ORIGINS == ["*"]
            assert settings.RATE_LIMIT_REQUESTS == 100
            assert settings.RATE_LIMIT_WINDOW == 3600
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "CLAUDE_API_KEY": "test-key",
            "CLAUDE_MAX_TOKENS": "2000",
            "SMTP_PORT": "465",
            "SMTP_USE_TLS": "False",
            "SMTP_USERNAME": "test@example.com",
            "SMTP_PASSWORD": "test-password",
            "EMAIL_RECIPIENTS": "test1@example.com,test2@example.com",
            "SCRAPING_TIMEOUT": "60",
            "DEBUG": "True",
            "LOG_LEVEL": "DEBUG",
            "PORT": "9000",
            "CORS_ORIGINS": "http://localhost:3000,https://example.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.DATABASE_URL == "postgresql://test:test@localhost/test"
            assert settings.CLAUDE_API_KEY == "test-key"
            assert settings.CLAUDE_MAX_TOKENS == 2000
            assert settings.SMTP_PORT == 465
            assert settings.SMTP_USE_TLS is False
            assert settings.EMAIL_RECIPIENTS == ["test1@example.com", "test2@example.com"]
            assert settings.SCRAPING_TIMEOUT == 60
            assert settings.DEBUG is True
            assert settings.LOG_LEVEL == "DEBUG"
            assert settings.PORT == 9000
            assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://example.com"]
    
    def test_invalid_integer_values(self):
        """Test handling of invalid integer environment variables"""
        env_vars = {
            "CLAUDE_MAX_TOKENS": "invalid",
            "SMTP_PORT": "not-a-number",
            "SCRAPING_TIMEOUT": "abc",
            "PORT": "99999999"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError):
                Settings()
    
    def test_invalid_log_level(self):
        """Test handling of invalid log level"""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True):
            settings = Settings()
            assert settings.LOG_LEVEL == "INFO"  # Should fall back to default
    
    def test_email_recipients_parsing(self):
        """Test email recipients parsing with various formats"""
        test_cases = [
            ("", []),
            ("single@example.com", ["single@example.com"]),
            ("one@example.com,two@example.com", ["one@example.com", "two@example.com"]),
            ("  spaced@example.com  ,  another@example.com  ", ["spaced@example.com", "another@example.com"]),
            ("with,empty,,values@example.com", ["with", "empty", "values@example.com"])
        ]
        
        for recipients_str, expected in test_cases:
            env_vars = {"EMAIL_RECIPIENTS": recipients_str}
            # Add SMTP credentials when recipients are set (and not empty)
            if recipients_str and expected:
                env_vars.update({
                    "SMTP_USERNAME": "test@example.com",
                    "SMTP_PASSWORD": "test-password"
                })
            
            with patch.dict(os.environ, env_vars, clear=True):
                settings = Settings()
                assert settings.EMAIL_RECIPIENTS == expected
    
    def test_configuration_validation_missing_smtp_credentials(self):
        """Test validation fails when email recipients are set but SMTP credentials are missing"""
        env_vars = {
            "EMAIL_RECIPIENTS": "test@example.com",
            "SMTP_USERNAME": "",
            "SMTP_PASSWORD": ""
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Settings()
            
            assert "SMTP_USERNAME is required" in str(exc_info.value)
            assert "SMTP_PASSWORD is required" in str(exc_info.value)
    
    def test_configuration_validation_invalid_port_ranges(self):
        """Test validation fails for invalid port ranges"""
        test_cases = [
            {"PORT": "0"},
            {"PORT": "65536"},
            {"SMTP_PORT": "-1"},
            {"SMTP_PORT": "70000"}
        ]
        
        for env_vars in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                with pytest.raises(ConfigurationError):
                    Settings()
    
    def test_get_masked_config(self):
        """Test that sensitive values are masked in configuration output"""
        env_vars = {
            "CLAUDE_API_KEY": "secret-key",
            "SMTP_PASSWORD": "secret-password",
            "SMTP_USERNAME": "user@example.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            masked_config = settings.get_masked_config()
            
            assert masked_config["CLAUDE_API_KEY"] == "***"
            assert masked_config["SMTP_PASSWORD"] == "***"
            assert masked_config["SMTP_USERNAME"] == "user@example.com"  # Username is not masked
    
    def test_email_from_defaults_to_smtp_username(self):
        """Test that EMAIL_FROM defaults to SMTP_USERNAME when not set"""
        with patch.dict(os.environ, {"SMTP_USERNAME": "test@example.com"}, clear=True):
            settings = Settings()
            assert settings.EMAIL_FROM == "test@example.com"
        
        with patch.dict(os.environ, {"SMTP_USERNAME": "test@example.com", "EMAIL_FROM": "custom@example.com"}, clear=True):
            settings = Settings()
            assert settings.EMAIL_FROM == "custom@example.com"