# Requirements Document

## Introduction

The Media Monitoring Agent is a web-based collaborative application designed to streamline the process of collecting, processing, and reporting on media articles for team analysis. The system enables team members to submit article URLs through a simple interface, while core team members can process these submissions along with paywalled content to generate comprehensive media and Hansard reports using AI summarization.

## Requirements

### Requirement 1

**User Story:** As a team member, I want to submit article URLs with my name, so that the core team can process relevant media content for reporting.

#### Acceptance Criteria

1. WHEN a team member accesses the application THEN the system SHALL display a submission form with "Your Name" and "Article URL" fields
2. WHEN a team member clicks the "Submit" button THEN the system SHALL validate that both fields are populated
3. WHEN a valid submission is made THEN the system SHALL check for duplicate URLs in both pending_articles and processed_archive tables
4. IF the URL is unique THEN the system SHALL save the submission to the pending_articles table with a timestamp
5. IF the URL already exists THEN the system SHALL display an appropriate message and not create a duplicate entry
6. WHEN a submission is successful THEN the system SHALL provide confirmation feedback to the user

### Requirement 2

**User Story:** As a core team member, I want to view all pending articles in a dashboard, so that I can see what content needs to be processed.

#### Acceptance Criteria

1. WHEN a core team member accesses the processing dashboard THEN the system SHALL display all articles from the pending_articles table
2. WHEN displaying pending articles THEN the system SHALL show the URL, submitted_by name, and timestamp for each article
3. WHEN the pending_articles table is updated THEN the dashboard SHALL reflect the current state without requiring a page refresh
4. WHEN there are no pending articles THEN the system SHALL display an appropriate empty state message

### Requirement 3

**User Story:** As a core team member, I want to paste paywalled article content into a text area, so that I can include content that cannot be automatically scraped.

#### Acceptance Criteria

1. WHEN a core team member accesses the processing dashboard THEN the system SHALL display a large text area for pasting article content
2. WHEN content is pasted into the text area THEN the system SHALL preserve the formatting and allow for multiple articles
3. WHEN the text area contains content THEN the system SHALL maintain this content until explicitly cleared or processed

### Requirement 4

**User Story:** As a core team member, I want to generate a media report, so that I can create a comprehensive summary of all pending articles for distribution.

#### Acceptance Criteria

1. WHEN a core team member clicks "Generate Media Report" THEN the system SHALL scrape all non-paywalled URLs from the pending_articles table
2. WHEN scraping articles THEN the system SHALL handle failed scrapes gracefully and continue processing other articles
3. WHEN processing content THEN the system SHALL combine scraped content with pasted text from the dashboard text area
4. WHEN all content is collected THEN the system SHALL send the combined text to the Claude API for summarization
5. WHEN Claude API returns summaries THEN the system SHALL combine all summaries into a single HTML report
6. WHEN the HTML report is generated THEN the system SHALL email the report to a predefined list of recipients
7. WHEN the report is successfully sent THEN the system SHALL move processed articles from pending_articles to processed_archive table
8. WHEN articles are archived THEN the system SHALL clear the dashboard text area
9. IF any step fails THEN the system SHALL log the error and provide appropriate feedback to the user

### Requirement 5

**User Story:** As a core team member, I want to generate a Hansard report, so that I can create parliamentary question summaries based on current media content.

#### Acceptance Criteria

1. WHEN a core team member clicks "Generate Hansard Report" THEN the system SHALL collect Hansard data as previously defined
2. WHEN Hansard data is processed THEN the system SHALL generate a report in the specified format
3. WHEN the Hansard report is complete THEN the system SHALL make it available for download or email distribution
4. WHEN Hansard processing is triggered THEN the system SHALL save relevant data to the hansard_questions table

### Requirement 6

**User Story:** As a system administrator, I want the application to use a SQLite database with proper schema, so that data is stored reliably and efficiently.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL initialize a SQLite database with three tables
2. WHEN creating the pending_articles table THEN the system SHALL include columns: id (primary key), url (unique), pasted_text, timestamp, submitted_by
3. WHEN creating the processed_archive table THEN the system SHALL include columns: id (primary key), url, timestamp, submitted_by
4. WHEN creating the hansard_questions table THEN the system SHALL include appropriate columns for Hansard data storage
5. WHEN database operations occur THEN the system SHALL handle connection errors gracefully
6. WHEN duplicate URLs are submitted THEN the database constraints SHALL prevent duplicate entries

### Requirement 7

**User Story:** As a user, I want the application to have a responsive web interface, so that I can access it from different devices and screen sizes.

#### Acceptance Criteria

1. WHEN a user accesses the application THEN the system SHALL serve a single HTML page with embedded CSS and JavaScript
2. WHEN the page loads THEN the system SHALL display both the team submission form and core team dashboard sections
3. WHEN viewed on different screen sizes THEN the interface SHALL remain functional and readable
4. WHEN JavaScript is disabled THEN the basic form submission SHALL still function
5. WHEN API calls are made THEN the system SHALL provide appropriate loading states and error handling

### Requirement 8

**User Story:** As a system integrator, I want the application to integrate with external services, so that it can scrape content, summarize text, and send emails.

#### Acceptance Criteria

1. WHEN scraping non-paywalled articles THEN the system SHALL handle various website structures and content types
2. WHEN calling the Claude API THEN the system SHALL include proper authentication and error handling
3. WHEN sending emails THEN the system SHALL use a configured SMTP server with appropriate credentials
4. WHEN external services are unavailable THEN the system SHALL provide meaningful error messages and graceful degradation
5. WHEN API rate limits are encountered THEN the system SHALL implement appropriate retry logic