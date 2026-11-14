import { describe, expect, it } from "vitest";

import { MAX_BYTES, porcentaje, validarFoto } from "./validar";

const archivo = (tipo: string, bytes: number) => new File([new Uint8Array(bytes)], "foto", { type: tipo });

describe("validación de la foto en el navegador", () => {
  it("acepta un JPG dentro del límite", () => {
    // Assert
    expect(validarFoto(archivo("image/jpeg", 1000))).toBeNull();
  });

  it("rechaza una foto de más de 8 MB sin llamar a la API", () => {
    // Act
    const error = validarFoto(archivo("image/png", MAX_BYTES + 1));
    // Assert
    expect(error).toMatch(/máximo es 8 MB/);
  });

  it("rechaza archivos que no son JPG ni PNG", () => {
    // Assert
    expect(validarFoto(archivo("application/pdf", 10))).toMatch(/JPG o PNG/);
  });

  it("muestra la confianza como porcentaje", () => {
    // Assert
    expect(porcentaje(0.876)).toBe("88 %");
  });
});
