/** Validación de la foto en el navegador, antes de llamar a la API (mismo límite que el backend). */

export const MAX_BYTES = 8 * 1024 * 1024;
export const TIPOS = ["image/jpeg", "image/png"];

export function validarFoto(archivo: File): string | null {
  if (!TIPOS.includes(archivo.type)) return "El archivo debe ser una imagen JPG o PNG.";
  if (archivo.size > MAX_BYTES) {
    const mb = (archivo.size / 1024 / 1024).toFixed(1);
    return `La foto pesa ${mb} MB; el máximo es 8 MB.`;
  }
  if (archivo.size === 0) return "El archivo está vacío.";
  return null;
}

export const porcentaje = (confianza: number) => `${Math.round(confianza * 100)} %`;
