import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AdminService } from '../../core/admin.service';
import { ServiceHealth } from '../../core/models';

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit {
  private readonly admin = inject(AdminService);

  protected readonly loading = signal(true);
  protected readonly health = signal<ServiceHealth[]>([]);
  protected readonly catalogTotal = signal<number | null>(null);

  /** "Need fresh data?" help accordion — open by default. -1 = closed. */
  protected readonly openNote = signal<number>(0);
  protected toggleNote(i: number): void {
    this.openNote.set(this.openNote() === i ? -1 : i);
  }

  ngOnInit(): void {
    this.refresh();
  }

  protected refresh(): void {
    this.loading.set(true);
    this.admin.health().subscribe((h) => {
      this.health.set(h);
      this.loading.set(false);
    });
    this.admin.getCatalog(1, 0).subscribe({
      next: (page) => this.catalogTotal.set(page.total),
      error: () => this.catalogTotal.set(null),
    });
  }

  protected get upCount(): number {
    return this.health().filter((h) => h.up).length;
  }
}
