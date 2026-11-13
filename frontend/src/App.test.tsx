import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ usuario_id: "u", hechos: {} }), { status: 200 })));
});

const abrir = (ruta: string) =>
  render(
    <MemoryRouter initialEntries={[ruta]}>
      <App />
    </MemoryRouter>,
  );

describe("diseño de la versión Streamlit", () => {
  it("la barra lateral tiene las tres áreas con sus páginas", () => {
    // Act
    abrir("/");
    // Assert
    for (const texto of ["Atención al cliente", "Panel del equipo", "Sustentación", "Guías de seguros", "Experimentos (MLflow)", "Entregables por curso"]) {
      expect(screen.getByText(texto)).toBeTruthy();
    }
  });

  it("cada página muestra su título", () => {
    // Act
    abrir("/foto");
    // Assert
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("Foto: ¿qué hago?");
  });

  it("el proveedor se elige en Configuración y se recuerda", () => {
    // Arrange
    abrir("/configuracion");
    // Act
    fireEvent.click(screen.getByRole("radio", { name: "DeepSeek" }));
    // Assert
    expect(screen.getByRole("radio", { name: "DeepSeek" }).getAttribute("aria-checked")).toBe("true");
    expect(localStorage.getItem("sb.proveedor")).toBe("deepseek");
  });
});
