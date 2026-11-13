import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Sin globals de Vitest, Testing Library no limpia sola: se desmonta cada render al terminar.
afterEach(() => cleanup());
