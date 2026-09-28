import { Component, computed, input } from '@angular/core';

import { ValorComparado } from '../../../../core/api/scoutia-api.service';
import { COLOR_JUGADOR_A, COLOR_JUGADOR_B } from '../../colores-comparador';

@Component({
  selector: 'app-comparacion-valor',
  standalone: true,
  templateUrl: './comparacion-valor.component.html',
})
export class ComparacionValorComponent {
  valor = input.required<ValorComparado>();
  nombreA = input.required<string>();
  nombreB = input.required<string>();

  readonly colorA = COLOR_JUGADOR_A;
  readonly colorB = COLOR_JUGADOR_B;

  // Las variables flag_* (ej. "Sin registro de titularidades") son indicadores de calidad
  // de datos, no estadísticas de juego -- no tiene sentido mostrárselas a un scout como
  // "variable que explica la diferencia de valor".
  readonly contribucionesVisibles = computed(() =>
    this.valor().contribuciones_diferencia.filter((c) => !c.feature.startsWith('flag_')),
  );

  readonly maxAbsDiferencia = computed(() =>
    Math.max(...this.contribucionesVisibles().map((c) => Math.abs(c.diferencia_log)), 0.001),
  );

  anchoBarra(diferenciaLog: number): number {
    return (Math.abs(diferenciaLog) / this.maxAbsDiferencia()) * 100;
  }

  colorFactor(diferenciaLog: number): string {
    return diferenciaLog > 0 ? this.colorA : this.colorB;
  }

  formatoEur(valor: number): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(valor);
  }
}
