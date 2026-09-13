import { Component, computed, input } from '@angular/core';

import { PercentilesJugador } from '../../../../core/api/scoutia-api.service';
import { PuntoRadar, RadarChartComponent } from '../../../../viz/radar-chart/radar-chart.component';

@Component({
  selector: 'app-radar-percentiles',
  standalone: true,
  imports: [RadarChartComponent],
  templateUrl: './radar-percentiles.component.html',
})
export class RadarPercentilesComponent {
  percentiles = input.required<PercentilesJugador>();

  readonly puntos = computed<PuntoRadar[]>(() =>
    this.percentiles().percentiles.map((p) => ({
      etiqueta: p.etiqueta,
      percentil: p.percentil,
    })),
  );
}
