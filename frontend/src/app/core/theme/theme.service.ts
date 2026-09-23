import { Injectable, effect, signal } from '@angular/core';

export type Tema = 'claro' | 'oscuro';

const STORAGE_KEY = 'scoutia-tema';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly tema = signal<Tema>(this.temaInicial());

  constructor() {
    effect(() => {
      const oscuro = this.tema() === 'oscuro';
      document.documentElement.classList.toggle('dark', oscuro);
      try {
        localStorage.setItem(STORAGE_KEY, this.tema());
      } catch {
        // localStorage puede no estar disponible (modo privado, etc.) — el tema sigue
        // funcionando para la sesión actual, solo no se recuerda al recargar.
      }
    });
  }

  alternar(): void {
    this.tema.set(this.tema() === 'oscuro' ? 'claro' : 'oscuro');
  }

  private temaInicial(): Tema {
    try {
      const guardado = localStorage.getItem(STORAGE_KEY);
      if (guardado === 'claro' || guardado === 'oscuro') return guardado;
    } catch {
      // ignorar y usar la preferencia del sistema
    }
    return matchMedia('(prefers-color-scheme: dark)').matches ? 'oscuro' : 'claro';
  }
}
