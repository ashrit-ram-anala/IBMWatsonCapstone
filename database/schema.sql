-- IBM Banking Data Pipeline Database Schema
-- PostgreSQL 15+

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS anomalies CASCADE;
DROP TABLE IF EXISTS dataset_metadata CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;

-- Create ENUM types
CREATE TYPE dataset_status AS ENUM ('uploaded', 'validating', 'cleaning', 'analyzing', 'completed', 'failed');
CREATE TYPE pipeline_stage AS ENUM ('ingestion', 'validation', 'cleaning', 'anomaly_detection', 'review', 'publishing');
CREATE TYPE pipeline_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE anomaly_type AS ENUM (
    'negative_balance',
    'duplicate_transaction',
    'invalid_date',
    'suspicious_amount',
    'status_mismatch',
    'missing_required_field',
    'invalid_format',
    'outlier',
    'semantic_inconsistency',
    'other'
);
CREATE TYPE anomaly_severity AS ENUM ('low', 'medium', 'high', 'critical');

-- Datasets table
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    status dataset_status DEFAULT 'uploaded' NOT NULL,

    -- Metrics
    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    invalid_rows INTEGER DEFAULT 0,
    cleaned_rows INTEGER DEFAULT 0,
    anomaly_count INTEGER DEFAULT 0,
    quality_score NUMERIC(5, 2) DEFAULT 0.0,

    -- Processing info
    processing_time_seconds NUMERIC(10, 2),
    error_message TEXT,
    pipeline_config JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    -- Core transaction fields
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    account_number VARCHAR(50),

    -- Financial details
    amount NUMERIC(15, 2) NOT NULL,
    balance NUMERIC(15, 2),
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,

    -- Transaction metadata
    transaction_date TIMESTAMP NOT NULL,
    transaction_type VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    description TEXT,
    merchant VARCHAR(255),
    category VARCHAR(100),

    -- Validation flags
    is_valid BOOLEAN DEFAULT TRUE NOT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE NOT NULL,
    was_cleaned BOOLEAN DEFAULT FALSE NOT NULL,

    -- Cleaning metadata
    original_values JSONB,
    cleaning_actions JSONB,
    validation_errors JSONB,

    -- Geographic info
    location VARCHAR(255),
    country_code VARCHAR(2),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Pipeline runs table
CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    -- Run identification
    run_id VARCHAR(100) UNIQUE NOT NULL,
    stage pipeline_stage NOT NULL,
    status pipeline_status DEFAULT 'pending' NOT NULL,

    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds NUMERIC(10, 2),

    -- Metrics
    input_rows INTEGER DEFAULT 0,
    output_rows INTEGER DEFAULT 0,
    rows_modified INTEGER DEFAULT 0,
    rows_removed INTEGER DEFAULT 0,
    stage_metrics JSONB,

    -- Errors and logs
    error_message TEXT,
    logs JSONB,

    -- Watsonx node information
    watsonx_node_id VARCHAR(100),
    watsonx_execution_id VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Anomalies table
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    transaction_id VARCHAR(100),

    -- Anomaly classification
    anomaly_type anomaly_type NOT NULL,
    severity anomaly_severity DEFAULT 'medium' NOT NULL,

    -- Detection details
    confidence_score NUMERIC(5, 4) NOT NULL,
    detected_by VARCHAR(100) NOT NULL,

    -- Description and context
    description TEXT NOT NULL,
    field_name VARCHAR(100),
    original_value TEXT,
    expected_value TEXT,
    context JSONB,

    -- Resolution
    is_resolved INTEGER DEFAULT 0 NOT NULL,
    resolution_action VARCHAR(50),
    resolved_value TEXT,

    -- LLM detection details
    llm_explanation TEXT,
    llm_model_id VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Dataset metadata table
CREATE TABLE dataset_metadata (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER UNIQUE NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    -- Schema information
    columns JSONB,
    column_count INTEGER DEFAULT 0,

    -- Data quality metrics
    completeness_score NUMERIC(5, 2) DEFAULT 0.0,
    validity_score NUMERIC(5, 2) DEFAULT 0.0,
    consistency_score NUMERIC(5, 2) DEFAULT 0.0,
    accuracy_score NUMERIC(5, 2) DEFAULT 0.0,

    -- Null statistics
    null_counts JSONB,
    null_percentages JSONB,

    -- Data type statistics
    data_types JSONB,
    type_violations JSONB,

    -- Value distributions
    unique_counts JSONB,
    value_distributions JSONB,

    -- Numeric statistics
    numeric_stats JSONB,

    -- Date/time statistics
    date_range JSONB,

    -- Cleaning operations
    cleaning_summary JSONB,
    transformations JSONB,

    -- File information
    file_size_bytes INTEGER,
    file_format VARCHAR(50),
    encoding VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_datasets_status ON datasets(status);
CREATE INDEX idx_datasets_created_at ON datasets(created_at DESC);
CREATE INDEX idx_transactions_dataset_id ON transactions(dataset_id);
CREATE INDEX idx_transactions_transaction_id ON transactions(transaction_id);
CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_anomaly ON transactions(is_anomaly) WHERE is_anomaly = TRUE;
CREATE INDEX idx_pipeline_runs_dataset_id ON pipeline_runs(dataset_id);
CREATE INDEX idx_pipeline_runs_run_id ON pipeline_runs(run_id);
CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX idx_anomalies_dataset_id ON anomalies(dataset_id);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_dataset_metadata_dataset_id ON dataset_metadata(dataset_id);

-- Create full-text search indexes
CREATE INDEX idx_transactions_description_gin ON transactions USING gin(to_tsvector('english', description));

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_datasets_updated_at
    BEFORE UPDATE ON datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_runs_updated_at
    BEFORE UPDATE ON pipeline_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_anomalies_updated_at
    BEFORE UPDATE ON anomalies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dataset_metadata_updated_at
    BEFORE UPDATE ON dataset_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO datasets (name, source_type, status, total_rows)
VALUES ('Sample Banking Dataset', 'csv', 'uploaded', 0);

COMMENT ON TABLE datasets IS 'Stores information about uploaded datasets';
COMMENT ON TABLE transactions IS 'Stores individual banking transaction records';
COMMENT ON TABLE pipeline_runs IS 'Tracks execution of pipeline stages';
COMMENT ON TABLE anomalies IS 'Records detected anomalies in datasets';
COMMENT ON TABLE dataset_metadata IS 'Stores statistical metadata about datasets';
