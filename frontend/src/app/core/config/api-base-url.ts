// Relativa a propósito: en dev, `ng serve --proxy-config proxy.conf.json` la reenvía a
// localhost:8000; en producción, FastAPI sirve el build de Angular y la API desde el mismo
// origen. Así funciona igual en localhost, en la red local o detrás de un túnel público,
// sin hardcodear un host.
export const API_BASE_URL = '/api/v1';
