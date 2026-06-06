import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { interval, switchMap, takeWhile } from 'rxjs';

import { AdminService } from '../../core/admin.service';
import { IngestionJob } from '../../core/models';

@Component({
  selector: 'app-ingestion',
  templateUrl: './ingestion.html',
  styleUrl: './ingestion.scss',
})
export class Ingestion {
  private readonly admin = inject(AdminService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly starting = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly job = signal<IngestionJob | null>(null);

  protected get isActive(): boolean {
    const s = this.job()?.status;
    return s === 'pending' || s === 'running';
  }

  protected trigger(): void {
    if (this.starting() || this.isActive) return;
    this.starting.set(true);
    this.error.set(null);

    this.admin.triggerIngest().subscribe({
      next: (job) => {
        this.job.set(job);
        this.starting.set(false);
        this.poll(job.id);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Failed to start ingestion (is ingestion-service up?)');
        this.starting.set(false);
      },
    });
  }

  /** Poll job status every 2s until it reaches a terminal state. */
  private poll(id: string): void {
    interval(2000)
      .pipe(
        switchMap(() => this.admin.getJob(id)),
        takeWhile((j) => j.status === 'pending' || j.status === 'running', true),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (j) => this.job.set(j),
        error: () => this.error.set('Lost connection while polling job status.'),
      });
  }
}
