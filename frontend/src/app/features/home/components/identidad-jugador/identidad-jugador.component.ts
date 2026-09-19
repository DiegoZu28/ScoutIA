import { Component, computed, input } from '@angular/core';

import { EstadisticasJugador } from '../../../../core/api/scoutia-api.service';
import { AvatarJugadorComponent } from '../../../../shared/ui/avatar-jugador/avatar-jugador.component';

@Component({
  selector: 'app-identidad-jugador',
  standalone: true,
  imports: [AvatarJugadorComponent],
  templateUrl: './identidad-jugador.component.html',
})
export class IdentidadJugadorComponent {
  estadisticas = input.required<EstadisticasJugador>();

  readonly contratoTexto = computed(() => {
    const est = this.estadisticas();
    if (!est.contrato_conocido || est.dias_contrato_restante == null) {
      return 'Desconocido';
    }
    const dias = est.dias_contrato_restante;
    if (dias < 0) {
      return 'Vencido (en renovación o situación libre)';
    }
    const anios = Math.floor(dias / 365);
    const meses = Math.round((dias % 365) / 30);
    if (anios === 0) {
      return `${meses} mes${meses === 1 ? '' : 'es'}`;
    }
    return `${anios} año${anios === 1 ? '' : 's'}${meses > 0 ? ` ${meses} mes${meses === 1 ? '' : 'es'}` : ''}`;
  });
}
