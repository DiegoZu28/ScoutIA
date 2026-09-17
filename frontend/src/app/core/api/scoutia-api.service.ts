import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config/api-base-url';
import type { components } from './schema.d.ts';

export type JugadorBusqueda = components['schemas']['JugadorBusqueda'];
export type EstadisticasJugador = components['schemas']['EstadisticasJugador'];
export type PrediccionValor = components['schemas']['PrediccionValor'];
export type ContribucionVariable = components['schemas']['ContribucionVariable'];
export type PercentilesJugador = components['schemas']['PercentilesJugador'];
export type GrupoComparacion = components['schemas']['GrupoComparacion'];
export type ArquetipoJugador = components['schemas']['ArquetipoJugador'];
export type HistorialJugador = components['schemas']['HistorialJugador'];
export type TemporadaRendimiento = components['schemas']['TemporadaRendimiento'];
export type ComparacionJugadores = components['schemas']['ComparacionJugadores'];
export type PercentilComparado = components['schemas']['PercentilComparado'];
export type ContribucionComparada = components['schemas']['ContribucionComparada'];
export type ValorComparado = components['schemas']['ValorComparado'];
export type ArquetipoComparado = components['schemas']['ArquetipoComparado'];
export type NarrativaComparacion = components['schemas']['NarrativaComparacion'];

export interface FichaJugador {
  estadisticas: EstadisticasJugador;
  valor: PrediccionValor;
  percentiles: PercentilesJugador;
  arquetipo: ArquetipoJugador;
  historial: HistorialJugador;
}

@Injectable({ providedIn: 'root' })
export class ScoutiaApiService {
  private readonly http = inject(HttpClient);

  buscarJugador(query: string, limit = 20): Observable<JugadorBusqueda[]> {
    const params = new HttpParams().set('q', query).set('limit', limit);
    return this.http.get<JugadorBusqueda[]>(`${API_BASE_URL}/jugadores/buscar`, { params });
  }

  obtenerFicha(playerId: string, temporada?: number): Observable<FichaJugador> {
    let params = new HttpParams();
    if (temporada !== undefined) {
      params = params.set('temporada', temporada);
    }
    return this.http.get<FichaJugador>(`${API_BASE_URL}/jugadores/${playerId}/ficha`, { params });
  }

  compararJugadores(
    jugadorA: string,
    jugadorB: string,
    temporadaA?: number,
    temporadaB?: number,
  ): Observable<ComparacionJugadores> {
    const params = this.paramsComparacion(jugadorA, jugadorB, temporadaA, temporadaB);
    return this.http.get<ComparacionJugadores>(`${API_BASE_URL}/jugadores/comparar`, { params });
  }

  obtenerNarrativaComparacion(
    jugadorA: string,
    jugadorB: string,
    temporadaA?: number,
    temporadaB?: number,
  ): Observable<NarrativaComparacion> {
    const params = this.paramsComparacion(jugadorA, jugadorB, temporadaA, temporadaB);
    return this.http.get<NarrativaComparacion>(`${API_BASE_URL}/jugadores/comparar/narrativa`, { params });
  }

  private paramsComparacion(
    jugadorA: string,
    jugadorB: string,
    temporadaA?: number,
    temporadaB?: number,
  ): HttpParams {
    let params = new HttpParams().set('jugador_a', jugadorA).set('jugador_b', jugadorB);
    if (temporadaA !== undefined) {
      params = params.set('temporada_a', temporadaA);
    }
    if (temporadaB !== undefined) {
      params = params.set('temporada_b', temporadaB);
    }
    return params;
  }
}
