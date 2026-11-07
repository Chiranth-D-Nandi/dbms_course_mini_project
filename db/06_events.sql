-- Owner: Person A
-- ==============================================================================
-- 06_events.sql: Recurring Scheduled Event for Automated Seat Hold Expiry
-- Runs every 30 seconds inside MySQL InnoDB engine
-- ==============================================================================

USE tatkal_db;

-- Enable MySQL Event Scheduler process thread
SET GLOBAL event_scheduler = ON;

DROP EVENT IF EXISTS ev_release_expired_holds;

DELIMITER $$

CREATE EVENT ev_release_expired_holds
ON SCHEDULE EVERY 30 SECOND
STARTS CURRENT_TIMESTAMP
ON COMPLETION PRESERVE
ENABLE
COMMENT 'Sweeps and releases unconfirmed seat holds older than 8 minutes every 30 seconds'
DO
BEGIN
    CALL sp_release_expired_holds();
END$$

DELIMITER ;
