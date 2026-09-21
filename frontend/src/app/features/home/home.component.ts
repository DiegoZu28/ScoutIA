import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

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
  private readonly route = inject(ActivatedRoute);

  playerId = signal<string | null>(null);

  constructor() {
    this.route.queryParamMap.pipe(takeUntilDestroyed()).subscribe((params) => {
      const jugador = params.get('jugador');
      if (jugador) {
        this.playerId.set(jugador);
      }
    });
  }

  onJugadorSeleccionado(jugador: JugadorBusqueda): void {
    this.playerId.set(jugador.player_id);
  }
}
