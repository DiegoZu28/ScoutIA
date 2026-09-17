import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';

import { GrupoComparacion, PercentilComparado } from '../../../../core/api/scoutia-api.service';
import { RadarChartComponent, SerieRadar } from '../../../../viz/radar-chart/radar-chart.component';
import { COLOR_JUGADOR_A, COLOR_JUGADOR_B } from '../../colores-comparador';

@Component({
  selector: 'app-comparacion-percentiles',
  standalone: true,
  imports: [RadarChartComponent, DecimalPipe],
  templateUrl: './comparacion-percentiles.component.html',
})
export class ComparacionPercentilesComponent {
  percentiles = input.required<PercentilComparado[]>();
  grupoA = input.required<GrupoComparacion>();
  grupoB = input.required<GrupoComparacion>();
  nombreA = input.required<string>();
  nombreB = input.required<string>();

  readonly mismaPosicion = computed(() => this.grupoA().posicion === this.grupoB().posicion);

  readonly series = computed<SerieRadar[]>(() => [
    {
      etiqueta: this.nombreA(),
      color: COLOR_JUGADOR_A,
      puntos: this.percentiles().map((p) => ({ etiqueta: p.etiqueta, percentil: p.percentil_a })),
    },
    {
      etiqueta: this.nombreB(),
      color: COLOR_JUGADOR_B,
      puntos: this.percentiles().map((p) => ({ etiqueta: p.etiqueta, percentil: p.percentil_b })),
    },
  ]);
}
