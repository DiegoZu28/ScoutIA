import { Routes } from '@angular/router';

import { ComparadorComponent } from './features/comparador/comparador.component';
import { HomeComponent } from './features/home/home.component';
import { OportunidadesComponent } from './features/oportunidades/oportunidades.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'comparar', component: ComparadorComponent },
  { path: 'oportunidades', component: OportunidadesComponent },
];
