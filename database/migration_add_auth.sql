-- Migration: Add authorized_users table for database-based authentication
-- Run this AFTER the initial migrations.sql has been executed

-- Authorized users table (for access control)
CREATE TABLE IF NOT EXISTS authorized_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    added_by_telegram_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster telegram_user_id lookups
CREATE INDEX IF NOT EXISTS idx_authorized_users_telegram_id ON authorized_users(telegram_user_id);

-- Enable Row Level Security
ALTER TABLE authorized_users ENABLE ROW LEVEL SECURITY;

-- RLS Policy to allow all operations (bot uses anon key)
CREATE POLICY "Allow all authorized_users operations" ON authorized_users
    FOR ALL USING (true) WITH CHECK (true);

-- Success message
SELECT 'Migration completed: authorized_users table created successfully!' as message;

