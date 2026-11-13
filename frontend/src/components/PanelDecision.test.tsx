import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { AgenteOut, DecisionOut } from "../api/types";
import PanelDecision from "./PanelDecision";

const datos: DecisionOut = { ruta: "datos", confianza: 0.9, senales: ["pregunta numérica"], tools: ["consultar_datos"], cautela: false };

describe("PanelDecision", () => {
  it("muestra la ruta del router y su confianza", () => {
    // Act
    render(<PanelDecision decision={datos} />);
    // Assert
    expect(screen.getByText("datos · CSV")).toBeTruthy();
    expect(screen.getByText(/confianza 90 %/)).toBeTruthy();
  });

  it("un saludo se ve como directo sin búsqueda", () => {
    // Act
    render(<PanelDecision decision={{ ...datos, ruta: "directo", tools: [] }} />);
    // Assert
    expect(screen.getByText("directo · sin búsqueda")).toBeTruthy();
    expect(screen.getByText("ninguna (respuesta directa)")).toBeTruthy();
  });

  it("lista las tools usadas con su latencia", () => {
    // Arrange
    const turno = {
      tiempos_tools: [{ tool: "consultar_datos", ms: 12.4 }],
      fuentes_descartadas: [],
      mensajes_en_memoria: 4,
      ms_total: 1800,
    } as unknown as AgenteOut;
    // Act
    render(<PanelDecision decision={datos} turno={turno} />);
    // Assert
    expect(screen.getByText("consultar_datos 12 ms")).toBeTruthy();
    expect(screen.getByText(/1.8 s/)).toBeTruthy();
  });

  it("marca la cautela cuando la confianza del router es baja", () => {
    // Act
    render(<PanelDecision decision={{ ...datos, ruta: "rag", cautela: true }} />);
    // Assert
    expect(screen.getByText(/cautela/)).toBeTruthy();
  });
});
