import { Component, computed, input } from '@angular/core';

import { PercentilesJugador } from '../../../../core/api/scoutia-api.service';
import { RadarChartComponent, SerieRadar } from '../../../../viz/radar-chart/radar-chart.component';

const COLOR_SERIE_UNICA = '#4263eb';

@Component({
  selector: 'app-radar-percentiles',
  standalone: true,
  imports: [RadarChartComponent],
  templateUrl: './radar-percentiles.component.html',
})
export class RadarPercentilesComponent {
  percentiles = input.required<PercentilesJugador>();

  readonly series = computed<SerieRadar[]>(() => [
    {
      etiqueta: 'Percentil',
      color: COLOR_SERIE_UNICA,
      puntos: this.percentiles().percentiles.map((p) => ({
        etiqueta: p.etiqueta,
        percentil: p.percentil,
      })),
    },
  ]);
}
