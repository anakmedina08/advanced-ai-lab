import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Inicio from "./Inicio";

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ usuario_id: "u", hechos: {} }), { status: 200 })));
});

describe("página principal en pantallas pequeñas", () => {
  it("la barra de conversaciones se pliega y se despliega con el botón", () => {
    // Arrange
    const { container } = render(<Inicio />);
    const boton = screen.getByRole("button", { name: /Conversaciones/ });
    // Act
    fireEvent.click(boton);
    // Assert
    expect(boton.getAttribute("aria-expanded")).toBe("true");
    expect(container.querySelector(".conversaciones")?.className).toContain("menu-abierto");
  });

  it("la zona de mensajes anuncia los cambios a lectores de pantalla", () => {
    // Act
    const { container } = render(<Inicio />);
    // Assert
    expect(container.querySelector(".mensajes")?.getAttribute("aria-live")).toBe("polite");
    expect(screen.getByLabelText("Mensaje")).toBeTruthy();
  });
});
