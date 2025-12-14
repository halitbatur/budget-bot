-- Budget Bot Database Schema
-- Run this in Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster telegram_user_id lookups
CREATE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id);

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

CREATE INDEX IF NOT EXISTS idx_authorized_users_telegram_id ON authorized_users(telegram_user_id);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    emoji TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Budgets table
CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_amount DECIMAL(12, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_date_range CHECK (end_date >= start_date)
);

-- Create index for user budget lookups
CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_budgets_dates ON budgets(start_date, end_date);

-- Expenses table
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    budget_id UUID REFERENCES budgets(id) ON DELETE SET NULL,
    category_id UUID NOT NULL REFERENCES categories(id),
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    expense_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for expense queries
CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_budget_id ON expenses(budget_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, expense_date);

-- Seed default categories
INSERT INTO categories (name, emoji) VALUES
    ('Food', '🍔'),
    ('Transport', '🚗'),
    ('Shopping', '🛍️'),
    ('Entertainment', '🎮'),
    ('Healthcare', '🏥'),
    ('Bills', '💰'),
    ('Education', '📚'),
    ('Other', '✨')
ON CONFLICT DO NOTHING;

-- Enable Row Level Security
ALTER TABLE authorized_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

-- RLS Policies for authorized_users (allow all operations)
CREATE POLICY "Allow all authorized_users operations" ON authorized_users
    FOR ALL USING (true) WITH CHECK (true);

-- RLS Policies for categories (public read)
CREATE POLICY "Categories are viewable by everyone" ON categories
    FOR SELECT USING (true);

-- RLS Policies for users (allow all operations for anon key)
-- The bot handles user isolation via telegram_user_id in queries
CREATE POLICY "Allow all user operations" ON users
    FOR ALL USING (true) WITH CHECK (true);

-- RLS Policies for budgets
CREATE POLICY "Allow all budget operations" ON budgets
    FOR ALL USING (true) WITH CHECK (true);

-- RLS Policies for expenses
CREATE POLICY "Allow all expense operations" ON expenses
    FOR ALL USING (true) WITH CHECK (true);

