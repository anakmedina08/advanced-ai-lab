import { useState } from "react";

import Chat from "./Chat";

/** Página principal: un hilo de chat (la lista de hilos y la memoria llegan en SPEC-025). */
export default function Inicio() {
  const [conversacionId] = useState(() => `hilo-${crypto.randomUUID().slice(0, 12)}`);
  return <Chat conversacionId={conversacionId} usuarioId={null} />;
}
