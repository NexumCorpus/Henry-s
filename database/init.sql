-- Initial database setup for Henry's SmartStock AI
-- This file is executed when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- Additional indexes will be created by SQLAlchemy migrations

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE henrys_smartstock TO henrys_user;