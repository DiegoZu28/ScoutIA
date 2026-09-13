import { Component, computed, input } from '@angular/core';

export interface PuntoLinea {
  etiqueta: string;
  valor: number;
}

const ANCHO = 480;
const ALTO = 220;
const MARGEN = { top: 16, right: 16, bottom: 28, left: 48 };

@Component({
  selector: 'app-line-chart',
  standalone: true,
  templateUrl: './line-chart.component.html',
})
export class LineChartComponent {
  puntos = input.required<PuntoLinea[]>();
  colorLinea = input('#4263eb');
  formatoValor = input<(v: number) => string>((v) => `${v}`);

  readonly ancho = ANCHO;
  readonly alto = ALTO;

  private readonly anchoUtil = ANCHO - MARGEN.left - MARGEN.right;
  private readonly altoUtil = ALTO - MARGEN.top - MARGEN.bottom;

  private readonly rango = computed(() => {
    const valores = this.puntos().map((p) => p.valor);
    const min = Math.min(...valores, 0);
    const max = Math.max(...valores, 1);
    return { min, max: max === min ? min + 1 : max };
  });

  private x(indice: number): number {
    const n = this.puntos().length;
    if (n <= 1) return MARGEN.left + this.anchoUtil / 2;
    return MARGEN.left + (indice / (n - 1)) * this.anchoUtil;
  }

  private y(valor: number): number {
    const { min, max } = this.rango();
    const frac = (valor - min) / (max - min);
    return MARGEN.top + this.altoUtil * (1 - frac);
  }

  readonly puntosSvg = computed(() =>
    this.puntos().map((p, i) => ({ ...p, x: this.x(i), y: this.y(p.valor) })),
  );

  readonly lineaPath = computed(() =>
    this.puntosSvg()
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`)
      .join(' '),
  );

  readonly lineasGuia = computed(() => {
    const { min, max } = this.rango();
    const pasos = 4;
    return Array.from({ length: pasos + 1 }, (_, i) => {
      const valor = min + ((max - min) * i) / pasos;
      return { valor, y: this.y(valor) };
    });
  });

  readonly ejeXY = MARGEN.left;
  readonly ejeXAlto = ALTO - MARGEN.bottom;
  readonly ejeXAncho = ANCHO - MARGEN.right;
}
