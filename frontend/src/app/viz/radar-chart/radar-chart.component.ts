import { Component, computed, input } from '@angular/core';

export interface PuntoRadar {
  etiqueta: string;
  percentil: number; // 0..1
}

export interface SerieRadar {
  etiqueta: string;
  color: string; // hex, ej. '#4f46e5'
  puntos: PuntoRadar[]; // mismos ejes y mismo orden entre series
}

interface EjeRadar {
  etiqueta: string;
  angulo: number;
}

const ANILLOS = [0.25, 0.5, 0.75, 1];

@Component({
  selector: 'app-radar-chart',
  standalone: true,
  templateUrl: './radar-chart.component.html',
})
export class RadarChartComponent {
  series = input.required<SerieRadar[]>();
  size = input(320);

  readonly anillos = ANILLOS;

  private readonly centro = computed(() => this.size() / 2);
  private readonly radioMax = computed(() => this.size() / 2 - 50);

  readonly ejes = computed<EjeRadar[]>(() => {
    const puntosReferencia = this.series()[0]?.puntos ?? [];
    const n = puntosReferencia.length;
    return puntosReferencia.map((punto, i) => ({
      etiqueta: punto.etiqueta,
      angulo: (2 * Math.PI * i) / n - Math.PI / 2,
    }));
  });

  poligonoPath(serie: SerieRadar): string {
    const ejes = this.ejes();
    return serie.puntos
      .map((punto, i) => this.coordenadaStr(ejes[i].angulo, this.radioMax() * punto.percentil))
      .join(' ');
  }

  private coordenada(angulo: number, radio: number): { x: number; y: number } {
    const c = this.centro();
    return { x: c + radio * Math.cos(angulo), y: c + radio * Math.sin(angulo) };
  }

  private coordenadaStr(angulo: number, radio: number): string {
    const { x, y } = this.coordenada(angulo, radio);
    return `${x},${y}`;
  }

  anilloPath(fraccion: number): string {
    return this.ejes()
      .map((eje) => this.coordenadaStr(eje.angulo, this.radioMax() * fraccion))
      .join(' ');
  }

  lineaEjeX2(eje: EjeRadar): number {
    return this.coordenada(eje.angulo, this.radioMax()).x;
  }

  lineaEjeY2(eje: EjeRadar): number {
    return this.coordenada(eje.angulo, this.radioMax()).y;
  }

  etiquetaX(eje: EjeRadar): number {
    return this.coordenada(eje.angulo, this.radioMax() + 26).x;
  }

  etiquetaY(eje: EjeRadar): number {
    return this.coordenada(eje.angulo, this.radioMax() + 26).y;
  }

  get centroValor(): number {
    return this.centro();
  }
}
