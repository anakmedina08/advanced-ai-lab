import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Sustentacion from "./Sustentacion";

const datos = {
  secciones: {
    "Gestión de Proyectos en IA y CD": [
      { requisito: "Mínimo 40 specs", estado: "cumplido", evidencia: "`openspec/specs/`" },
      { requisito: "Proteger main", estado: "pendiente", evidencia: "T-15" },
    ],
    "Técnicas Avanzadas de IA en Modelos de Lenguaje": [{ requisito: "Router", estado: "cumplido", evidencia: "router.py" }],
  },
  contadores: { funciones_de_prueba: 540, archivos_de_prueba: 43, specs: 45, adr: 22, tareas_hechas: 63, tareas_pendientes: 11 },
  corridas_mlflow: 23,
  enlaces: { Repositorio: "https://github.com/x" },
};

afterEach(() => vi.unstubAllGlobals());

describe("Entregables por curso", () => {
  it("muestra las cifras y el progreso del curso", async () => {
    // Arrange
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(datos), { status: 200 })));
    // Act
    render(<Sustentacion />);
    // Assert
    await waitFor(() => expect(screen.getByText("540")).toBeTruthy());
    expect(screen.getByText("1 de 2 cumplidos")).toBeTruthy();
    expect(screen.getByText("openspec/specs/").tagName).toBe("CODE");
  });

  it("el filtro deja solo los requisitos pendientes", async () => {
    // Arrange
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(datos), { status: 200 })));
    render(<Sustentacion />);
    await waitFor(() => expect(screen.getByText("Mínimo 40 specs")).toBeTruthy());
    // Act
    fireEvent.click(screen.getByRole("button", { name: "cumplido" }));
    fireEvent.click(screen.getByRole("button", { name: "en curso" }));
    // Assert
    expect(screen.queryByText("Mínimo 40 specs")).toBeNull();
    expect(screen.getByText("Proteger main")).toBeTruthy();
  });
});
