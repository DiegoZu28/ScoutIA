import { Component, input } from '@angular/core';

import { ArquetipoComparado } from '../../../../core/api/scoutia-api.service';
import { COLOR_JUGADOR_A, COLOR_JUGADOR_B } from '../../colores-comparador';

@Component({
  selector: 'app-comparacion-arquetipo',
  standalone: true,
  templateUrl: './comparacion-arquetipo.component.html',
})
export class ComparacionArquetipoComponent {
  arquetipo = input.required<ArquetipoComparado>();
  nombreA = input.required<string>();
  nombreB = input.required<string>();

  readonly colorA = COLOR_JUGADOR_A;
  readonly colorB = COLOR_JUGADOR_B;
}
