-- ==============================================================================
-- Aura Retail - PostgreSQL Initialization Script
-- Executed automatically on container first-time initialization
-- ==============================================================================

-- Create extension for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create dedicated application schema for Aura Retail
CREATE SCHEMA IF NOT EXISTS aura_retail;

-- Set timezone to UTC for consistent date/time analysis
SET timezone = 'UTC';

-- Schema creation confirmation comment
COMMENT ON DATABASE aura_retail_db IS 'Aura Retail Marketing and Customer Analytics relational data warehouse';
COMMENT ON SCHEMA aura_retail IS 'Core relational warehouse schema for Aura Retail analytics';
