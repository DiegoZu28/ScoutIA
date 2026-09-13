import { Component, effect, inject, input, signal } from '@angular/core';

import { FichaJugador, ScoutiaApiService } from '../../../../core/api/scoutia-api.service';
import { ErrorMessageComponent } from '../../../../shared/ui/error-message/error-message.component';
import { LoadingSpinnerComponent } from '../../../../shared/ui/loading-spinner/loading-spinner.component';
import { ArquetipoJugadorComponent } from '../arquetipo-jugador/arquetipo-jugador.component';
import { BandaValorComponent } from '../banda-valor/banda-valor.component';
import { IdentidadJugadorComponent } from '../identidad-jugador/identidad-jugador.component';
import { RadarPercentilesComponent } from '../radar-percentiles/radar-percentiles.component';
import { RendimientoHistoricoComponent } from '../rendimiento-historico/rendimiento-historico.component';
import { ValorHistoricoComponent } from '../valor-historico/valor-historico.component';

@Component({
  selector: 'app-ficha-jugador',
  standalone: true,
  imports: [
    LoadingSpinnerComponent,
    ErrorMessageComponent,
    IdentidadJugadorComponent,
    BandaValorComponent,
    RadarPercentilesComponent,
    ArquetipoJugadorComponent,
    RendimientoHistoricoComponent,
    ValorHistoricoComponent,
  ],
  templateUrl: './ficha-jugador.component.html',
})
export class FichaJugadorComponent {
  private readonly api = inject(ScoutiaApiService);

  playerId = input.required<string>();

  cargando = signal(false);
  error = signal<string | null>(null);
  ficha = signal<FichaJugador | null>(null);

  constructor() {
    effect(() => {
      const id = this.playerId();
      this.cargando.set(true);
      this.error.set(null);
      this.ficha.set(null);

      this.api.obtenerFicha(id).subscribe({
        next: (ficha) => {
          this.ficha.set(ficha);
          this.cargando.set(false);
        },
        error: () => {
          this.error.set('No se pudo cargar la información de este jugador.');
          this.cargando.set(false);
        },
      });
    });
  }
}
