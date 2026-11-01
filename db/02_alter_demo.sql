-- Owner: Person A
-- ==============================================================================
-- 02_alter_demo.sql: Demonstration of DDL ALTER and DROP operations
-- Meets syllabus evaluation requirements for DDL operations
-- ==============================================================================

USE tatkal_db;

-- ------------------------------------------------------------------------------
-- 1. Create a demonstration staging table
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS demo_tatkal_quota_archive;

CREATE TABLE demo_tatkal_quota_archive (
    archive_id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    class_code CHAR(3) NOT NULL,
    total_tatkal_seats INT NOT NULL,
    booked_tatkal_seats INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. ALTER TABLE: ADD COLUMN
-- Add a new column to record booking surge index
-- ------------------------------------------------------------------------------
ALTER TABLE demo_tatkal_quota_archive
    ADD COLUMN surge_multiplier DECIMAL(3,2) NOT NULL DEFAULT 1.00 AFTER booked_tatkal_seats;

-- ------------------------------------------------------------------------------
-- 3. ALTER TABLE: MODIFY COLUMN
-- Expand class_code or modify column definitions
-- ------------------------------------------------------------------------------
ALTER TABLE demo_tatkal_quota_archive
    MODIFY COLUMN surge_multiplier DECIMAL(4,2) NOT NULL DEFAULT 1.00;

-- ------------------------------------------------------------------------------
-- 4. ALTER TABLE: ADD CONSTRAINT (CHECK Constraint)
-- Enforce that surge_multiplier cannot drop below 1.00
-- ------------------------------------------------------------------------------
ALTER TABLE demo_tatkal_quota_archive
    ADD CONSTRAINT chk_demo_surge_range CHECK (surge_multiplier BETWEEN 1.00 AND 5.00);

-- ------------------------------------------------------------------------------
-- 5. ALTER TABLE: ADD INDEX
-- Create a composite index on (run_id, class_code)
-- ------------------------------------------------------------------------------
ALTER TABLE demo_tatkal_quota_archive
    ADD INDEX idx_demo_archive_run_class (run_id, class_code);

-- ------------------------------------------------------------------------------
-- 6. ALTER TABLE: DROP COLUMN
-- Demonstrate column removal
-- ------------------------------------------------------------------------------
ALTER TABLE demo_tatkal_quota_archive
    DROP COLUMN created_at;

-- ------------------------------------------------------------------------------
-- 7. Verify Schema Modification
-- ------------------------------------------------------------------------------
DESCRIBE demo_tatkal_quota_archive;
SHOW INDEX FROM demo_tatkal_quota_archive;

-- ------------------------------------------------------------------------------
-- 8. DROP TABLE
-- Clean up demonstration table
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS demo_tatkal_quota_archive;
