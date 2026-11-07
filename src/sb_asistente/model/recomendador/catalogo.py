"""Catálogo de productos de seguros para personas.

Los nombres y líneas se inspiran en la oferta pública de una aseguradora colombiana; las
descripciones son redacción propia y sirven como texto para los *embeddings* del modelo base
(``passage: …``). No contienen precios ni condiciones reales: las primas de referencia son
sintéticas.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Producto:
    """Un producto del catálogo."""

    product_id: str
    nombre: str
    linea: str
    descripcion: str
    prima_base_cop: int
    edad_min: int = 18
    edad_max: int = 80


CATALOGO: tuple[Producto, ...] = (
    Producto(
        "P01",
        "Seguro de Autos Todo Riesgo",
        "movilidad",
        "Protege el carro ante choques, hurto total o parcial y daños a terceros; incluye grúa, "
        "conductor elegido y asistencia en carretera las 24 horas.",
        210_000,
    ),
    Producto(
        "P02",
        "Seguro para Carros Eléctricos e Híbridos",
        "movilidad",
        "Cobertura para vehículos eléctricos o híbridos, incluido el cargador, con traslado a la "
        "estación de carga más cercana y red de talleres especializados.",
        240_000,
    ),
    Producto(
        "P03",
        "Seguro de Bicicletas",
        "movilidad",
        "Ampara la bicicleta convencional o eléctrica contra hurto y daños, y cubre lesiones del "
        "ciclista en sus recorridos urbanos.",
        25_000,
        16,
        70,
    ),
    Producto(
        "P04",
        "Seguro de Hogar",
        "hogar",
        "Protege la vivienda y sus contenidos ante incendio, terremoto y daños por agua; incluye "
        "cerrajería, plomería, gas y orientación jurídica.",
        65_000,
    ),
    Producto(
        "P05",
        "Seguro de Hogar Digital",
        "hogar",
        "Póliza de hogar contratada en línea en minutos, con planes ajustables para casa o "
        "apartamento, propio o arrendado.",
        40_000,
    ),
    Producto(
        "P06",
        "Seguro de Arrendamiento",
        "hogar",
        "Para propietarios que arriendan: garantiza el pago del canon y de la administración si "
        "el inquilino incumple, y protege el inmueble arrendado.",
        90_000,
        25,
        80,
    ),
    Producto(
        "P07",
        "Seguro para Mascotas",
        "mascotas",
        "Cubre gastos veterinarios por urgencia, daños que la mascota cause a terceros y gastos "
        "exequiales de perros y gatos.",
        35_000,
    ),
    Producto(
        "P08",
        "Seguro de Vida Individual",
        "vida",
        "Respaldo económico para la familia en caso de fallecimiento, invalidez o enfermedad "
        "grave del asegurado.",
        80_000,
        18,
        70,
    ),
    Producto(
        "P09",
        "Seguro de Vida Deudores",
        "vida",
        "Cubre el saldo de un crédito si el titular fallece o queda incapacitado, para que la "
        "deuda no pase a su familia.",
        30_000,
    ),
    Producto(
        "P10",
        "Seguro de Accidentes Personales",
        "accidentes",
        "Indemnización por muerte accidental, incapacidad o pérdida funcional, con renta por "
        "hospitalización a causa de un accidente.",
        28_000,
        18,
        70,
    ),
    Producto(
        "P11",
        "Accidentes Personales por Días",
        "accidentes",
        "Protección contra accidentes que se activa solo los días que la persona la necesita, "
        "pensada para independientes y actividades puntuales.",
        8_000,
        18,
        65,
    ),
    Producto(
        "P12",
        "Seguro de Salud Integral",
        "salud",
        "Atención médica ambulatoria, hospitalaria y quirúrgica con red de clínicas y "
        "especialistas, sin pasar por la EPS.",
        320_000,
        0,
        70,
    ),
    Producto(
        "P13",
        "Seguro de Salud Internacional",
        "salud",
        "Cobertura médica en Colombia y en el exterior con montos anuales altos, maternidad y "
        "enfermedades críticas.",
        900_000,
        0,
        70,
    ),
    Producto(
        "P14",
        "Renta Diaria por Hospitalización",
        "salud",
        "Pago diario en dinero por cada día de hospitalización, doble si es en cuidados intensivos.",
        22_000,
        18,
        70,
    ),
    Producto(
        "P15",
        "Seguro de Cáncer",
        "salud",
        "Indemnización única al diagnóstico de cáncer para cubrir tratamientos y gastos adicionales.",
        45_000,
        25,
        70,
    ),
    Producto(
        "P16",
        "Plan Educativo",
        "ahorro",
        "Ahorro programado para la educación de los hijos, con respaldo si falta el padre o "
        "madre que aporta.",
        150_000,
        20,
        60,
    ),
    Producto(
        "P17",
        "Título de Capitalización",
        "ahorro",
        "Ahorro con sorteos periódicos que ayuda a construir un capital para metas personales.",
        50_000,
    ),
    Producto(
        "P18",
        "Protección de Tarjetas",
        "proteccion_financiera",
        "Ampara compras y retiros fraudulentos, robo de tarjetas y uso indebido de los productos bancarios.",
        12_000,
    ),
    Producto(
        "P19",
        "Protección Cibernética Familiar",
        "proteccion_financiera",
        "Respaldo ante fraude en línea, suplantación de identidad y ciberacoso para toda la familia.",
        18_000,
    ),
)

PRODUCT_IDS: tuple[str, ...] = tuple(p.product_id for p in CATALOGO)
POR_ID: dict[str, Producto] = {p.product_id: p for p in CATALOGO}
