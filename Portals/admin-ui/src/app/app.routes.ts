import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'Dashboard — Anime Admin',
    loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.Dashboard),
  },
  {
    path: 'ingestion',
    title: 'Ingestion — Anime Admin',
    loadComponent: () => import('./pages/ingestion/ingestion').then((m) => m.Ingestion),
  },
  {
    path: 'catalog',
    title: 'Catalog — Anime Admin',
    loadComponent: () => import('./pages/catalog/catalog').then((m) => m.Catalog),
  },
  { path: '**', redirectTo: '' },
];
