import { Component, effect, inject, input, signal } from '@angular/core';

import { ComparacionJugadores, ScoutiaApiService } from '../../../../core/api/scoutia-api.service';
import { AvatarJugadorComponent } from '../../../../shared/ui/avatar-jugador/avatar-jugador.component';
import { ErrorMessageComponent } from '../../../../shared/ui/error-message/error-message.component';
import { LoadingSpinnerComponent } from '../../../../shared/ui/loading-spinner/loading-spinner.component';
import { COLOR_JUGADOR_A, COLOR_JUGADOR_B } from '../../colores-comparador';
import { ComparacionArquetipoComponent } from '../comparacion-arquetipo/comparacion-arquetipo.component';
import { ComparacionPercentilesComponent } from '../comparacion-percentiles/comparacion-percentiles.component';
import { ComparacionValorComponent } from '../comparacion-valor/comparacion-valor.component';
import { NarrativaComparacionComponent } from '../narrativa-comparacion/narrativa-comparacion.component';

@Component({
  selector: 'app-comparacion-resultado',
  standalone: true,
  imports: [
    LoadingSpinnerComponent,
    ErrorMessageComponent,
    AvatarJugadorComponent,
    ComparacionPercentilesComponent,
    ComparacionValorComponent,
    ComparacionArquetipoComponent,
    NarrativaComparacionComponent,
  ],
  templateUrl: './comparacion-resultado.component.html',
})
export class ComparacionResultadoComponent {
  private readonly api = inject(ScoutiaApiService);

  jugadorAId = input.required<string>();
  jugadorBId = input.required<string>();

  readonly colorA = COLOR_JUGADOR_A;
  readonly colorB = COLOR_JUGADOR_B;

  cargando = signal(false);
  error = signal<string | null>(null);
  comparacion = signal<ComparacionJugadores | null>(null);

  constructor() {
    effect(() => {
      const jugadorA = this.jugadorAId();
      const jugadorB = this.jugadorBId();
      this.cargando.set(true);
      this.error.set(null);
      this.comparacion.set(null);

      this.api.compararJugadores(jugadorA, jugadorB).subscribe({
        next: (comparacion) => {
          this.comparacion.set(comparacion);
          this.cargando.set(false);
        },
        error: () => {
          this.error.set('No se pudo comparar a estos jugadores.');
          this.cargando.set(false);
        },
      });
    });
  }
}
