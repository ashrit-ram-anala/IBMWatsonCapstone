-- IBM Banking Data Pipeline Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

DROP TABLE IF EXISTS anomalies CASCADE;
DROP TABLE IF EXISTS dataset_metadata CASCADE;
DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;

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


CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    status dataset_status DEFAULT 'uploaded' NOT NULL,


    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    invalid_rows INTEGER DEFAULT 0,
    cleaned_rows INTEGER DEFAULT 0,
    anomaly_count INTEGER DEFAULT 0,
    quality_score NUMERIC(5, 2) DEFAULT 0.0,

   
    processing_time_seconds NUMERIC(10, 2),
    error_message TEXT,
    pipeline_config JSONB,

   
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    account_number VARCHAR(50),

 
    amount NUMERIC(15, 2) NOT NULL,
    balance NUMERIC(15, 2),
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,

   
    transaction_date TIMESTAMP NOT NULL,
    transaction_type VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    description TEXT,
    merchant VARCHAR(255),
    category VARCHAR(100),

 
    is_valid BOOLEAN DEFAULT TRUE NOT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE NOT NULL,
    was_cleaned BOOLEAN DEFAULT FALSE NOT NULL,

   
    original_values JSONB,
    cleaning_actions JSONB,
    validation_errors JSONB,

  
    location VARCHAR(255),
    country_code VARCHAR(2),

   
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    
    run_id VARCHAR(100) UNIQUE NOT NULL,
    stage pipeline_stage NOT NULL,
    status pipeline_status DEFAULT 'pending' NOT NULL,

    
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds NUMERIC(10, 2),


    input_rows INTEGER DEFAULT 0,
    output_rows INTEGER DEFAULT 0,
    rows_modified INTEGER DEFAULT 0,
    rows_removed INTEGER DEFAULT 0,
    stage_metrics JSONB,


    error_message TEXT,
    logs JSONB,


    watsonx_node_id VARCHAR(100),
    watsonx_execution_id VARCHAR(100),


    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    transaction_id VARCHAR(100),


    anomaly_type anomaly_type NOT NULL,
    severity anomaly_severity DEFAULT 'medium' NOT NULL,


    confidence_score NUMERIC(5, 4) NOT NULL,
    detected_by VARCHAR(100) NOT NULL,


    description TEXT NOT NULL,
    field_name VARCHAR(100),
    original_value TEXT,
    expected_value TEXT,
    context JSONB,


    is_resolved INTEGER DEFAULT 0 NOT NULL,
    resolution_action VARCHAR(50),
    resolved_value TEXT,


    llm_explanation TEXT,
    llm_model_id VARCHAR(100),


    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE TABLE dataset_metadata (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER UNIQUE NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    
    columns JSONB,
    column_count INTEGER DEFAULT 0,

    
    completeness_score NUMERIC(5, 2) DEFAULT 0.0,
    validity_score NUMERIC(5, 2) DEFAULT 0.0,
    consistency_score NUMERIC(5, 2) DEFAULT 0.0,
    accuracy_score NUMERIC(5, 2) DEFAULT 0.0,

    
    null_counts JSONB,
    null_percentages JSONB,

    
    data_types JSONB,
    type_violations JSONB,

    
    unique_counts JSONB,
    value_distributions JSONB,

    
    numeric_stats JSONB,

    
    date_range JSONB,

    
    cleaning_summary JSONB,
    transformations JSONB,

    
    file_size_bytes INTEGER,
    file_format VARCHAR(50),
    encoding VARCHAR(50),


    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


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


CREATE INDEX idx_transactions_description_gin ON transactions USING gin(to_tsvector('english', description));


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


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


INSERT INTO datasets (name, source_type, status, total_rows)
VALUES ('Sample Banking Dataset', 'csv', 'uploaded', 0);

COMMENT ON TABLE datasets IS 'Stores information about uploaded datasets';
COMMENT ON TABLE transactions IS 'Stores individual banking transaction records';
COMMENT ON TABLE pipeline_runs IS 'Tracks execution of pipeline stages';
COMMENT ON TABLE anomalies IS 'Records detected anomalies in datasets';
COMMENT ON TABLE dataset_metadata IS 'Stores statistical metadata about datasets';
