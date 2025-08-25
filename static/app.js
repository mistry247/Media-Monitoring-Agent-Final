/**
 * Media Monitoring Agent - Frontend JavaScript
 * Handles form submission, validation, and user feedback
 */

class MediaMonitoringApp {
    constructor() {
        // Form elements
        this.form = document.getElementById('article-form');
        this.nameInput = document.getElementById('submitted-by');
        this.urlInput = document.getElementById('article-url');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.feedbackElement = document.getElementById('submission-feedback');
        
        // Dashboard elements
        this.pendingArticlesTable = document.getElementById('pending-articles-table');
        this.pendingArticlesBody = document.getElementById('pending-articles-body');
        this.refreshButton = document.getElementById('refresh-articles');
        this.pastedContentTextarea = document.getElementById('pasted-content');
        this.recipientEmailInput = document.getElementById('recipient-email');
        this.generateMediaReportButton = document.getElementById('generate-media-report');
        this.generateHansardReportButton = document.getElementById('generate-hansard-report');
        this.reportFeedbackElement = document.getElementById('report-feedback');
        
        // Dashboard state
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshIntervalMs = 30000; // 30 seconds
        
        // Security state
        this.csrfToken = null;
        this.rateLimitInfo = null;
        
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.initSecurity();
        this.initDashboard();
        console.log('Media Monitoring Agent initialized');
    }

    /**
     * Initialize security features
     */
    async initSecurity() {
        try {
            // Get CSRF token
            await this.refreshCSRFToken();
        } catch (error) {
            console.warn('Failed to initialize CSRF protection:', error);
        }
    }

    /**
     * Get or refresh CSRF token
     */
    async refreshCSRFToken() {
        try {
            const response = await fetch('/api/csrf-token');
            if (response.ok) {
                const data = await response.json();
                this.csrfToken = data.csrf_token;
            }
        } catch (error) {
            console.warn('Failed to get CSRF token:', error);
        }
    }

    bindEvents() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Real-time validation
        this.nameInput.addEventListener('blur', () => this.validateName());
        this.urlInput.addEventListener('blur', () => this.validateUrl());
        this.urlInput.addEventListener('input', () => this.clearFieldError(this.urlInput));
        this.nameInput.addEventListener('input', () => this.clearFieldError(this.nameInput));
        
        // Dashboard events
        this.refreshButton.addEventListener('click', () => this.refreshPendingArticles());
        this.generateMediaReportButton.addEventListener('click', () => this.handleGenerateMediaReport());
        this.generateHansardReportButton.addEventListener('click', () => this.handleGenerateHansardReport());
        
        // Auto-save pasted content to localStorage and validate
        this.pastedContentTextarea.addEventListener('input', () => {
            this.validatePastedContent();
            this.savePastedContent();
        });
        
        // Validate recipient email
        this.recipientEmailInput.addEventListener('blur', () => this.validateRecipientEmail());
        this.recipientEmailInput.addEventListener('input', () => this.clearFieldError(this.recipientEmailInput));
        
        // Handle page visibility changes for auto-refresh
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
    }

    /**
     * Handle form submission with validation and AJAX
     */
    async handleFormSubmit(event) {
        event.preventDefault();
        
        // Clear previous feedback
        this.clearFeedback();
        
        // Validate form
        if (!this.validateForm()) {
            return;
        }

        // Show loading state
        this.setLoadingState(true);

        try {
            const formData = new FormData(this.form);
            const data = {
                url: formData.get('url').trim(),
                submitted_by: formData.get('submitted_by').trim()
            };

            const response = await this.submitArticle(data);
            
            if (response.success) {
                this.showSuccess(response.message || 'Article submitted successfully!');
                this.resetForm();
                // Refresh pending articles table to show the new submission
                setTimeout(() => this.refreshPendingArticles(), 500);
            } else {
                this.showError(response.message || 'Failed to submit article. Please try again.');
            }
        } catch (error) {
            console.error('Submission error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Submit article data to the API
     */
    async submitArticle(data) {
        const headers = {
            'Content-Type': 'application/json',
        };

        // Add CSRF token if available
        if (this.csrfToken) {
            headers['X-CSRF-Token'] = this.csrfToken;
        }

        const response = await fetch('/api/articles/submit', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });

        // Handle rate limiting
        if (response.status === 429) {
            const retryAfter = response.headers.get('Retry-After');
            const errorData = await response.json();
            throw new Error(`Rate limit exceeded. Please try again in ${retryAfter ? Math.ceil(retryAfter / 60) + ' minutes' : 'a few minutes'}.`);
        }

        // Update rate limit info from headers
        this.updateRateLimitInfo(response);

        if (!response.ok) {
            if (response.status === 400) {
                const errorData = await response.json();
                throw new Error(errorData.message || errorData.detail || 'Invalid submission data');
            } else if (response.status === 409) {
                const errorData = await response.json();
                throw new Error(errorData.message || errorData.detail || 'This article URL has already been submitted');
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || errorData.detail || `Server error: ${response.status}`);
            }
        }

        return await response.json();
    }

    /**
     * Validate the entire form
     */
    validateForm() {
        const nameValid = this.validateName();
        const urlValid = this.validateUrl();
        
        return nameValid && urlValid;
    }

    /**
     * Validate name field
     */
    validateName() {
        const name = this.nameInput.value.trim();
        
        if (!name) {
            this.showFieldError(this.nameInput, 'Name is required');
            return false;
        }
        
        if (name.length < 2) {
            this.showFieldError(this.nameInput, 'Name must be at least 2 characters long');
            return false;
        }
        
        if (name.length > 100) {
            this.showFieldError(this.nameInput, 'Name must be less than 100 characters');
            return false;
        }

        // Check for invalid characters (allow only letters, numbers, spaces, hyphens, apostrophes, periods)
        if (!/^[a-zA-Z0-9\s\-'.]+$/.test(name)) {
            this.showFieldError(this.nameInput, 'Name contains invalid characters. Only letters, numbers, spaces, hyphens, apostrophes, and periods are allowed');
            return false;
        }
        
        this.clearFieldError(this.nameInput);
        return true;
    }

    /**
     * Validate URL field
     */
    validateUrl() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.showFieldError(this.urlInput, 'URL is required');
            return false;
        }

        if (url.length > 2048) {
            this.showFieldError(this.urlInput, 'URL is too long (maximum 2048 characters)');
            return false;
        }
        
        if (!this.isValidUrl(url)) {
            this.showFieldError(this.urlInput, 'Please enter a valid HTTP or HTTPS URL (e.g., https://example.com)');
            return false;
        }

        // Check for suspicious patterns
        const suspiciousPatterns = [
            /javascript:/i,
            /data:/i,
            /vbscript:/i,
            /file:/i,
            /ftp:/i,
            /<script/i,
            /<\/script>/i,
            /<iframe/i,
            /<\/iframe>/i
        ];

        for (const pattern of suspiciousPatterns) {
            if (pattern.test(url)) {
                this.showFieldError(this.urlInput, 'URL contains suspicious content and is not allowed');
                return false;
            }
        }
        
        this.clearFieldError(this.urlInput);
        return true;
    }

    /**
     * Check if URL is valid
     */
    isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    /**
     * Validate recipient email field
     */
    validateRecipientEmail() {
        const email = this.recipientEmailInput.value.trim();
        
        if (!email) {
            this.showFieldError(this.recipientEmailInput, 'Recipient email is required');
            return false;
        }
        
        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showFieldError(this.recipientEmailInput, 'Please enter a valid email address');
            return false;
        }
        
        if (email.length > 254) {
            this.showFieldError(this.recipientEmailInput, 'Email address is too long');
            return false;
        }
        
        this.clearFieldError(this.recipientEmailInput);
        return true;
    }

    /**
     * Show field-specific error
     */
    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('error');
        field.setAttribute('aria-invalid', 'true');
        
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        errorElement.setAttribute('role', 'alert');
        
        field.parentNode.appendChild(errorElement);
    }

    /**
     * Clear field-specific error
     */
    clearFieldError(field) {
        field.classList.remove('error');
        field.removeAttribute('aria-invalid');
        
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.feedbackElement.className = 'feedback success';
        this.feedbackElement.textContent = message;
        this.feedbackElement.style.display = 'block';
        
        // Auto-hide success message after 5 seconds
        setTimeout(() => {
            this.clearFeedback();
        }, 5000);
    }

    /**
     * Show error message
     */
    showError(message) {
        this.feedbackElement.className = 'feedback error';
        this.feedbackElement.textContent = message;
        this.feedbackElement.style.display = 'block';
    }

    /**
     * Clear feedback messages
     */
    clearFeedback() {
        this.feedbackElement.style.display = 'none';
        this.feedbackElement.textContent = '';
        this.feedbackElement.className = 'feedback';
    }

    /**
     * Set loading state for form submission
     */
    setLoadingState(loading) {
        const btnText = this.submitButton.querySelector('.btn-text');
        const btnLoading = this.submitButton.querySelector('.btn-loading');
        
        if (loading) {
            this.submitButton.disabled = true;
            btnText.hidden = true;
            btnLoading.hidden = false;
            this.form.classList.add('loading');
        } else {
            this.submitButton.disabled = false;
            btnText.hidden = false;
            btnLoading.hidden = true;
            this.form.classList.remove('loading');
        }
    }

    /**
     * Reset form to initial state
     */
    resetForm() {
        this.form.reset();
        this.clearFieldError(this.nameInput);
        this.clearFieldError(this.urlInput);
    }

    // ===== DASHBOARD FUNCTIONALITY =====

    /**
     * Initialize dashboard functionality
     */
    initDashboard() {
        // Load pending articles immediately
        this.refreshPendingArticles();
        
        // Restore pasted content from localStorage
        this.restorePastedContent();
        
        // Start auto-refresh
        this.startAutoRefresh();
    }

    /**
     * Refresh pending articles table
     */
    async refreshPendingArticles() {
        try {
            this.setRefreshButtonLoading(true);
            
            const response = await fetch('/api/articles/pending');
            
            if (!response.ok) {
                throw new Error(`Failed to fetch pending articles: ${response.status}`);
            }
            
            const data = await response.json();
            const articles = data.articles || [];
            this.updatePendingArticlesTable(articles);
            
        } catch (error) {
            console.error('Error refreshing pending articles:', error);
            this.showReportError('Failed to refresh pending articles. Please try again.');
        } finally {
            this.setRefreshButtonLoading(false);
        }
    }

    /**
     * Update the pending articles table with new data
     */
    updatePendingArticlesTable(articles) {
        // Clear existing rows
        this.pendingArticlesBody.innerHTML = '';
        
        if (articles.length === 0) {
            // Show empty state
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'empty-state';
            emptyRow.innerHTML = '<td colspan="3">No pending articles</td>';
            this.pendingArticlesBody.appendChild(emptyRow);
        } else {
            // Add article rows
            articles.forEach(article => {
                const row = this.createArticleRow(article);
                this.pendingArticlesBody.appendChild(row);
            });
        }
    }

    /**
     * Create a table row for an article
     */
    createArticleRow(article) {
        const row = document.createElement('tr');
        
        // URL cell with link
        const urlCell = document.createElement('td');
        const urlLink = document.createElement('a');
        urlLink.href = article.url;
        urlLink.target = '_blank';
        urlLink.rel = 'noopener noreferrer';
        urlLink.textContent = this.truncateUrl(article.url);
        urlLink.title = article.url;
        urlCell.appendChild(urlLink);
        
        // Submitted by cell
        const submittedByCell = document.createElement('td');
        submittedByCell.textContent = article.submitted_by;
        
        // Timestamp cell
        const timestampCell = document.createElement('td');
        timestampCell.textContent = this.formatTimestamp(article.timestamp);
        timestampCell.title = new Date(article.timestamp).toLocaleString();
        
        row.appendChild(urlCell);
        row.appendChild(submittedByCell);
        row.appendChild(timestampCell);
        
        return row;
    }

    /**
     * Truncate URL for display
     */
    truncateUrl(url, maxLength = 50) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength - 3) + '...';
    }

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    /**
     * Handle media report generation
     */
    async handleGenerateMediaReport() {
        try {
            this.clearReportFeedback();
            
            // Validate recipient email first
            if (!this.validateRecipientEmail()) {
                this.showReportError('Please enter a valid recipient email address');
                return;
            }
            
            this.setReportButtonLoading(this.generateMediaReportButton, true);
            
            const pastedContent = this.pastedContentTextarea.value.trim();
            const recipientEmail = this.recipientEmailInput.value.trim();

            // Validate pasted content length
            if (pastedContent.length > 100000) {
                this.showReportError('Pasted content exceeds maximum length of 100,000 characters');
                return;
            }

            const headers = {
                'Content-Type': 'application/json',
            };

            // Add CSRF token if available
            if (this.csrfToken) {
                headers['X-CSRF-Token'] = this.csrfToken;
            }
            
            const response = await fetch('/api/reports/media', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    pasted_content: pastedContent,
                    recipient_email: recipientEmail
                })
            });

            // Handle rate limiting
            if (response.status === 429) {
                const retryAfter = response.headers.get('Retry-After');
                const errorData = await response.json();
                this.showReportError(`Rate limit exceeded. Please try again in ${retryAfter ? Math.ceil(retryAfter / 60) + ' minutes' : 'a few minutes'}.`);
                return;
            }

            // Update rate limit info from headers
            this.updateRateLimitInfo(response);
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showReportSuccess(result.message || 'Media report generated successfully!');
                // Clear pasted content after successful report generation
                this.pastedContentTextarea.value = '';
                this.savePastedContent();
                // Refresh pending articles as they may have been processed
                setTimeout(() => this.refreshPendingArticles(), 1000);
            } else {
                this.showReportError(result.message || result.detail || 'Failed to generate media report. Please try again.');
            }
            
        } catch (error) {
            console.error('Error generating media report:', error);
            this.showReportError('Network error. Please check your connection and try again.');
        } finally {
            this.setReportButtonLoading(this.generateMediaReportButton, false);
        }
    }

    /**
     * Handle Hansard report generation
     */
    async handleGenerateHansardReport() {
        try {
            this.clearReportFeedback();
            
            // Validate recipient email first
            if (!this.validateRecipientEmail()) {
                this.showReportError('Please enter a valid recipient email address');
                return;
            }
            
            this.setReportButtonLoading(this.generateHansardReportButton, true);

            const recipientEmail = this.recipientEmailInput.value.trim();

            const headers = {
                'Content-Type': 'application/json',
            };

            // Add CSRF token if available
            if (this.csrfToken) {
                headers['X-CSRF-Token'] = this.csrfToken;
            }
            
            const response = await fetch('/api/reports/hansard', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    recipient_email: recipientEmail
                })
            });

            // Handle rate limiting
            if (response.status === 429) {
                const retryAfter = response.headers.get('Retry-After');
                const errorData = await response.json();
                this.showReportError(`Rate limit exceeded. Please try again in ${retryAfter ? Math.ceil(retryAfter / 60) + ' minutes' : 'a few minutes'}.`);
                return;
            }

            // Update rate limit info from headers
            this.updateRateLimitInfo(response);
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showReportSuccess(result.message || 'Hansard report generated successfully!');
            } else {
                this.showReportError(result.message || result.detail || 'Failed to generate Hansard report. Please try again.');
            }
            
        } catch (error) {
            console.error('Error generating Hansard report:', error);
            this.showReportError('Network error. Please check your connection and try again.');
        } finally {
            this.setReportButtonLoading(this.generateHansardReportButton, false);
        }
    }

    /**
     * Save pasted content to localStorage
     */
    savePastedContent() {
        try {
            localStorage.setItem('media-monitoring-pasted-content', this.pastedContentTextarea.value);
        } catch (error) {
            console.warn('Failed to save pasted content to localStorage:', error);
        }
    }

    /**
     * Restore pasted content from localStorage
     */
    restorePastedContent() {
        try {
            const savedContent = localStorage.getItem('media-monitoring-pasted-content');
            if (savedContent) {
                this.pastedContentTextarea.value = savedContent;
            }
        } catch (error) {
            console.warn('Failed to restore pasted content from localStorage:', error);
        }
    }

    /**
     * Start auto-refresh for pending articles
     */
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => {
                if (!document.hidden) {
                    this.refreshPendingArticles();
                }
            }, this.refreshIntervalMs);
        }
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Handle page visibility changes
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden, stop auto-refresh to save resources
            this.stopAutoRefresh();
        } else {
            // Page is visible, restart auto-refresh and refresh immediately
            this.startAutoRefresh();
            this.refreshPendingArticles();
        }
    }

    /**
     * Set loading state for refresh button
     */
    setRefreshButtonLoading(loading) {
        if (loading) {
            this.refreshButton.disabled = true;
            this.refreshButton.textContent = 'Refreshing...';
        } else {
            this.refreshButton.disabled = false;
            this.refreshButton.textContent = 'Refresh Articles';
        }
    }

    /**
     * Set loading state for report generation buttons
     */
    setReportButtonLoading(button, loading) {
        const btnText = button.querySelector('.btn-text');
        const btnLoading = button.querySelector('.btn-loading');
        
        if (loading) {
            button.disabled = true;
            btnText.hidden = true;
            btnLoading.hidden = false;
        } else {
            button.disabled = false;
            btnText.hidden = false;
            btnLoading.hidden = true;
        }
    }

    /**
     * Show report success message
     */
    showReportSuccess(message) {
        this.reportFeedbackElement.className = 'feedback success';
        this.reportFeedbackElement.textContent = message;
        this.reportFeedbackElement.style.display = 'block';
        
        // Auto-hide success message after 8 seconds
        setTimeout(() => {
            this.clearReportFeedback();
        }, 8000);
    }

    /**
     * Show report error message
     */
    showReportError(message) {
        this.reportFeedbackElement.className = 'feedback error';
        this.reportFeedbackElement.textContent = message;
        this.reportFeedbackElement.style.display = 'block';
    }

    /**
     * Clear report feedback messages
     */
    clearReportFeedback() {
        this.reportFeedbackElement.style.display = 'none';
        this.reportFeedbackElement.textContent = '';
        this.reportFeedbackElement.className = 'feedback';
    }

    /**
     * Update rate limit information from response headers
     */
    updateRateLimitInfo(response) {
        const limit = response.headers.get('X-RateLimit-Limit');
        const remaining = response.headers.get('X-RateLimit-Remaining');
        const reset = response.headers.get('X-RateLimit-Reset');

        if (limit && remaining && reset) {
            this.rateLimitInfo = {
                limit: parseInt(limit),
                remaining: parseInt(remaining),
                reset: parseInt(reset)
            };

            // Show warning if approaching rate limit
            if (this.rateLimitInfo.remaining <= 2) {
                const resetTime = new Date(this.rateLimitInfo.reset * 1000);
                console.warn(`Approaching rate limit. ${this.rateLimitInfo.remaining} requests remaining until ${resetTime.toLocaleTimeString()}`);
            }
        }
    }

    /**
     * Validate pasted content length and show character count
     */
    validatePastedContent() {
        const content = this.pastedContentTextarea.value;
        const maxLength = 100000;
        const currentLength = content.length;

        // Update character count display if it exists
        const charCountElement = document.getElementById('char-count');
        if (charCountElement) {
            charCountElement.textContent = `${currentLength.toLocaleString()} / ${maxLength.toLocaleString()} characters`;
            
            if (currentLength > maxLength * 0.9) {
                charCountElement.className = 'char-count warning';
            } else if (currentLength > maxLength) {
                charCountElement.className = 'char-count error';
            } else {
                charCountElement.className = 'char-count';
            }
        }

        return currentLength <= maxLength;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MediaMonitoringApp();
});