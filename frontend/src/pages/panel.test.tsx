import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Evaluacion from "./Evaluacion";
import Experimentos from "./Experimentos";

const responder = (rutas: Record<string, unknown>) =>
  vi.fn(async (url: string) => {
    const clave = Object.keys(rutas).find((r) => url.endsWith(r));
    return new Response(JSON.stringify(clave ? rutas[clave] : []), { status: 200 });
  });

afterEach(() => vi.unstubAllGlobals());

describe("panel del equipo", () => {
  it("Evaluación muestra la mejor cita de fuente y las corridas", async () => {
    // Arrange
    const corridas = [
      { modelo: "anthropic", version: "v1", preguntas: 25, keyword_hit_promedio: 1, tasa_cita_fuente: 0.2, tasa_fallback_correcto: 0.84, latencia_promedio_s: 2.5 },
      { modelo: "anthropic", version: "v3", preguntas: 25, keyword_hit_promedio: 0.98, tasa_cita_fuente: 1, tasa_fallback_correcto: 0.96, latencia_promedio_s: 1.6 },
    ];
    vi.stubGlobal("fetch", responder({ "/evaluacion": corridas }));
    // Act
    render(<Evaluacion />);
    // Assert
    await waitFor(() => expect(screen.getByText("Corrida con mejor cita")).toBeTruthy());
    expect(document.body.textContent).toContain("anthropic · v3");
    expect(screen.getAllByText("100 %").length).toBeGreaterThan(0);
  });

  it("Experimentos explica cómo activar MLflow si no está activo", async () => {
    // Arrange
    vi.stubGlobal("fetch", responder({ "/experimentos": { activa: false, url_ui: "", nombres: {}, experimentos: {} } }));
    // Act
    render(<Experimentos />);
    // Assert
    await waitFor(() => expect(screen.getByText(/no está activa/)).toBeTruthy());
  });

  it("Experimentos lista las corridas de YOLO con su p95", async () => {
    // Arrange
    const datos = {
      activa: true,
      url_ui: "http://127.0.0.1:5050",
      nombres: { "vision-yolo": "YOLO de la API" },
      experimentos: { "vision-yolo": [{ nombre: "yolo26l-conf0.35", fecha: 1, commit: "abc", parametros: {}, metricas: { precision: 0.834, latencia_p95_ms: 438.1 } }] },
    };
    vi.stubGlobal("fetch", responder({ "/experimentos": datos }));
    // Act
    render(<Experimentos />);
    // Assert
    await waitFor(() => expect(screen.getByText("yolo26l-conf0.35")).toBeTruthy());
    expect(screen.getByText("438")).toBeTruthy();
    expect(screen.getByText("0.834")).toBeTruthy();
  });
});
