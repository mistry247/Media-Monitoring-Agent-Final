-- Add manual_input_articles table for manual processing workflow
-- Migration: 002_add_manual_input_articles
-- Created: 2025-08-26

-- Create manual_input_articles table
CREATE TABLE IF NOT EXISTS manual_input_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    submitted_by TEXT NOT NULL,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    article_content TEXT -- Can store long article text, initially empty/null
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_manual_input_articles_url ON manual_input_articles(url);
CREATE INDEX IF NOT EXISTS idx_manual_input_articles_submitted_by ON manual_input_articles(submitted_by);
CREATE INDEX IF NOT EXISTS idx_manual_input_articles_submitted_at ON manual_input_articles(submitted_at);