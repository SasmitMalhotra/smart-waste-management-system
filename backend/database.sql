-- Smart Waste Management System - MySQL schema
-- Run this if you want to deploy on MySQL instead of the default SQLite.
-- (SQLAlchemy will also auto-create these tables from models.py on first run.)

CREATE DATABASE IF NOT EXISTS smart_waste_db;
USE smart_waste_db;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('Citizen','Collector','Admin') DEFAULT 'Citizen',
    address VARCHAR(255) NULL,
    zone VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE waste_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NULL
);

CREATE TABLE bins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bin_code VARCHAR(30) UNIQUE NOT NULL,
    location VARCHAR(200) NOT NULL,
    latitude FLOAT NULL,
    longitude FLOAT NULL,
    zone VARCHAR(100) NOT NULL,
    capacity_liters INT DEFAULT 100,
    current_fill_level INT DEFAULT 0,
    waste_type ENUM('General','Recyclable','Organic','Hazardous') DEFAULT 'General',
    status ENUM('Empty','Half','Full','Overflowing') DEFAULT 'Empty',
    last_collected_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensor_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bin_id INT NOT NULL,
    fill_level INT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE CASCADE
);

CREATE TABLE collections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bin_id INT NOT NULL,
    collector_id INT NULL,
    scheduled_date DATETIME NOT NULL,
    status ENUM('Pending','In Progress','Completed','Missed') DEFAULT 'Pending',
    notes VARCHAR(255) NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE CASCADE,
    FOREIGN KEY (collector_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE complaints (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    bin_id INT NULL,
    reason TEXT NOT NULL,
    status ENUM('Pending','In Progress','Resolved') DEFAULT 'Pending',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE SET NULL
);

CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    status ENUM('Read','Unread') DEFAULT 'Unread',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
