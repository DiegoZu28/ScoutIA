import { Component, computed, effect, input, signal } from '@angular/core';

@Component({
  selector: 'app-avatar-jugador',
  standalone: true,
  templateUrl: './avatar-jugador.component.html',
})
export class AvatarJugadorComponent {
  nombre = input.required<string>();
  fotoUrl = input<string | null | undefined>(null);
  color = input<string>('#4f46e5');
  tamano = input<'sm' | 'md' | 'lg' | 'xl'>('md');
  forma = input<'circulo' | 'cuadro'>('circulo');

  private readonly fotoFallo = signal(false);

  readonly mostrarFoto = computed(() => !!this.fotoUrl() && !this.fotoFallo());

  constructor() {
    // Si cambia la URL (ej. al elegir otro jugador), reintenta la imagen.
    effect(() => {
      this.fotoUrl();
      this.fotoFallo.set(false);
    });
  }

  onErrorFoto(): void {
    this.fotoFallo.set(true);
  }

  readonly iniciales = computed(() => {
    const palabras = this.nombre().trim().split(/\s+/).filter(Boolean);
    if (palabras.length === 0) {
      return '?';
    }
    if (palabras.length === 1) {
      return palabras[0].slice(0, 2).toUpperCase();
    }
    return (palabras[0][0] + palabras[palabras.length - 1][0]).toUpperCase();
  });

  readonly claseTamano = computed(() => {
    switch (this.tamano()) {
      case 'xl':
        return 'h-24 w-24 text-2xl';
      case 'lg':
        return 'h-16 w-16 text-xl';
      case 'sm':
        return 'h-8 w-8 text-xs';
      default:
        return 'h-12 w-12 text-base';
    }
  });

  readonly claseForma = computed(() => (this.forma() === 'cuadro' ? 'rounded-xl' : 'rounded-full'));
}
