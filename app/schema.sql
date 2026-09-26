-- ================================================================
-- AERIS DATABASE SCHEMA
-- Aerospace Equipment & Reliability Intelligence System
-- Class XII CBSE AI Capstone Project
-- PostgreSQL / Neon
-- ================================================================

-- ----------------------------------------------------------------
-- USERS
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash TEXT,
    name VARCHAR(150),
    google_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT users_email_not_blank
        CHECK (length(trim(email)) > 0)
);


-- ----------------------------------------------------------------
-- ANALYSIS HISTORY
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analysis_history (
    id UUID PRIMARY KEY,

    user_id UUID NOT NULL,

    analysis_type VARCHAR(30) NOT NULL,

    filename VARCHAR(255),

    status VARCHAR(30) NOT NULL DEFAULT 'completed',

    total_observations INTEGER,

    anomalies_detected INTEGER,

    anomaly_rate DOUBLE PRECISION,

    features_used INTEGER,

    method VARCHAR(100),

    method_description TEXT,

    file_path TEXT,

    result_data JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_analysis_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT analysis_type_valid
        CHECK (
            analysis_type IN (
                'telemetry',
                'image'
            )
        ),

    CONSTRAINT analysis_status_valid
        CHECK (
            status IN (
                'processing',
                'completed',
                'failed'
            )
        ),

    CONSTRAINT anomaly_rate_valid
        CHECK (
            anomaly_rate IS NULL
            OR (
                anomaly_rate >= 0
                AND anomaly_rate <= 100
            )
        ),

    CONSTRAINT total_observations_valid
        CHECK (
            total_observations IS NULL
            OR total_observations >= 0
        ),

    CONSTRAINT anomalies_detected_valid
        CHECK (
            anomalies_detected IS NULL
            OR anomalies_detected >= 0
        ),

    CONSTRAINT features_used_valid
        CHECK (
            features_used IS NULL
            OR features_used >= 0
        )
);


-- ----------------------------------------------------------------
-- INDEXES
-- ----------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_google_id
    ON users(google_id);

CREATE INDEX IF NOT EXISTS idx_analysis_user_id
    ON analysis_history(user_id);

CREATE INDEX IF NOT EXISTS idx_analysis_created_at
    ON analysis_history(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_type
    ON analysis_history(analysis_type);

CREATE INDEX IF NOT EXISTS idx_analysis_status
    ON analysis_history(status);


-- ----------------------------------------------------------------
-- OPTIONAL JSONB INDEX
--
-- Useful when searching structured analysis results.
-- ----------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_analysis_result_data
    ON analysis_history
    USING GIN(result_data);


-- ================================================================
-- NOTES
-- ================================================================
--
-- 1. Telemetry CSV files are stored on local disk.
-- 2. Spacecraft images are stored on local disk.
-- 3. PostgreSQL stores metadata and explainable analysis results.
-- 4. Uploaded filenames should be generated using UUIDs by Flask.
-- 5. Passwords must never be stored in plaintext.
-- 6. password_hash contains a Werkzeug-generated password hash.
-- 7. result_data stores JSON-serializable analysis information such
--    as feature names, anomaly rows, image measurements and
--    explanation text.
--
-- ================================================================