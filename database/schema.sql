-- ============================================================================
-- AI Face Recognition Attendance Management System - Database Schema (MySQL)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `ai_attendance_system` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `ai_attendance_system`;

-- ----------------------------------------------------------------------------
-- Table: users (System Administrators & Staff)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(60) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` VARCHAR(20) DEFAULT 'admin',
    `full_name` VARCHAR(100) DEFAULT 'System Administrator',
    `is_active` BOOLEAN DEFAULT TRUE,
    `last_login` DATETIME NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_username` (`username`),
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table: students (Enrolled Students with Multi-Sample Face Embeddings)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `students` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `student_id` VARCHAR(50) NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `department` VARCHAR(100) NOT NULL,
    `year` VARCHAR(20) NOT NULL,
    `section` VARCHAR(20) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NULL,
    `face_embedding` LONGTEXT NULL COMMENT 'JSON array of multi-sample 128D/512D face embedding vectors',
    `samples_count` INT DEFAULT 0 COMMENT 'Number of enrolled face samples',
    `photo_path` VARCHAR(255) NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    `biometric_registered_at` DATETIME NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_students_student_id` (`student_id`),
    INDEX `idx_students_department` (`department`),
    INDEX `idx_students_year` (`year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table: attendance (Attendance Logs with Anti-Duplicate Constraint)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `attendance` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `student_id` VARCHAR(50) NOT NULL,
    `student_name` VARCHAR(100) NOT NULL,
    `department` VARCHAR(100) NOT NULL,
    `attendance_date` DATE NOT NULL,
    `attendance_time` TIME NOT NULL,
    `status` ENUM('Present', 'Late', 'Absent') DEFAULT 'Present',
    `confidence` FLOAT DEFAULT 0.0 COMMENT 'Face recognition confidence score (0.00 - 1.00)',
    `session_name` VARCHAR(50) DEFAULT 'Morning Session',
    `verification_method` VARCHAR(30) DEFAULT 'Face Recognition',
    `remarks` VARCHAR(255) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_attendance_student` FOREIGN KEY (`student_id`) 
        REFERENCES `students` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `unique_student_date_session` (`student_id`, `attendance_date`, `session_name`),
    INDEX `idx_attendance_date` (`attendance_date`),
    INDEX `idx_attendance_student_id` (`student_id`),
    INDEX `idx_attendance_dept_date` (`department`, `attendance_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table: system_settings (Key-Value Dynamic Configuration)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `system_settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `setting_key` VARCHAR(100) NOT NULL UNIQUE,
    `setting_value` TEXT NOT NULL,
    `description` VARCHAR(255) NULL,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table: activity_logs (Audit Trail for Real-Time UI and Security)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `activity_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `event_type` VARCHAR(50) NOT NULL,
    `description` TEXT NOT NULL,
    `student_id` VARCHAR(50) NULL,
    `ip_address` VARCHAR(45) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_activity_logs_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Initial Default Settings Seed Data
-- ----------------------------------------------------------------------------
INSERT INTO `system_settings` (`setting_key`, `setting_value`, `description`) 
VALUES 
('recognition_threshold', '0.65', 'Confidence threshold for positive face recognition'),
('camera_index', '0', 'Default hardware camera device index'),
('attendance_session', 'Morning Session', 'Active attendance session name'),
('session_start_time', '08:00', 'Session start time (HH:MM)'),
('session_late_time', '09:30', 'Late arrival cutoff time (HH:MM)'),
('session_end_time', '17:00', 'Session end time (HH:MM)'),
('cooldown_seconds', '60', 'Seconds before same face can be logged again')
ON DUPLICATE KEY UPDATE `setting_value`=VALUES(`setting_value`);
