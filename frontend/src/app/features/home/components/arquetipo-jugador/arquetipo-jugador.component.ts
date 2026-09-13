import { Component, input } from '@angular/core';

import { ArquetipoJugador } from '../../../../core/api/scoutia-api.service';

@Component({
  selector: 'app-arquetipo-jugador',
  standalone: true,
  templateUrl: './arquetipo-jugador.component.html',
})
export class ArquetipoJugadorComponent {
  arquetipo = input.required<ArquetipoJugador>();
}
