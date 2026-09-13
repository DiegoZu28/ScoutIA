import { Component, signal } from '@angular/core';

import { JugadorBusqueda } from '../../core/api/scoutia-api.service';
import { BuscadorJugadorComponent } from './components/buscador-jugador/buscador-jugador.component';
import { FichaJugadorComponent } from './components/ficha-jugador/ficha-jugador.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [BuscadorJugadorComponent, FichaJugadorComponent],
  templateUrl: './home.component.html',
})
export class HomeComponent {
  jugadorSeleccionado = signal<JugadorBusqueda | null>(null);

  onJugadorSeleccionado(jugador: JugadorBusqueda): void {
    this.jugadorSeleccionado.set(jugador);
  }
}
