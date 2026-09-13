import { Component, input } from '@angular/core';

@Component({
  selector: 'app-error-message',
  standalone: true,
  template: `
    <div class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ mensaje() }}
    </div>
  `,
})
export class ErrorMessageComponent {
  mensaje = input('Ocurrió un error inesperado.');
}
