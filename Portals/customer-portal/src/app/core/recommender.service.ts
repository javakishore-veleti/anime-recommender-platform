import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ParsedRecommendation, RecommendationResponse } from './models';

@Injectable({ providedIn: 'root' })
export class RecommenderService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.recommenderApiUrl;

  recommend(query: string): Observable<RecommendationResponse> {
    return this.http.post<RecommendationResponse>(`${this.baseUrl}/recommend`, { query });
  }

  /**
   * Best-effort parse of the LLM's numbered-list response into discrete cards.
   * The model is asked for exactly three numbered recommendations; if parsing
   * fails we fall back to a single block rendered as-is.
   */
  parse(text: string): ParsedRecommendation[] {
    if (!text) return [];
    // Split on leading "1." / "2." / "3." markers (start of line).
    const parts = text.split(/\n(?=\s*\d+[\.\)]\s)/).map((p) => p.trim()).filter(Boolean);
    const blocks: ParsedRecommendation[] = [];
    for (const part of parts) {
      const match = part.match(/^\s*(\d+)[\.\)]\s*(.*)$/s);
      if (!match) continue;
      const index = Number(match[1]);
      const rest = match[2].trim();
      // First line / bolded segment becomes the title.
      const firstLine = rest.split('\n')[0].replace(/\*\*/g, '').replace(/^["']|["':]$/g, '').trim();
      const title = firstLine.split(/[:\-–—]/)[0].trim() || `Recommendation ${index}`;
      const body = rest.slice(rest.indexOf('\n') + 1).trim() || rest;
      blocks.push({ index, title, body });
    }
    return blocks;
  }
}
