import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Estado from "../pages/Estado";
import AvisoConexion from "./AvisoConexion";

describe("estado del servicio", () => {
  it("el aviso aparece si la API está caída y permite reintentar", () => {
    // Arrange
    const reintentar = vi.fn();
    render(<AvisoConexion estado={{ fase: "caida", detalle: "sin red" }} onReintentar={reintentar} />);
    // Act
    fireEvent.click(screen.getByText("Reintentar"));
    // Assert
    expect(screen.getByRole("alert").textContent).toContain("No hay conexión con la API");
    expect(reintentar).toHaveBeenCalledOnce();
  });

  it("sin caída no se muestra ningún aviso", () => {
    // Act
    const { container } = render(<AvisoConexion estado={{ fase: "cargando" }} onReintentar={() => {}} />);
    // Assert
    expect(container.textContent).toBe("");
  });

  it("la página de estado marca los componentes que faltan", () => {
    // Arrange
    const datos = { status: "degradado" as const, version: "1.0", llm: "anthropic", componentes: { corpus: true, indice_qdrant: false } };
    // Act
    render(<Estado estado={{ fase: "ok", datos }} onReintentar={() => {}} />);
    // Assert
    expect(screen.getByText("Degradado")).toBeTruthy();
    expect(screen.getByText(/Índice Qdrant/).textContent).toContain("no disponible");
  });
});
