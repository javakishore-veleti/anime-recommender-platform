import { Component, OnInit, computed, inject, signal } from '@angular/core';

import { AdminService } from '../../core/admin.service';
import { CatalogItem } from '../../core/models';

@Component({
  selector: 'app-catalog',
  templateUrl: './catalog.html',
  styleUrl: './catalog.scss',
})
export class Catalog implements OnInit {
  private readonly admin = inject(AdminService);
  protected readonly limit = 20;

  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly items = signal<CatalogItem[]>([]);
  protected readonly total = signal(0);
  protected readonly offset = signal(0);

  protected readonly page = computed(() => Math.floor(this.offset() / this.limit) + 1);
  protected readonly pageCount = computed(() => Math.max(1, Math.ceil(this.total() / this.limit)));

  ngOnInit(): void {
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.admin.getCatalog(this.limit, this.offset()).subscribe({
      next: (p) => {
        this.items.set(p.items);
        this.total.set(p.total);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err?.error?.detail ?? 'Could not load catalog. Has ingestion run yet?');
        this.loading.set(false);
      },
    });
  }

  protected prev(): void {
    if (this.offset() === 0) return;
    this.offset.set(Math.max(0, this.offset() - this.limit));
    this.load();
  }

  protected next(): void {
    if (this.page() >= this.pageCount()) return;
    this.offset.set(this.offset() + this.limit);
    this.load();
  }
}
