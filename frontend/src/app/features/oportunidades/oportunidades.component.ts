import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ListaOportunidades, ScoutiaApiService } from '../../core/api/scoutia-api.service';
import { ErrorMessageComponent } from '../../shared/ui/error-message/error-message.component';
import { LoadingSpinnerComponent } from '../../shared/ui/loading-spinner/loading-spinner.component';
import { AvatarJugadorComponent } from '../../shared/ui/avatar-jugador/avatar-jugador.component';

@Component({
  selector: 'app-oportunidades',
  standalone: true,
  imports: [LoadingSpinnerComponent, ErrorMessageComponent, AvatarJugadorComponent, RouterLink],
  templateUrl: './oportunidades.component.html',
})
export class OportunidadesComponent {
  private readonly api = inject(ScoutiaApiService);

  cargando = signal(false);
  error = signal<string | null>(null);
  datos = signal<ListaOportunidades | null>(null);

  constructor() {
    this.cargar();
  }

  private cargar(): void {
    this.cargando.set(true);
    this.error.set(null);

    this.api.obtenerOportunidades(30).subscribe({
      next: (datos) => {
        this.datos.set(datos);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar la lista de casos a revisión manual.');
        this.cargando.set(false);
      },
    });
  }

  formatoEur(valor: number): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(valor);
  }

  formatoPct(valor: number): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'percent',
      maximumFractionDigits: 0,
    }).format(valor);
  }
}
