import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'AniMatch — Discover anime',
    loadComponent: () => import('./pages/search/search').then((m) => m.Search),
  },
  {
    path: 'about',
    title: 'About — AniMatch',
    loadComponent: () => import('./pages/about/about').then((m) => m.About),
  },
  { path: '**', redirectTo: '' },
];
