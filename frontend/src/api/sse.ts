/**
 * Lector incremental de Server-Sent Events.
 *
 * `EventSource` no admite POST con cuerpo JSON, así que se lee el cuerpo de `fetch` como
 * `ReadableStream` y se separan los bloques `event: …\ndata: …\n\n`, aunque lleguen partidos en
 * trozos arbitrarios de la red.
 */

export interface EventoSSE {
  evento: string;
  datos: string;
}

/** Acumula texto y devuelve los eventos completos que ya llegaron. */
export class ParserSSE {
  private buffer = "";

  agregar(trozo: string): EventoSSE[] {
    this.buffer += trozo.replace(/\r\n/g, "\n");
    const eventos: EventoSSE[] = [];
    let corte = this.buffer.indexOf("\n\n");
    while (corte !== -1) {
      const bloque = this.buffer.slice(0, corte);
      this.buffer = this.buffer.slice(corte + 2);
      const evento = ParserSSE.bloque(bloque);
      if (evento) eventos.push(evento);
      corte = this.buffer.indexOf("\n\n");
    }
    return eventos;
  }

  private static bloque(bloque: string): EventoSSE | null {
    let evento = "message";
    const datos: string[] = [];
    for (const linea of bloque.split("\n")) {
      if (linea.startsWith("event:")) evento = linea.slice(6).trim();
      else if (linea.startsWith("data:")) datos.push(linea.slice(5).replace(/^ /, ""));
    }
    return datos.length ? { evento, datos: datos.join("\n") } : null;
  }
}

/** Recorre un `ReadableStream` de bytes y entrega los eventos SSE en orden. */
export async function* leerSSE(cuerpo: ReadableStream<Uint8Array>): AsyncGenerator<EventoSSE> {
  const lector = cuerpo.getReader();
  const decodificador = new TextDecoder("utf-8");
  const parser = new ParserSSE();
  try {
    while (true) {
      const { value, done } = await lector.read();
      if (done) break;
      yield* parser.agregar(decodificador.decode(value, { stream: true }));
    }
    yield* parser.agregar(decodificador.decode() + "\n\n");
  } finally {
    lector.releaseLock();
  }
}
