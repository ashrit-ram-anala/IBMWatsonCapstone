import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Dataset,
  PipelineStatus,
  Anomaly,
  MetricsSummary
} from '../models/dataset.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Ingestion endpoints
  uploadCSV(file: File, autoProcess: boolean = true): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post(
      `${this.apiUrl}/ingest/csv?auto_process=${autoProcess}`,
      formData
    );
  }

  ingestFromSQL(connectionString: string, query?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/ingest/sql`, {
      connection_string: connectionString,
      query: query
    });
  }

  ingestFromAPI(apiEndpoint: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/ingest/api`, {
      api_endpoint: apiEndpoint
    });
  }

  // Pipeline endpoints
  getPipelineStatus(pipelineId: string): Observable<PipelineStatus> {
    return this.http.get<PipelineStatus>(
      `${this.apiUrl}/pipelines/${pipelineId}`
    );
  }

  listPipelines(): Observable<{ total: number; pipelines: any[] }> {
    return this.http.get<{ total: number; pipelines: any[] }>(
      `${this.apiUrl}/pipelines`
    );
  }

  deletePipeline(pipelineId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/pipelines/${pipelineId}`);
  }

  // Metrics endpoints
  getOverallMetrics(): Observable<MetricsSummary> {
    return this.http.get<MetricsSummary>(`${this.apiUrl}/metrics`);
  }

  getPipelineMetrics(pipelineId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/metrics/${pipelineId}`);
  }

  // Dataset endpoints
  listDatasets(): Observable<{ total: number; datasets: Dataset[] }> {
    return this.http.get<{ total: number; datasets: Dataset[] }>(
      `${this.apiUrl}/datasets`
    );
  }

  getDataset(pipelineId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/datasets/${pipelineId}`);
  }

  downloadDataset(pipelineId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/datasets/${pipelineId}/download`);
  }

  // Anomaly endpoints
  getAllAnomalies(severity?: string, limit: number = 100): Observable<any> {
    let url = `${this.apiUrl}/anomalies?limit=${limit}`;
    if (severity) {
      url += `&severity=${severity}`;
    }
    return this.http.get(url);
  }

  getPipelineAnomalies(pipelineId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/anomalies/${pipelineId}`);
  }

  getAnomalySummary(): Observable<any> {
    return this.http.get(`${this.apiUrl}/anomalies/stats/summary`);
  }
}
