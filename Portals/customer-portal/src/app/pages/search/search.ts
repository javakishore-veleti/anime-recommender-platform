import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { RecommenderService } from '../../core/recommender.service';
import { ParsedRecommendation, RecommendationResponse } from '../../core/models';

@Component({
  selector: 'app-search',
  imports: [FormsModule],
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class Search {
  private readonly recommender = inject(RecommenderService);

  protected readonly query = signal('');
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly result = signal<RecommendationResponse | null>(null);
  protected readonly cards = signal<ParsedRecommendation[]>([]);

  protected readonly examples = [
    'light-hearted anime with school settings',
    'dark psychological thrillers',
    'epic fantasy adventures with strong world-building',
    'cozy slice-of-life to relax to',
    'mecha with political intrigue',
  ];

  protected useExample(text: string): void {
    this.query.set(text);
    this.submit();
  }

  protected submit(): void {
    const q = this.query().trim();
    if (!q || this.loading()) return;

    this.loading.set(true);
    this.error.set(null);
    this.result.set(null);
    this.cards.set([]);

    this.recommender.recommend(q).subscribe({
      next: (res) => {
        this.result.set(res);
        this.cards.set(this.recommender.parse(res.recommendation));
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(
          err?.error?.detail ??
            'Could not reach the recommender service. Is it running on :8003?',
        );
        this.loading.set(false);
      },
    });
  }
}
