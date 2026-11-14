import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Chat from "./Chat";
import Foto from "./Foto";

const codificador = new TextEncoder();

/** `fetch` falso que responde un flujo SSE con los eventos dados. */
function fetchSSE(eventos: object[]) {
  return vi.fn(async () => {
    const cuerpo = new ReadableStream<Uint8Array>({
      start(control) {
        for (const e of eventos) {
          const tipo = (e as { tipo: string }).tipo;
          control.enqueue(codificador.encode(`event: ${tipo}\ndata: ${JSON.stringify(e)}\n\n`));
        }
        control.close();
      },
    });
    return new Response(cuerpo, { status: 200, headers: { "Content-Type": "text/event-stream" } });
  });
}

const decision = { ruta: "datos", confianza: 0.9, senales: ["pregunta numérica"], tools: ["consultar_datos"], cautela: false };
const turno = {
  conversacion_id: "hilo-prueba-01",
  usuario_id: null,
  salida: { respuesta: "Se vendieron **989** pólizas.", fuentes: [], intencion: "datos", confianza: "alta", productos_recomendados: [], requiere_asesor: false },
  decision,
  pasos: [],
  fuentes_descartadas: [],
  mensajes_en_memoria: 4,
  tiempos_tools: [{ tool: "consultar_datos", ms: 15 }],
  ms_total: 2100,
};

afterEach(() => vi.unstubAllGlobals());

describe("chat de punta a punta (con API simulada)", () => {
  it("envía la pregunta, muestra la respuesta y la decisión del router", async () => {
    // Arrange
    const falso = fetchSSE([
      { tipo: "router", ...decision },
      { tipo: "tool_inicio", tool: "consultar_datos", argumentos: {} },
      { tipo: "texto", delta: "Se vendieron " },
      { tipo: "final", turno },
    ]);
    vi.stubGlobal("fetch", falso);
    render(<Chat conversacionId="hilo-prueba-01" usuarioId={null} />);
    // Act
    fireEvent.change(screen.getByLabelText("Mensaje"), { target: { value: "¿Cuántas pólizas se vendieron?" } });
    fireEvent.click(screen.getByText("Enviar"));
    // Assert
    await waitFor(() => expect(screen.getByText("989")).toBeTruthy());
    expect(screen.getByText("datos · CSV")).toBeTruthy();
    const [url, init] = falso.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/agente\/stream$/);
    expect(JSON.parse(String(init.body))).toMatchObject({ conversacion_id: "hilo-prueba-01" });
  });

  it("un error de la API se ve en la burbuja con Reintentar", async () => {
    // Arrange
    const error = { error: "no_disponible", detalle: "Faltan datos", ruta: "/agente/stream", request_id: "abc" };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(error), { status: 503 })));
    render(<Chat conversacionId="hilo-prueba-02" usuarioId={null} />);
    // Act
    fireEvent.click(screen.getByText("¿Qué cubre el SOAT?"));
    // Assert
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Faltan datos"));
    expect(screen.getByText("Reintentar")).toBeTruthy();
    expect(screen.getByText(/request id: abc/)).toBeTruthy();
  });
});

describe("foto", () => {
  it("rechaza un archivo que no es imagen sin llamar a la API", async () => {
    // Arrange
    const falso = vi.fn();
    vi.stubGlobal("fetch", falso);
    const { container } = render(<Foto />);
    const entrada = container.querySelector("input[type=file]") as HTMLInputElement;
    // Act
    fireEvent.change(entrada, { target: { files: [new File(["x"], "nota.pdf", { type: "application/pdf" })] } });
    // Assert
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("JPG o PNG"));
    expect(falso).not.toHaveBeenCalled();
  });

  it("muestra las detecciones con su confianza al terminar", async () => {
    // Arrange
    const foto = {
      tiempo_inferencia_ms: 320,
      ancho: 100,
      alto: 80,
      personas_difuminadas: 1,
      detecciones: [{ clase: "car", etiqueta: "carro", confianza: 0.91, caja: { x_min: 1, y_min: 1, x_max: 50, y_max: 40 } }],
      sugerencias: [],
      escena: null,
      plan: { tipo: "siniestro", nombre: "Accidente de tránsito", pregunta: null, paginas: [] },
      aviso: null,
      respuesta: null,
      recomendaciones: [],
      imagen_jpeg_b64: "AAAA",
    };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(foto), { status: 200 })));
    const { container } = render(<Foto />);
    const entrada = container.querySelector("input[type=file]") as HTMLInputElement;
    // Act
    fireEvent.change(entrada, { target: { files: [new File(["x"], "choque.jpg", { type: "image/jpeg" })] } });
    // Assert
    await waitFor(() => expect(screen.getByText("Siniestro: qué hacer ahora")).toBeTruthy());
    expect(screen.getAllByText(/91 %/).length).toBeGreaterThan(0);
    expect(screen.getByText(/personas difuminadas: 1/)).toBeTruthy();
  });
});
