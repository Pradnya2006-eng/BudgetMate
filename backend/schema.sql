-- BudgetMate database schema for MySQL 8.0.16 or newer.
--
-- Run it once:
--   mysql -u root -p < schema.sql
-- or open it in MySQL Workbench and click Run.
-- It only creates things that don't exist yet, so it is safe to run again.

CREATE DATABASE IF NOT EXISTS budgetmate
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE budgetmate;

-- One row per registered person. 
CREATE TABLE IF NOT EXISTS users (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(100)    NOT NULL,
  email         VARCHAR(254)    NOT NULL,
  password_hash VARCHAR(255)    NOT NULL,  -- salted hash, never the password itself
  role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

-- Income and expense entries. Deleting a user deletes their entries too.
CREATE TABLE IF NOT EXISTS transactions (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  type        ENUM('income', 'expense') NOT NULL,
  amount      DECIMAL(12, 2)  NOT NULL,
  category    VARCHAR(60)     NOT NULL,
  description VARCHAR(80)     NOT NULL DEFAULT '',
  tx_date     DATE            NOT NULL,
  created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_transactions_user_date (user_id, tx_date, id),
  CONSTRAINT fk_transactions_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT chk_transactions_amount CHECK (amount > 0)
) ENGINE=InnoDB;

-- One monthly budget per user.
CREATE TABLE IF NOT EXISTS budgets (
  user_id        BIGINT UNSIGNED NOT NULL,
  monthly_budget DECIMAL(12, 2)  NOT NULL DEFAULT 0,
  updated_at     TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  CONSTRAINT fk_budgets_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT chk_budgets_amount CHECK (monthly_budget >= 0)
) ENGINE=InnoDB;

-- Forgot-password links. Only a hash of each token is stored, so a copy of
-- this table can't be used to reset anyone's password.
CREATE TABLE IF NOT EXISTS password_resets (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id    BIGINT UNSIGNED NOT NULL,
  token_hash CHAR(64)        NOT NULL,
  expires_at DATETIME        NOT NULL,  -- stored in UTC
  used_at    DATETIME        NULL,
  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_password_resets_token (token_hash),
  KEY idx_password_resets_user (user_id),
  CONSTRAINT fk_password_resets_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB;
