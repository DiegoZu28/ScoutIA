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

  readonly maxAbsDiferencia = computed(() =>
    Math.max(...this.valor().contribuciones_diferencia.map((c) => Math.abs(c.diferencia_log)), 0.001),
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
