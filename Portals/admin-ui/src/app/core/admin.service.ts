import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, forkJoin, map, of } from 'rxjs';

import { environment } from '../../environments/environment';
import { CatalogPage, IngestionJob, ServiceHealth } from './models';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  private readonly services = [
    { name: 'vectorstore-service', url: environment.vectorstoreApiUrl },
    { name: 'ingestion-service', url: environment.ingestionApiUrl },
    { name: 'recommender-service', url: environment.recommenderApiUrl },
  ];

  /** Ping every service's /health endpoint; never errors (down => up:false). */
  health(): Observable<ServiceHealth[]> {
    return forkJoin(
      this.services.map((s) =>
        this.http.get(`${s.url}/health`).pipe(
          map(() => ({ name: s.name, url: s.url, up: true })),
          catchError(() => of({ name: s.name, url: s.url, up: false })),
        ),
      ),
    );
  }

  triggerIngest(): Observable<IngestionJob> {
    return this.http.post<IngestionJob>(`${environment.ingestionApiUrl}/ingest`, {});
  }

  getJob(id: string): Observable<IngestionJob> {
    return this.http.get<IngestionJob>(`${environment.ingestionApiUrl}/jobs/${id}`);
  }

  getCatalog(limit: number, offset: number): Observable<CatalogPage> {
    return this.http.get<CatalogPage>(
      `${environment.ingestionApiUrl}/catalog?limit=${limit}&offset=${offset}`,
    );
  }
}
