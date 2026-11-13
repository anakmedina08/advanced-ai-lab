import type { DeteccionOut } from "../api/types";
import { porcentaje } from "../foto/validar";

interface Props {
  src: string;
  ancho: number;
  alto: number;
  detecciones: DeteccionOut[];
}

/** Imagen (ya difuminada por la API) con las cajas de YOLO en SVG escalable y su confianza. */
export default function CajasDeteccion({ src, ancho, alto, detecciones }: Props) {
  const grosor = Math.max(2, Math.round(Math.max(ancho, alto) / 300));
  const letra = Math.max(14, Math.round(Math.max(ancho, alto) / 45));
  return (
    <figure className="cajas">
      <svg viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label={`Foto con ${detecciones.length} objetos detectados`}>
        <image href={src} width={ancho} height={alto} />
        {detecciones.map((d, i) => {
          const { x_min, y_min, x_max, y_max } = d.caja;
          const texto = `${d.etiqueta} ${porcentaje(d.confianza)}`;
          return (
            <g key={`${d.clase}-${i}`}>
              <rect x={x_min} y={y_min} width={x_max - x_min} height={y_max - y_min} className="caja" strokeWidth={grosor} />
              <rect x={x_min} y={Math.max(0, y_min - letra * 1.4)} width={texto.length * letra * 0.6} height={letra * 1.4} className="etiqueta-fondo" />
              <text x={x_min + 4} y={Math.max(letra, y_min - letra * 0.35)} fontSize={letra} className="etiqueta">
                {texto}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
