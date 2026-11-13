import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { nuevoId, useSesiones } from "./sesiones";

beforeEach(() => localStorage.clear());

describe("sesiones del navegador", () => {
  it("genera ids seguros para la API (6 a 64 caracteres sin barras)", () => {
    // Act
    const id = nuevoId("hilo");
    // Assert
    expect(id).toMatch(/^[A-Za-z0-9_-]{6,64}$/);
  });

  it("el usuario_id se conserva entre visitas", () => {
    // Act
    const primero = renderHook(() => useSesiones()).result.current.usuarioId;
    const segundo = renderHook(() => useSesiones()).result.current.usuarioId;
    // Assert
    expect(primero).toBe(segundo);
  });

  it("el primer mensaje titula y guarda el hilo activo", () => {
    // Arrange
    const { result } = renderHook(() => useSesiones());
    // Act
    act(() => result.current.titular("¿Qué cubre el SOAT?"));
    // Assert
    expect(result.current.hilos).toEqual([expect.objectContaining({ id: result.current.activo, titulo: "¿Qué cubre el SOAT?" })]);
    expect(JSON.parse(localStorage.getItem("sb.hilos")!)).toHaveLength(1);
  });

  it("nueva conversación cambia el hilo activo y quitar lo saca de la lista", () => {
    // Arrange
    const { result } = renderHook(() => useSesiones());
    act(() => result.current.titular("hola"));
    const anterior = result.current.activo;
    // Act
    act(() => result.current.nuevo());
    act(() => result.current.quitar(anterior));
    // Assert
    expect(result.current.activo).not.toBe(anterior);
    expect(result.current.hilos).toEqual([]);
  });
});
