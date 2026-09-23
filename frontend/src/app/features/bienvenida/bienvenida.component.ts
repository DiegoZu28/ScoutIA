import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ResumenDataset, ScoutiaApiService } from '../../core/api/scoutia-api.service';
import { ErrorMessageComponent } from '../../shared/ui/error-message/error-message.component';
import { LoadingSpinnerComponent } from '../../shared/ui/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-bienvenida',
  standalone: true,
  imports: [RouterLink, LoadingSpinnerComponent, ErrorMessageComponent],
  templateUrl: './bienvenida.component.html',
})
export class BienvenidaComponent {
  private readonly api = inject(ScoutiaApiService);

  cargando = signal(false);
  error = signal<string | null>(null);
  resumen = signal<ResumenDataset | null>(null);

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.cargando.set(true);
    this.error.set(null);

    this.api.obtenerResumen().subscribe({
      next: (resumen) => {
        this.resumen.set(resumen);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar las cifras del dataset.');
        this.cargando.set(false);
      },
    });
  }

  formatoMiles(valor: number): string {
    return new Intl.NumberFormat('es-ES').format(valor);
  }

  temporadaCorta(temporada: string): string {
    return temporada
      .split('-')
      .map((anio) => anio.slice(2))
      .join('-');
  }
}
