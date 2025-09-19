-- Add has_content field to manual_input_articles table
-- Migration: 003_add_has_content_field
-- Created: 2025-01-27

-- Add has_content column to manual_input_articles table
ALTER TABLE manual_input_articles ADD COLUMN has_content BOOLEAN DEFAULT 0;

-- Update existing records to set has_content based on article_content
UPDATE manual_input_articles 
SET has_content = CASE 
    WHEN article_content IS NOT NULL AND TRIM(article_content) != '' THEN 1 
    ELSE 0 
END;
