/**
 * Frontend JavaScript Tests
 * Tests for form validation and submission functionality
 */

// Mock DOM elements for testing
class MockElement {
    constructor(tagName = 'div', attributes = {}) {
        this.tagName = tagName;
        this.attributes = attributes;
        this.classList = new MockClassList();
        this.style = {};
        this.children = [];
        this.parentNode = null;
        this.textContent = '';
        this.value = '';
        this.hidden = false;
        this.disabled = false;
        this.eventListeners = {};
    }

    setAttribute(name, value) {
        this.attributes[name] = value;
    }

    removeAttribute(name) {
        delete this.attributes[name];
    }

    getAttribute(name) {
        return this.attributes[name];
    }

    addEventListener(event, handler) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(handler);
    }

    querySelector(selector) {
        // Simple mock implementation
        if (selector === '.btn-text') return new MockElement('span');
        if (selector === '.btn-loading') return new MockElement('span');
        if (selector === '.field-error') return null;
        if (selector === 'button[type="submit"]') return new MockElement('button');
        return null;
    }

    appendChild(child) {
        this.children.push(child);
        child.parentNode = this;
    }

    remove() {
        if (this.parentNode) {
            const index = this.parentNode.children.indexOf(this);
            if (index > -1) {
                this.parentNode.children.splice(index, 1);
            }
        }
    }

    reset() {
        this.value = '';
    }
}

class MockClassList {
    constructor() {
        this.classes = [];
    }

    add(className) {
        if (!this.classes.includes(className)) {
            this.classes.push(className);
        }
    }

    remove(className) {
        const index = this.classes.indexOf(className);
        if (index > -1) {
            this.classes.splice(index, 1);
        }
    }

    contains(className) {
        return this.classes.includes(className);
    }
}

// Mock document object
const mockDocument = {
    getElementById: (id) => {
        const elements = {
            'article-form': new MockElement('form'),
            'submitted-by': new MockElement('input', { type: 'text' }),
            'article-url': new MockElement('input', { type: 'url' }),
            'submission-feedback': new MockElement('div'),
            'pending-articles-table': new MockElement('table'),
            'pending-articles-body': new MockElement('tbody'),
            'refresh-articles': new MockElement('button'),
            'pasted-content': new MockElement('textarea'),
            'generate-media-report': new MockElement('button'),
            'generate-hansard-report': new MockElement('button'),
            'report-feedback': new MockElement('div')
        };
        return elements[id] || new MockElement();
    },
    createElement: (tagName) => new MockElement(tagName),
    addEventListener: () => {},
    hidden: false
};

// Mock global objects
global.document = mockDocument;
global.URL = class {
    constructor(url) {
        if (!url || typeof url !== 'string') {
            throw new Error('Invalid URL');
        }
        if (url.startsWith('http://') || url.startsWith('https://')) {
            this.protocol = url.startsWith('https://') ? 'https:' : 'http:';
        } else {
            throw new Error('Invalid URL');
        }
    }
};

global.fetch = jest.fn();
global.FormData = class {
    constructor() {
        this.data = {};
    }
    get(key) {
        return this.data[key] || '';
    }
    set(key, value) {
        this.data[key] = value;
    }
};

global.console = {
    log: jest.fn(),
    error: jest.fn()
};

global.setTimeout = jest.fn((fn) => fn());
global.setInterval = jest.fn();
global.clearInterval = jest.fn();
global.localStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn()
};

// Import the class we're testing (in a real environment, this would be loaded differently)
// For testing purposes, we'll define a simplified version
class MediaMonitoringApp {
    constructor() {
        // Form elements
        this.form = mockDocument.getElementById('article-form');
        this.nameInput = mockDocument.getElementById('submitted-by');
        this.urlInput = mockDocument.getElementById('article-url');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.feedbackElement = mockDocument.getElementById('submission-feedback');
        
        // Dashboard elements
        this.pendingArticlesTable = mockDocument.getElementById('pending-articles-table');
        this.pendingArticlesBody = mockDocument.getElementById('pending-articles-body');
        this.refreshButton = mockDocument.getElementById('refresh-articles');
        this.pastedContentTextarea = mockDocument.getElementById('pasted-content');
        this.generateMediaReportButton = mockDocument.getElementById('generate-media-report');
        this.generateHansardReportButton = mockDocument.getElementById('generate-hansard-report');
        this.reportFeedbackElement = mockDocument.getElementById('report-feedback');
        
        // Dashboard state
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshIntervalMs = 30000;
    }

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
        
        this.clearFieldError(this.nameInput);
        return true;
    }

    validateUrl() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.showFieldError(this.urlInput, 'URL is required');
            return false;
        }
        
        if (!this.isValidUrl(url)) {
            this.showFieldError(this.urlInput, 'Please enter a valid URL (e.g., https://example.com)');
            return false;
        }
        
        this.clearFieldError(this.urlInput);
        return true;
    }

    isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('error');
        field.setAttribute('aria-invalid', 'true');
        
        const errorElement = mockDocument.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = message;
        errorElement.setAttribute('role', 'alert');
        
        field.parentNode.appendChild(errorElement);
    }

    clearFieldError(field) {
        field.classList.remove('error');
        field.removeAttribute('aria-invalid');
        
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }

    validateForm() {
        const nameValid = this.validateName();
        const urlValid = this.validateUrl();
        
        return nameValid && urlValid;
    }

    async submitArticle(data) {
        const response = await fetch('/api/articles/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            if (response.status === 400) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Invalid submission data');
            } else if (response.status === 409) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'This article URL has already been submitted');
            } else {
                throw new Error(`Server error: ${response.status}`);
            }
        }

        return await response.json();
    }

    // Dashboard functionality for testing
    async refreshPendingArticles() {
        const response = await fetch('/api/articles/pending');
        if (!response.ok) {
            throw new Error(`Failed to fetch pending articles: ${response.status}`);
        }
        const articles = await response.json();
        this.updatePendingArticlesTable(articles);
    }

    updatePendingArticlesTable(articles) {
        this.pendingArticlesBody.innerHTML = '';
        
        if (articles.length === 0) {
            const emptyRow = mockDocument.createElement('tr');
            emptyRow.className = 'empty-state';
            emptyRow.innerHTML = '<td colspan="3">No pending articles</td>';
            this.pendingArticlesBody.appendChild(emptyRow);
        } else {
            articles.forEach(article => {
                const row = this.createArticleRow(article);
                this.pendingArticlesBody.appendChild(row);
            });
        }
    }

    createArticleRow(article) {
        const row = mockDocument.createElement('tr');
        
        const urlCell = mockDocument.createElement('td');
        const urlLink = mockDocument.createElement('a');
        urlLink.href = article.url;
        urlLink.textContent = this.truncateUrl(article.url);
        urlCell.appendChild(urlLink);
        
        const submittedByCell = mockDocument.createElement('td');
        submittedByCell.textContent = article.submitted_by;
        
        const timestampCell = mockDocument.createElement('td');
        timestampCell.textContent = this.formatTimestamp(article.timestamp);
        
        row.appendChild(urlCell);
        row.appendChild(submittedByCell);
        row.appendChild(timestampCell);
        
        return row;
    }

    truncateUrl(url, maxLength = 50) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength - 3) + '...';
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        return date.toLocaleDateString();
    }

    async handleGenerateMediaReport() {
        const pastedContent = this.pastedContentTextarea.value.trim();
        
        const response = await fetch('/api/reports/media', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pasted_content: pastedContent
            })
        });
        
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.message || 'Failed to generate media report');
        }
        
        return result;
    }

    async handleGenerateHansardReport() {
        const response = await fetch('/api/reports/hansard', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.message || 'Failed to generate Hansard report');
        }
        
        return result;
    }

    savePastedContent() {
        localStorage.setItem('media-monitoring-pasted-content', this.pastedContentTextarea.value);
    }

    restorePastedContent() {
        const savedContent = localStorage.getItem('media-monitoring-pasted-content');
        if (savedContent) {
            this.pastedContentTextarea.value = savedContent;
        }
    }
}

// Test Suite
describe('MediaMonitoringApp Form Validation', () => {
    let app;

    beforeEach(() => {
        app = new MediaMonitoringApp();
        jest.clearAllMocks();
    });

    describe('Name Validation', () => {
        test('should reject empty name', () => {
            app.nameInput.value = '';
            expect(app.validateName()).toBe(false);
            expect(app.nameInput.classList.contains('error')).toBe(true);
        });

        test('should reject name with less than 2 characters', () => {
            app.nameInput.value = 'A';
            expect(app.validateName()).toBe(false);
            expect(app.nameInput.classList.contains('error')).toBe(true);
        });

        test('should reject name with more than 100 characters', () => {
            app.nameInput.value = 'A'.repeat(101);
            expect(app.validateName()).toBe(false);
            expect(app.nameInput.classList.contains('error')).toBe(true);
        });

        test('should accept valid name', () => {
            app.nameInput.value = 'John Doe';
            expect(app.validateName()).toBe(true);
            expect(app.nameInput.classList.contains('error')).toBe(false);
        });

        test('should trim whitespace from name', () => {
            app.nameInput.value = '  John Doe  ';
            expect(app.validateName()).toBe(true);
        });
    });

    describe('URL Validation', () => {
        test('should reject empty URL', () => {
            app.urlInput.value = '';
            expect(app.validateUrl()).toBe(false);
            expect(app.urlInput.classList.contains('error')).toBe(true);
        });

        test('should reject invalid URL format', () => {
            app.urlInput.value = 'not-a-url';
            expect(app.validateUrl()).toBe(false);
            expect(app.urlInput.classList.contains('error')).toBe(true);
        });

        test('should reject URL without protocol', () => {
            app.urlInput.value = 'example.com';
            expect(app.validateUrl()).toBe(false);
            expect(app.urlInput.classList.contains('error')).toBe(true);
        });

        test('should accept valid HTTP URL', () => {
            app.urlInput.value = 'http://example.com';
            expect(app.validateUrl()).toBe(true);
            expect(app.urlInput.classList.contains('error')).toBe(false);
        });

        test('should accept valid HTTPS URL', () => {
            app.urlInput.value = 'https://example.com/article';
            expect(app.validateUrl()).toBe(true);
            expect(app.urlInput.classList.contains('error')).toBe(false);
        });

        test('should trim whitespace from URL', () => {
            app.urlInput.value = '  https://example.com  ';
            expect(app.validateUrl()).toBe(true);
        });
    });

    describe('Form Validation', () => {
        test('should validate entire form', () => {
            app.nameInput.value = 'John Doe';
            app.urlInput.value = 'https://example.com';
            expect(app.validateForm()).toBe(true);
        });

        test('should fail validation if name is invalid', () => {
            app.nameInput.value = '';
            app.urlInput.value = 'https://example.com';
            expect(app.validateForm()).toBe(false);
        });

        test('should fail validation if URL is invalid', () => {
            app.nameInput.value = 'John Doe';
            app.urlInput.value = 'invalid-url';
            expect(app.validateForm()).toBe(false);
        });
    });

    describe('Error Handling', () => {
        test('should show field error', () => {
            app.showFieldError(app.nameInput, 'Test error');
            expect(app.nameInput.classList.contains('error')).toBe(true);
            expect(app.nameInput.getAttribute('aria-invalid')).toBe('true');
            expect(app.nameInput.parentNode.children.length).toBe(1);
        });

        test('should clear field error', () => {
            app.showFieldError(app.nameInput, 'Test error');
            app.clearFieldError(app.nameInput);
            expect(app.nameInput.classList.contains('error')).toBe(false);
            expect(app.nameInput.getAttribute('aria-invalid')).toBe(null);
        });
    });

    describe('API Submission', () => {
        test('should submit valid data successfully', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({ success: true, message: 'Success' })
            };
            global.fetch.mockResolvedValue(mockResponse);

            const data = { url: 'https://example.com', submitted_by: 'John Doe' };
            const result = await app.submitArticle(data);

            expect(global.fetch).toHaveBeenCalledWith('/api/articles/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            expect(result).toEqual({ success: true, message: 'Success' });
        });

        test('should handle 400 error response', async () => {
            const mockResponse = {
                ok: false,
                status: 400,
                json: jest.fn().mockResolvedValue({ message: 'Bad request' })
            };
            global.fetch.mockResolvedValue(mockResponse);

            const data = { url: 'invalid', submitted_by: 'John Doe' };
            
            await expect(app.submitArticle(data)).rejects.toThrow('Bad request');
        });

        test('should handle 409 conflict response', async () => {
            const mockResponse = {
                ok: false,
                status: 409,
                json: jest.fn().mockResolvedValue({ message: 'URL already exists' })
            };
            global.fetch.mockResolvedValue(mockResponse);

            const data = { url: 'https://example.com', submitted_by: 'John Doe' };
            
            await expect(app.submitArticle(data)).rejects.toThrow('URL already exists');
        });

        test('should handle server error response', async () => {
            const mockResponse = {
                ok: false,
                status: 500,
                json: jest.fn().mockResolvedValue({})
            };
            global.fetch.mockResolvedValue(mockResponse);

            const data = { url: 'https://example.com', submitted_by: 'John Doe' };
            
            await expect(app.submitArticle(data)).rejects.toThrow('Server error: 500');
        });
    });
});

describe('MediaMonitoringApp Dashboard Functionality', () => {
    let app;

    beforeEach(() => {
        app = new MediaMonitoringApp();
        jest.clearAllMocks();
    });

    describe('Pending Articles Table', () => {
        test('should fetch and display pending articles', async () => {
            const mockArticles = [
                {
                    id: 1,
                    url: 'https://example.com/article1',
                    submitted_by: 'John Doe',
                    timestamp: new Date().toISOString()
                },
                {
                    id: 2,
                    url: 'https://example.com/article2',
                    submitted_by: 'Jane Smith',
                    timestamp: new Date().toISOString()
                }
            ];

            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue(mockArticles)
            };
            global.fetch.mockResolvedValue(mockResponse);

            await app.refreshPendingArticles();

            expect(global.fetch).toHaveBeenCalledWith('/api/articles/pending');
            expect(app.pendingArticlesBody.children.length).toBe(2);
        });

        test('should display empty state when no articles', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue([])
            };
            global.fetch.mockResolvedValue(mockResponse);

            await app.refreshPendingArticles();

            expect(app.pendingArticlesBody.children.length).toBe(1);
            expect(app.pendingArticlesBody.children[0].className).toBe('empty-state');
        });

        test('should handle fetch error', async () => {
            const mockResponse = {
                ok: false,
                status: 500
            };
            global.fetch.mockResolvedValue(mockResponse);

            await expect(app.refreshPendingArticles()).rejects.toThrow('Failed to fetch pending articles: 500');
        });

        test('should create article row correctly', () => {
            const article = {
                id: 1,
                url: 'https://example.com/very-long-article-title-that-should-be-truncated',
                submitted_by: 'John Doe',
                timestamp: new Date().toISOString()
            };

            const row = app.createArticleRow(article);

            expect(row.children.length).toBe(3);
            expect(row.children[0].children[0].href).toBe(article.url);
            expect(row.children[1].textContent).toBe('John Doe');
        });

        test('should truncate long URLs', () => {
            const longUrl = 'https://example.com/very-long-article-title-that-should-be-truncated';
            const truncated = app.truncateUrl(longUrl);
            
            expect(truncated.length).toBeLessThanOrEqual(50);
            expect(truncated.endsWith('...')).toBe(true);
        });

        test('should format timestamps correctly', () => {
            const now = new Date();
            const oneMinuteAgo = new Date(now.getTime() - 60000);
            const justNow = new Date(now.getTime() - 30000);

            expect(app.formatTimestamp(justNow.toISOString())).toBe('Just now');
            expect(app.formatTimestamp(oneMinuteAgo.toISOString())).toBe('1m ago');
        });
    });

    describe('Report Generation', () => {
        test('should generate media report successfully', async () => {
            app.pastedContentTextarea.value = 'Test pasted content';
            
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({ success: true, message: 'Report generated' })
            };
            global.fetch.mockResolvedValue(mockResponse);

            const result = await app.handleGenerateMediaReport();

            expect(global.fetch).toHaveBeenCalledWith('/api/reports/media', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pasted_content: 'Test pasted content' })
            });
            expect(result.success).toBe(true);
        });

        test('should handle media report generation error', async () => {
            const mockResponse = {
                ok: false,
                json: jest.fn().mockResolvedValue({ success: false, message: 'Generation failed' })
            };
            global.fetch.mockResolvedValue(mockResponse);

            await expect(app.handleGenerateMediaReport()).rejects.toThrow('Generation failed');
        });

        test('should generate Hansard report successfully', async () => {
            const mockResponse = {
                ok: true,
                json: jest.fn().mockResolvedValue({ success: true, message: 'Hansard report generated' })
            };
            global.fetch.mockResolvedValue(mockResponse);

            const result = await app.handleGenerateHansardReport();

            expect(global.fetch).toHaveBeenCalledWith('/api/reports/hansard', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            expect(result.success).toBe(true);
        });

        test('should handle Hansard report generation error', async () => {
            const mockResponse = {
                ok: false,
                json: jest.fn().mockResolvedValue({ success: false, message: 'Hansard generation failed' })
            };
            global.fetch.mockResolvedValue(mockResponse);

            await expect(app.handleGenerateHansardReport()).rejects.toThrow('Hansard generation failed');
        });
    });

    describe('Pasted Content Management', () => {
        test('should save pasted content to localStorage', () => {
            app.pastedContentTextarea.value = 'Test content';
            app.savePastedContent();

            expect(localStorage.setItem).toHaveBeenCalledWith('media-monitoring-pasted-content', 'Test content');
        });

        test('should restore pasted content from localStorage', () => {
            localStorage.getItem.mockReturnValue('Restored content');
            
            app.restorePastedContent();

            expect(localStorage.getItem).toHaveBeenCalledWith('media-monitoring-pasted-content');
            expect(app.pastedContentTextarea.value).toBe('Restored content');
        });

        test('should handle localStorage errors gracefully', () => {
            localStorage.getItem.mockImplementation(() => {
                throw new Error('localStorage error');
            });

            // Should not throw
            expect(() => app.restorePastedContent()).not.toThrow();
        });
    });

    describe('Table Population and Updates', () => {
        test('should update table with multiple articles', () => {
            const articles = [
                { id: 1, url: 'https://example.com/1', submitted_by: 'User 1', timestamp: new Date().toISOString() },
                { id: 2, url: 'https://example.com/2', submitted_by: 'User 2', timestamp: new Date().toISOString() },
                { id: 3, url: 'https://example.com/3', submitted_by: 'User 3', timestamp: new Date().toISOString() }
            ];

            app.updatePendingArticlesTable(articles);

            expect(app.pendingArticlesBody.children.length).toBe(3);
            expect(app.pendingArticlesBody.innerHTML).toBe('');
        });

        test('should clear existing rows before adding new ones', () => {
            // Add some initial content
            app.pendingArticlesBody.innerHTML = '<tr><td>Old content</td></tr>';
            
            const articles = [
                { id: 1, url: 'https://example.com/1', submitted_by: 'User 1', timestamp: new Date().toISOString() }
            ];

            app.updatePendingArticlesTable(articles);

            expect(app.pendingArticlesBody.innerHTML).toBe('');
            expect(app.pendingArticlesBody.children.length).toBe(1);
        });
    });
});

// Export for potential use in other test files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MediaMonitoringApp, mockDocument };
}