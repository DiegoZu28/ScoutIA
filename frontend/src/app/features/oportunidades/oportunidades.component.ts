import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ListaOportunidades, ScoutiaApiService } from '../../core/api/scoutia-api.service';
import { ErrorMessageComponent } from '../../shared/ui/error-message/error-message.component';
import { LoadingSpinnerComponent } from '../../shared/ui/loading-spinner/loading-spinner.component';
import { AvatarJugadorComponent } from '../../shared/ui/avatar-jugador/avatar-jugador.component';

// Mismas 13 etiquetas que POSICIONES_DETALLADAS en app/src/app/domain/posiciones.py
// (posicion_tm ya viene traducida al español desde el backend) -- si esa lista cambia,
// actualizar acá también.
const POSICIONES = [
  'Portero',
  'Defensa central',
  'Lateral izquierdo',
  'Lateral derecho',
  'Pivote',
  'Centrocampista',
  'Mediapunta',
  'Interior izquierdo',
  'Interior derecho',
  'Extremo izquierdo',
  'Extremo derecho',
  'Segundo delantero',
  'Delantero centro',
];

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
  posiciones = POSICIONES;
  posicionSeleccionada = signal<string>('');

  constructor() {
    this.cargar();
  }

  filtrarPorPosicion(posicion: string): void {
    this.posicionSeleccionada.set(posicion);
    this.cargar();
  }

  private cargar(): void {
    this.cargando.set(true);
    this.error.set(null);

    this.api.obtenerOportunidades(30, this.posicionSeleccionada() || undefined).subscribe({
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
