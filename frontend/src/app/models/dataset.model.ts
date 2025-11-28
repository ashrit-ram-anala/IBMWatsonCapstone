export interface Dataset {
  pipeline_id: string;
  file_name: string;
  source_type: 'csv' | 'sql' | 'api';
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  total_rows: number;
  valid_rows: number;
  quality_score: number;
  processing_time: number;
}

export interface PipelineStatus {
  pipeline_id: string;
  status: string;
  completed: boolean;
  result?: PipelineResult;
  error?: string;
}

export interface PipelineResult {
  pipeline_id: string;
  status: string;
  stages: {
    ingestion?: StageResult;
    validation?: StageResult;
    cleaning?: StageResult;
    anomaly_detection?: StageResult;
    review?: StageResult;
    publishing?: StageResult;
  };
  overall_metrics: OverallMetrics;
  errors: any[];
}

export interface StageResult {
  status: string;
  metrics: any;
}

export interface OverallMetrics {
  total_rows_ingested: number;
  valid_rows: number;
  invalid_rows: number;
  cleaned_rows: number;
  anomalies_detected: number;
  quality_score: number;
  duration_seconds: number;
}

export interface Anomaly {
  row_index: number;
  transaction_id: string;
  anomaly_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  detected_by: string;
  description: string;
  field_name?: string;
  original_value?: string;
  llm_explanation?: string;
}

export interface MetricsSummary {
  total_pipelines: number;
  completed_pipelines: number;
  failed_pipelines: number;
  running_pipelines: number;
  total_rows_processed: number;
  total_anomalies_detected: number;
  total_rows_cleaned: number;
  success_rate: number;
}
