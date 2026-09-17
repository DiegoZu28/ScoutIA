import { Routes } from '@angular/router';

import { ComparadorComponent } from './features/comparador/comparador.component';
import { HomeComponent } from './features/home/home.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'comparar', component: ComparadorComponent },
];
