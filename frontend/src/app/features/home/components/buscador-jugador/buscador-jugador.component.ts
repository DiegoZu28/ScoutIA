import { Component, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { JugadorBusqueda, ScoutiaApiService } from '../../../../core/api/scoutia-api.service';
import { AvatarJugadorComponent } from '../../../../shared/ui/avatar-jugador/avatar-jugador.component';

@Component({
  selector: 'app-buscador-jugador',
  standalone: true,
  imports: [FormsModule, AvatarJugadorComponent],
  templateUrl: './buscador-jugador.component.html',
})
export class BuscadorJugadorComponent {
  private readonly api = inject(ScoutiaApiService);
  private readonly consulta$ = new Subject<string>();

  query = signal('');
  resultados = signal<JugadorBusqueda[]>([]);
  buscando = signal(false);

  jugadorSeleccionado = output<JugadorBusqueda>();

  constructor() {
    this.consulta$
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap((texto) => {
          if (texto.trim().length < 2) {
            this.buscando.set(false);
            return [];
          }
          this.buscando.set(true);
          return this.api.buscarJugador(texto);
        }),
        takeUntilDestroyed(),
      )
      .subscribe((resultados) => {
        this.resultados.set(resultados);
        this.buscando.set(false);
      });
  }

  onInput(valor: string): void {
    this.query.set(valor);
    this.consulta$.next(valor);
  }

  seleccionar(jugador: JugadorBusqueda): void {
    this.resultados.set([]);
    this.query.set(jugador.nombre);
    this.jugadorSeleccionado.emit(jugador);
  }
}
