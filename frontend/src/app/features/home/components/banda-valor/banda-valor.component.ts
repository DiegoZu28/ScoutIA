import { Component, computed, input } from '@angular/core';

import { PrediccionValor } from '../../../../core/api/scoutia-api.service';

@Component({
  selector: 'app-banda-valor',
  standalone: true,
  templateUrl: './banda-valor.component.html',
})
export class BandaValorComponent {
  prediccion = input.required<PrediccionValor>();

  // Las variables flag_* (ej. "Sin registro de titularidades") son indicadores de calidad
  // de datos, no estadísticas de juego -- no tiene sentido mostrárselas a un scout como
  // "variable que influye en el valor".
  readonly contribucionesVisibles = computed(() =>
    this.prediccion().contribuciones.filter((c) => !c.feature.startsWith('flag_')),
  );

  readonly maxAbsContribucion = computed(() =>
    Math.max(...this.contribucionesVisibles().map((c) => Math.abs(c.contribucion_log)), 0.001),
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
