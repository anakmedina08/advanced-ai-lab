/** Ícono de Material Symbols. Decorativo: el texto va aparte. */
export default function Icono({ nombre, className = "" }: { nombre: string; className?: string }) {
  return (
    <span className={`material-symbols-rounded ${className}`} aria-hidden="true">
      {nombre}
    </span>
  );
}
