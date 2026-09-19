-- ==============================================================================
-- Aura Retail Analytics - 001: Schema Creation
-- Purpose: Initialize dedicated application schema and required extensions
-- ==============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create dedicated application schema
CREATE SCHEMA IF NOT EXISTS aura_retail;

-- Schema documentation comment
COMMENT ON SCHEMA aura_retail IS 'Core relational warehouse schema for Aura Retail analytics platform';
