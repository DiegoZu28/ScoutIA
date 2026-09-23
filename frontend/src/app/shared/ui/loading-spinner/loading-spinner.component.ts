import { Component } from '@angular/core';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  template: `
    <div class="flex items-center justify-center gap-2 py-6 text-slate-500 dark:text-slate-400">
      <span
        class="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600 dark:border-slate-600 dark:border-t-slate-300"
      ></span>
      <span class="text-sm">Cargando…</span>
    </div>
  `,
})
export class LoadingSpinnerComponent {}
