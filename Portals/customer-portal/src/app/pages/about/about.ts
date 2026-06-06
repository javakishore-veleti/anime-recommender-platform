import { Component } from '@angular/core';

@Component({
  selector: 'app-about',
  templateUrl: './about.html',
  styleUrl: './about.scss',
})
export class About {
  protected readonly steps = [
    { icon: '📝', title: 'Describe a vibe', text: 'Tell us the mood, setting, or genre you are in the mood for.' },
    { icon: '🔎', title: 'Semantic retrieval', text: 'We search a vector index of anime synopses for the closest matches.' },
    { icon: '✨', title: 'LLM picks 3', text: 'A Groq-hosted LLM curates three titles and explains each pick.' },
  ];
}
