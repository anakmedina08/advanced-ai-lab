import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, obtener, pedir, streamAgente } from "./client";
import { ParserSSE } from "./sse";

function cuerpoSSE(trozos: string[]): ReadableStream<Uint8Array> {
  const codificador = new TextEncoder();
  return new ReadableStream({
    start(control) {
      trozos.forEach((t) => control.enqueue(codificador.encode(t)));
      control.close();
    },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("ParserSSE", () => {
  it("arma eventos completos aunque lleguen partidos", () => {
    // Arrange
    const parser = new ParserSSE();
    // Act
    const a = parser.agregar('event: texto\ndata: {"del');
    const b = parser.agregar('ta":"Ho"}\n\nevent: texto\ndata: {"delta":"la"}\n\n');
    // Assert
    expect(a).toEqual([]);
    expect(b.map((e) => JSON.parse(e.datos).delta)).toEqual(["Ho", "la"]);
  });

  it("acepta saltos de línea de Windows", () => {
    // Act
    const eventos = new ParserSSE().agregar("event: final\r\ndata: {}\r\n\r\n");
    // Assert
    expect(eventos).toEqual([{ evento: "final", datos: "{}" }]);
  });
});

describe("cliente de la API", () => {
  it("traduce ErrorOut a ApiError con su request id", async () => {
    // Arrange
    const cuerpo = { error: "validacion", detalle: [{ campo: "mensaje", mensaje: "vacío" }], ruta: "/x", request_id: "r1" };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(cuerpo), { status: 422 })));
    // Act
    const error = await pedir("/x").catch((e) => e);
    // Assert
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 422, codigo: "validacion", detalle: "mensaje: vacío", requestId: "r1" });
  });

  it("un fallo de red se informa como error legible", async () => {
    // Arrange
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("Failed to fetch"))));
    // Act
    const error = await pedir("/health").catch((e) => e);
    // Assert
    expect(error).toMatchObject({ status: 0, codigo: "red" });
  });

  it("reintenta los GET ante un 503 y luego responde", async () => {
    // Arrange
    const falso = vi
      .fn()
      .mockResolvedValueOnce(new Response("{}", { status: 503 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    vi.stubGlobal("fetch", falso);
    // Act
    const r = await obtener<{ status: string }>("/health", 1);
    // Assert
    expect(r.status).toBe("ok");
    expect(falso).toHaveBeenCalledTimes(2);
  });

  it("no reintenta un 404", async () => {
    // Arrange
    const falso = vi.fn(async () => new Response(JSON.stringify({ error: "no_encontrado" }), { status: 404 }));
    vi.stubGlobal("fetch", falso);
    // Act
    await obtener("/nada").catch(() => undefined);
    // Assert
    expect(falso).toHaveBeenCalledTimes(1);
  });

  it("streamAgente entrega los eventos tipados en orden", async () => {
    // Arrange
    const sse = cuerpoSSE([
      'event: router\ndata: {"tipo":"router","ruta":"rag","confianza":0.8,"senales":[],"tools":[],"cautela":false}\n\n',
      'event: texto\ndata: {"tipo":"texto","delta":"Hola"}\n\nevent: fin',
      'al\ndata: {"tipo":"final","turno":{}}\n\n',
    ]);
    vi.stubGlobal("fetch", vi.fn(async () => new Response(sse, { status: 200 })));
    // Act
    const tipos: string[] = [];
    for await (const e of streamAgente({ mensaje: "hola", conversacion_id: "hilo-001" })) tipos.push(e.tipo);
    // Assert
    expect(tipos).toEqual(["router", "texto", "final"]);
  });
});
