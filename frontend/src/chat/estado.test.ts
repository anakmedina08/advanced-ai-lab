import { describe, expect, it } from "vitest";

import type { AgenteOut } from "../api/types";
import { inicial, reducir, sinUltimoIntento } from "./estado";

const decision = { ruta: "rag" as const, confianza: 0.8, senales: [], tools: ["buscar_conocimiento"], cautela: false };

describe("reducer del chat", () => {
  it("enviar agrega la pregunta y una burbuja vacía del asistente", () => {
    // Act
    const e = reducir(inicial, { tipo: "enviar", texto: "¿Qué cubre el SOAT?", id: "1" });
    // Assert
    expect(e.fase).toBe("enviando");
    expect(e.mensajes.map((m) => m.rol)).toEqual(["usuario", "asistente"]);
  });

  it("los eventos de texto hacen crecer la respuesta antes del final", () => {
    // Arrange
    let e = reducir(inicial, { tipo: "enviar", texto: "hola", id: "1" });
    // Act
    e = reducir(e, { tipo: "evento", evento: { tipo: "router", ...decision } });
    e = reducir(e, { tipo: "evento", evento: { tipo: "texto", delta: "Hola, " } });
    e = reducir(e, { tipo: "evento", evento: { tipo: "texto", delta: "Ana" } });
    // Assert
    expect(e.fase).toBe("transmitiendo");
    expect(e.mensajes[1].texto).toBe("Hola, Ana");
    expect(e.mensajes[1].decision?.ruta).toBe("rag");
  });

  it("una tool muestra el paso actual y queda registrada", () => {
    // Arrange
    const e0 = reducir(inicial, { tipo: "enviar", texto: "x", id: "1" });
    // Act
    const e = reducir(e0, { tipo: "evento", evento: { tipo: "tool_inicio", tool: "consultar_datos", argumentos: {} } });
    // Assert
    expect(e.mensajes[1].pasoActual).toBe("Consultando los datos…");
    expect(e.mensajes[1].toolsUsadas).toEqual(["consultar_datos"]);
  });

  it("el evento final fija la respuesta validada y termina", () => {
    // Arrange
    const turno = { salida: { respuesta: "Texto final", fuentes: ["https://a"] }, decision } as unknown as AgenteOut;
    const e0 = reducir(inicial, { tipo: "enviar", texto: "x", id: "1" });
    // Act
    const e = reducir(e0, { tipo: "evento", evento: { tipo: "final", turno } });
    // Assert
    expect(e.fase).toBe("listo");
    expect(e.mensajes[1].texto).toBe("Texto final");
    expect(e.mensajes[1].turno).toBe(turno);
  });

  it("un fallo deja el error con su request id y permite reintentar", () => {
    // Arrange
    const e0 = reducir(inicial, { tipo: "enviar", texto: "x", id: "1" });
    // Act
    const e = reducir(e0, { tipo: "fallo", detalle: "No hay conexión", requestId: "r9" });
    // Assert
    expect(e.fase).toBe("error");
    expect(e.mensajes[1].error).toEqual({ detalle: "No hay conexión", requestId: "r9" });
    expect(sinUltimoIntento(e).mensajes).toEqual([]);
  });

  it("cargar reemplaza el historial al abrir un hilo", () => {
    // Act
    const e = reducir(inicial, { tipo: "cargar", mensajes: [{ rol: "usuario", texto: "hola" }] });
    // Assert
    expect(e.mensajes).toHaveLength(1);
    expect(e.fase).toBe("idle");
  });
});
