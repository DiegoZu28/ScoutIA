import { Component, computed, input } from '@angular/core';

import { HistorialJugador } from '../../../../core/api/scoutia-api.service';
import { LineChartComponent, PuntoLinea } from '../../../../viz/line-chart/line-chart.component';

@Component({
  selector: 'app-valor-historico',
  standalone: true,
  imports: [LineChartComponent],
  templateUrl: './valor-historico.component.html',
})
export class ValorHistoricoComponent {
  historial = input.required<HistorialJugador>();

  readonly puntos = computed<PuntoLinea[]>(() =>
    this.historial().temporadas.map((t) => ({
      etiqueta: t.temporada
        .split('-')
        .map((anio) => anio.slice(2))
        .join('-'),
      valor: t.valor_mercado_eur,
    })),
  );

  formatoCompacto = (v: number): string => {
    if (Math.abs(v) >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    if (Math.abs(v) >= 1_000) return `${(v / 1_000).toFixed(0)}k`;
    return `${Math.round(v)}`;
  };
}
