import { Component, computed, input } from '@angular/core';

import { PrediccionValor } from '../../../../core/api/scoutia-api.service';

@Component({
  selector: 'app-banda-valor',
  standalone: true,
  templateUrl: './banda-valor.component.html',
})
export class BandaValorComponent {
  prediccion = input.required<PrediccionValor>();

  readonly maxAbsContribucion = computed(() =>
    Math.max(...this.prediccion().contribuciones.map((c) => Math.abs(c.contribucion_log)), 0.001),
  );

  anchoBarra(contribucionLog: number): number {
    return (Math.abs(contribucionLog) / this.maxAbsContribucion()) * 100;
  }

  formatoEur(valor: number): string {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(valor);
  }
}
