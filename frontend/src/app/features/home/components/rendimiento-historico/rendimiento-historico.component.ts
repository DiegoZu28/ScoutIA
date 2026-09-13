import { Component, computed, input, signal } from '@angular/core';

import { HistorialJugador } from '../../../../core/api/scoutia-api.service';
import { LineChartComponent, PuntoLinea } from '../../../../viz/line-chart/line-chart.component';

type StatKey = 'goles' | 'tiros' | 'tarjetas_amarillas' | 'asistencias';

interface OpcionStat {
  clave: StatKey;
  etiqueta: string;
  color: string;
}

const OPCIONES: OpcionStat[] = [
  { clave: 'goles', etiqueta: 'Goles', color: '#2b8a3e' },
  { clave: 'tiros', etiqueta: 'Tiros', color: '#4263eb' },
  { clave: 'tarjetas_amarillas', etiqueta: 'Tarjetas amarillas', color: '#f08c00' },
  { clave: 'asistencias', etiqueta: 'Asistencias', color: '#7048e8' },
];

@Component({
  selector: 'app-rendimiento-historico',
  standalone: true,
  imports: [LineChartComponent],
  templateUrl: './rendimiento-historico.component.html',
})
export class RendimientoHistoricoComponent {
  historial = input.required<HistorialJugador>();

  readonly opciones = OPCIONES;
  readonly statSeleccionado = signal<StatKey>('goles');

  readonly opcionActual = computed(
    () => this.opciones.find((o) => o.clave === this.statSeleccionado())!,
  );

  readonly puntos = computed<PuntoLinea[]>(() => {
    const clave = this.statSeleccionado();
    return this.historial().temporadas.map((t) => ({
      etiqueta: t.temporada.split('-').map((anio) => anio.slice(2)).join('-'),
      valor: t[clave],
    }));
  });

  elegir(clave: StatKey): void {
    this.statSeleccionado.set(clave);
  }

  formatoEntero = (v: number) => Math.round(v).toString();
}
