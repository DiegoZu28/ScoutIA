import { Component, signal } from '@angular/core';

import { JugadorBusqueda } from '../../core/api/scoutia-api.service';
import { BuscadorJugadorComponent } from '../home/components/buscador-jugador/buscador-jugador.component';
import { COLOR_JUGADOR_A, COLOR_JUGADOR_B } from './colores-comparador';
import { ComparacionResultadoComponent } from './components/comparacion-resultado/comparacion-resultado.component';

@Component({
  selector: 'app-comparador',
  standalone: true,
  imports: [BuscadorJugadorComponent, ComparacionResultadoComponent],
  templateUrl: './comparador.component.html',
})
export class ComparadorComponent {
  readonly colorA = COLOR_JUGADOR_A;
  readonly colorB = COLOR_JUGADOR_B;

  jugadorA = signal<JugadorBusqueda | null>(null);
  jugadorB = signal<JugadorBusqueda | null>(null);

  onSeleccionA(jugador: JugadorBusqueda): void {
    this.jugadorA.set(jugador);
  }

  onSeleccionB(jugador: JugadorBusqueda): void {
    this.jugadorB.set(jugador);
  }
}
