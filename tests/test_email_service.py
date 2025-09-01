"""
Unit tests for email service (n8n webhook)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests
from services.email_service import EmailService, email_service


class TestEmailService:
    """Test cases for EmailService class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.email_service = EmailService()
        self.sample_summaries = [
            {
                'title': 'Test Article 1',
                'summary': 'This is a test summary for article 1.',
                'url': 'https://example.com/article1',
                'submitted_by': 'John Doe'
            },
            {
                'title': 'Test Article 2',
                'summary': 'This is a test summary for article 2.',
                'url': 'https://example.com/article2',
                'submitted_by': 'Jane Smith'
            }
        ]
    
    @patch('services.email_service.requests.post')
    @patch('services.email_service.settings')
    def test_send_report_success(self, mock_settings, mock_post):
        """Test successful email sending via webhook"""
        # Mock settings
        mock_settings.N8N_WEBHOOK_URL = 'https://test.webhook.url'
        
        # Mock successful webhook response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test
        html_content = "<html><body>Test Report</body></html>"
        result = self.email_service.send_report(html_content, recipients=['test@example.com'])
        
        # Assertions
        assert result is True
        mock_post.assert_called_once_with(
            'https://test.webhook.url',
            json={
                'recipient': 'test@example.com',
                'subject': pytest.approx('Media Report - ', abs=50),  # Allow for timestamp variation
                'body': html_content
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
    
    @patch('services.email_service.requests.post')
    @patch('services.email_service.settings')
    def test_send_report_with_custom_subject(self, mock_settings, mock_post):
        """Test email sending with custom subject"""
        # Mock settings
        mock_settings.N8N_WEBHOOK_URL = 'https://test.webhook.url'
        
        # Mock successful webhook response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test with custom subject
        html_content = "<html><body>Test Report</body></html>"
        custom_subject = "Custom Test Report"
        result = self.email_service.send_report(html_content, recipients=['test@example.com'], subject=custom_subject)
        
        # Assertions
        assert result is True
        
        # Check that the webhook was called with custom subject
        call_args = mock_post.call_args[1]['json']
        assert call_args['subject'] == custom_subject
    
    @patch('services.email_service.requests.post')
    @patch('services.email_service.settings')
    def test_send_report_no_recipients(self, mock_settings, mock_post):
        """Test email sending with no recipients"""
        # Mock settings
        mock_settings.N8N_WEBHOOK_URL = 'https://test.webhook.url'
        
        # Mock successful webhook response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test with no recipients (should use default)
        html_content = "<html><body>Test Report</body></html>"
        result = self.email_service.send_report(html_content)
        
        # Assertions
        assert result is True
        
        # Check that default recipient was used
        call_args = mock_post.call_args[1]['json']
        assert call_args['recipient'] == 'default@example.com'
    
    @patch('services.email_service.requests.post')
    @patch('services.email_service.settings')
    def test_send_report_webhook_error(self, mock_settings, mock_post):
        """Test email sending with webhook error"""
        # Mock settings
        mock_settings.N8N_WEBHOOK_URL = 'https://test.webhook.url'
        
        # Mock failed webhook response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response
        
        # Test
        html_content = "<html><body>Test Report</body></html>"
        result = self.email_service.send_report(html_content, recipients=['test@example.com'])
        
        # Assertions
        assert result is False
    
    @patch('services.email_service.requests.post')
    @patch('services.email_service.settings')
    def test_send_report_request_exception(self, mock_settings, mock_post):
        """Test email sending with request exception"""
        # Mock settings
        mock_settings.N8N_WEBHOOK_URL = 'https://test.webhook.url'
        
        # Mock request exception
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
        
        # Test
        html_content = "<html><body>Test Report</body></html>"
        result = self.email_service.send_report(html_content, recipients=['test@example.com'])
        
        # Assertions
        assert result is False
    
    def test_format_html_report_with_summaries(self):
        """Test HTML report formatting with summaries"""
        result = self.email_service.format_html_report(self.sample_summaries)
        
        # Assertions
        assert isinstance(result, str)
        assert '<!DOCTYPE html>' in result
        assert 'Media Report' in result
        assert 'Test Article 1' in result
        assert 'Test Article 2' in result
        assert 'This is a test summary for article 1.' in result
        assert 'This is a test summary for article 2.' in result
        assert 'https://example.com/article1' in result
        assert 'https://example.com/article2' in result
        assert 'John Doe' in result
        assert 'Jane Smith' in result
        assert 'Report contains 2 articles' in result
    
    def test_format_html_report_empty_summaries(self):
        """Test HTML report formatting with empty summaries"""
        result = self.email_service.format_html_report([])
        
        # Assertions
        assert isinstance(result, str)
        assert '<!DOCTYPE html>' in result
        assert 'Media Report' in result
        assert 'No articles were processed for this report.' in result
        assert 'Report contains 0 articles' in result
    
    def test_format_html_report_custom_type(self):
        """Test HTML report formatting with custom report type"""
        result = self.email_service.format_html_report(self.sample_summaries, "Hansard Report")
        
        # Assertions
        assert isinstance(result, str)
        assert 'Hansard Report' in result
        assert 'Test Article 1' in result
    
    def test_format_html_report_missing_fields(self):
        """Test HTML report formatting with missing fields"""
        incomplete_summaries = [
            {
                'summary': 'Summary without title or URL',
                'submitted_by': 'Test User'
            },
            {
                'title': 'Article with missing summary',
                'url': 'https://example.com/test'
            }
        ]
        
        result = self.email_service.format_html_report(incomplete_summaries)
        
        # Assertions
        assert isinstance(result, str)
        assert 'Article 1' in result  # Default title
        assert 'Article with missing summary' in result
        assert 'Summary without title or URL' in result
        assert 'No summary available' in result
        assert 'Unknown' in result  # Default submitted_by
    
    @patch('services.email_service.datetime')
    def test_format_html_report_date_formatting(self, mock_datetime):
        """Test HTML report date formatting"""
        # Mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "January 15, 2024 at 14:30"
        mock_datetime.now.return_value = mock_now
        
        result = self.email_service.format_html_report(self.sample_summaries)
        
        # Assertions
        assert 'Generated on January 15, 2024 at 14:30' in result
        mock_datetime.now.assert_called_once()
        mock_now.strftime.assert_called_with('%B %d, %Y at %H:%M')
    
    def test_format_html_report_html_structure(self):
        """Test HTML report structure and styling"""
        result = self.email_service.format_html_report(self.sample_summaries)
        
        # Check HTML structure
        assert '<html lang="en">' in result
        assert '<head>' in result
        assert '<meta charset="UTF-8">' in result
        assert '<style>' in result
        assert '<body>' in result
        assert '<div class="container">' in result
        assert '<div class="header">' in result
        assert '<div class="summary-section">' in result
        assert '<div class="footer">' in result
        assert '</html>' in result
        
        # Check CSS classes are present
        assert 'summary-title' in result
        assert 'summary-content' in result
        assert 'source-info' in result
        assert 'source-url' in result
    
    def test_global_email_service_instance(self):
        """Test that global email service instance is created"""
        assert email_service is not None
        assert isinstance(email_service, EmailService)


class TestEmailServiceIntegration:
    """Integration tests for EmailService"""
    
    @patch('services.email_service.requests.post')
    @patch('services.email_service.settings')
    def test_complete_email_workflow(self, mock_settings, mock_post):
        """Test complete email workflow from formatting to sending via webhook"""
        # Mock settings
        mock_settings.N8N_WEBHOOK_URL = 'https://test.webhook.url'
        
        # Mock successful webhook response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test data
        summaries = [
            {
                'title': 'Integration Test Article',
                'summary': 'This is an integration test summary.',
                'url': 'https://example.com/integration-test',
                'submitted_by': 'Integration Tester'
            }
        ]
        
        # Create service and format report
        service = EmailService()
        html_content = service.format_html_report(summaries)
        
        # Send report
        result = service.send_report(html_content, recipients=['test@example.com'])
        
        # Assertions
        assert result is True
        assert 'Integration Test Article' in html_content
        assert 'This is an integration test summary.' in html_content
        mock_post.assert_called_once()
        
        # Check webhook payload
        call_args = mock_post.call_args[1]['json']
        assert call_args['recipient'] == 'test@example.com'
        assert 'Integration Test Article' in call_args['body']