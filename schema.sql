-- Create the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS product_api;

-- Switch to using that database
USE product_api;

-- Categories table
-- UNIQUE on name: prevents two categories with the same name (business logic rule)
-- updated_at: auto-updates every time a row is modified (industry standard)
CREATE TABLE IF NOT EXISTS categories (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Products table
-- updated_at: auto-updates every time a row is modified
CREATE TABLE IF NOT EXISTS products (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    product_image   VARCHAR(255),
    price           DECIMAL(10, 2) NOT NULL,
    category_ids    VARCHAR(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
