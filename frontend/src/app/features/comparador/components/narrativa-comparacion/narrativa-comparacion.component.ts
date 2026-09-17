import { Component, effect, inject, input, signal } from '@angular/core';

import { NarrativaComparacion, ScoutiaApiService } from '../../../../core/api/scoutia-api.service';
import { ErrorMessageComponent } from '../../../../shared/ui/error-message/error-message.component';
import { LoadingSpinnerComponent } from '../../../../shared/ui/loading-spinner/loading-spinner.component';
import { COLOR_JUGADOR_A, COLOR_JUGADOR_B } from '../../colores-comparador';

@Component({
  selector: 'app-narrativa-comparacion',
  standalone: true,
  imports: [LoadingSpinnerComponent, ErrorMessageComponent],
  templateUrl: './narrativa-comparacion.component.html',
})
export class NarrativaComparacionComponent {
  private readonly api = inject(ScoutiaApiService);

  jugadorAId = input.required<string>();
  jugadorBId = input.required<string>();
  nombreA = input.required<string>();
  nombreB = input.required<string>();

  readonly colorA = COLOR_JUGADOR_A;
  readonly colorB = COLOR_JUGADOR_B;

  cargando = signal(false);
  error = signal<string | null>(null);
  narrativa = signal<NarrativaComparacion | null>(null);

  constructor() {
    // Cambiar de pareja de jugadores invalida cualquier narrativa ya generada, pero no
    // dispara sola una nueva llamada al LLM: eso lo decide el usuario con el botón.
    effect(() => {
      this.jugadorAId();
      this.jugadorBId();
      this.narrativa.set(null);
      this.error.set(null);
      this.cargando.set(false);
    });
  }

  generar(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.narrativa.set(null);

    this.api.obtenerNarrativaComparacion(this.jugadorAId(), this.jugadorBId()).subscribe({
      next: (narrativa) => {
        this.narrativa.set(narrativa);
        this.cargando.set(false);
      },
      error: (err) => {
        this.error.set(
          err?.status === 503
            ? 'El análisis con IA no está disponible en este momento (falta configurar el servicio).'
            : 'No se pudo generar el análisis con IA.',
        );
        this.cargando.set(false);
      },
    });
  }
}
