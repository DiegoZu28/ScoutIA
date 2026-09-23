import { Routes } from '@angular/router';

import { BienvenidaComponent } from './features/bienvenida/bienvenida.component';
import { ComparadorComponent } from './features/comparador/comparador.component';
import { HomeComponent } from './features/home/home.component';
import { OportunidadesComponent } from './features/oportunidades/oportunidades.component';

export const routes: Routes = [
  { path: '', component: BienvenidaComponent },
  { path: 'jugador', component: HomeComponent },
  { path: 'comparar', component: ComparadorComponent },
  { path: 'oportunidades', component: OportunidadesComponent },
];
