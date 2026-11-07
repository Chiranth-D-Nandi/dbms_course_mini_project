-- Owner: Person A
-- ==============================================================================
-- 00_reset.sql: Idempotent database teardown and initialization script
-- ==============================================================================

-- Ensure tatkal_db exists and is selected before performing any teardown
CREATE DATABASE IF NOT EXISTS tatkal_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tatkal_db;

SET FOREIGN_KEY_CHECKS = 0;

-- Drop all tables if they exist in reverse dependency order
DROP TABLE IF EXISTS cancellation;
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS passenger;
DROP TABLE IF EXISTS booking;
DROP TABLE IF EXISTS run_seat;
DROP TABLE IF EXISTS train_run;
DROP TABLE IF EXISTS seat;
DROP TABLE IF EXISTS coach;
DROP TABLE IF EXISTS seat_class;
DROP TABLE IF EXISTS train_running_day;
DROP TABLE IF EXISTS train_stop;
DROP TABLE IF EXISTS train;
DROP TABLE IF EXISTS station;
DROP TABLE IF EXISTS app_user;
DROP TABLE IF EXISTS audit_log;

-- Drop all views
DROP VIEW IF EXISTS v_passenger_age;
DROP VIEW IF EXISTS v_admin_revenue;
DROP VIEW IF EXISTS v_train_route;
DROP VIEW IF EXISTS v_booking_summary;
DROP VIEW IF EXISTS v_run_availability;

-- Drop all stored procedures and functions
DROP PROCEDURE IF EXISTS sp_generate_run_inventory;
DROP FUNCTION IF EXISTS fn_calc_fare;
DROP PROCEDURE IF EXISTS sp_search_trains;
DROP PROCEDURE IF EXISTS sp_book_tickets;
DROP PROCEDURE IF EXISTS sp_confirm_payment;
DROP PROCEDURE IF EXISTS sp_cancel_booking;
DROP PROCEDURE IF EXISTS sp_release_expired_holds;

-- Drop events
DROP EVENT IF EXISTS ev_release_expired_holds;

SET FOREIGN_KEY_CHECKS = 1;

-- Provision application users with least-privilege security model
-- 1. app_rw: Application read-write user for Django backend
CREATE USER IF NOT EXISTS 'app_rw'@'localhost' IDENTIFIED BY 'TatkalRw_SecurePass#2026';
CREATE USER IF NOT EXISTS 'app_rw'@'127.0.0.1' IDENTIFIED BY 'TatkalRw_SecurePass#2026';

GRANT SELECT, INSERT, UPDATE, DELETE ON tatkal_db.* TO 'app_rw'@'localhost', 'app_rw'@'127.0.0.1';
GRANT EXECUTE ON tatkal_db.* TO 'app_rw'@'localhost', 'app_rw'@'127.0.0.1';
GRANT SHOW VIEW ON tatkal_db.* TO 'app_rw'@'localhost', 'app_rw'@'127.0.0.1';

-- 2. app_ro: Read-only user for analytical reporting
CREATE USER IF NOT EXISTS 'app_ro'@'localhost' IDENTIFIED BY 'TatkalRo_SecurePass#2026';
CREATE USER IF NOT EXISTS 'app_ro'@'127.0.0.1' IDENTIFIED BY 'TatkalRo_SecurePass#2026';

GRANT SELECT ON tatkal_db.* TO 'app_ro'@'localhost', 'app_ro'@'127.0.0.1';
-- Read-only accounts receive EXECUTE only on sp_search_trains after it is created.
GRANT SHOW VIEW ON tatkal_db.* TO 'app_ro'@'localhost', 'app_ro'@'127.0.0.1';

FLUSH PRIVILEGES;
