-- Initial database schema for Media Monitoring Agent
-- Migration: 001_initial_schema
-- Created: 2025-01-17

-- Create pending_articles table
CREATE TABLE IF NOT EXISTS pending_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    pasted_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    submitted_by TEXT NOT NULL
);

-- Create processed_archive table
CREATE TABLE IF NOT EXISTS processed_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    submitted_by TEXT NOT NULL,
    processed_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create hansard_questions table
CREATE TABLE IF NOT EXISTS hansard_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    category TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_articles TEXT -- JSON array of related article IDs
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_pending_articles_timestamp ON pending_articles(timestamp);
CREATE INDEX IF NOT EXISTS idx_pending_articles_submitted_by ON pending_articles(submitted_by);
CREATE INDEX IF NOT EXISTS idx_processed_archive_timestamp ON processed_archive(timestamp);
CREATE INDEX IF NOT EXISTS idx_processed_archive_processed_date ON processed_archive(processed_date);
CREATE INDEX IF NOT EXISTS idx_hansard_questions_timestamp ON hansard_questions(timestamp);
CREATE INDEX IF NOT EXISTS idx_hansard_questions_category ON hansard_questions(category);