"""Pruebas de las métricas de flujo del tablero (fechas fijas, sin GitHub)."""

from datetime import UTC, datetime, timedelta

from sb_asistente.model.kanban import Historia, calcular, excede_wip

AHORA = datetime(2026, 11, 13, 18, 0, tzinfo=UTC)


def h(numero, estado, horas_desde_creada, horas_hasta_cierre=None):
    creada = AHORA - timedelta(hours=horas_desde_creada)
    cerrada = creada + timedelta(hours=horas_hasta_cierre) if horas_hasta_cierre is not None else None
    return Historia(numero, f"SPEC-{numero}", estado, creada, cerrada)


def test_wip_cuenta_solo_lo_empezado_y_abierto():
    # Act
    m = calcular(
        [h(1, "In progress", 5), h(2, "In review", 3), h(3, "Done", 9, 2), h(4, "Backlog", 1)], AHORA
    )
    # Assert
    assert m.wip == {"In progress": 1, "In review": 1}


def test_throughput_por_semana_iso():
    # Act
    m = calcular([h(1, "Done", 10, 1), h(2, "Done", 200, 1)], AHORA)
    # Assert
    assert m.throughput_semanal == {"2026-S45": 1, "2026-S46": 1}


def test_edad_de_lo_que_sigue_abierto_en_dias():
    # Act
    m = calcular([h(7, "In review", 36)], AHORA)
    # Assert
    assert m.edad_dias == {7: 1.5}


def test_cycle_time_mediana_y_percentil_85():
    # Act
    m = calcular([h(i, "Done", 50, horas) for i, horas in enumerate([1, 2, 3, 4, 10])], AHORA)
    # Assert
    assert m.cycle_time_mediana_h == 3.0
    assert m.cycle_time_p85_h == 6.4  # posición 3,4 → 4 + (10 - 4) × 0,4
    assert m.cerradas == 5


def test_sin_cerradas_no_hay_cycle_time():
    # Assert
    assert calcular([h(1, "In progress", 1)], AHORA).cycle_time_mediana_h is None


def test_detecta_columnas_fuera_del_limite_wip():
    # Act
    m = calcular([h(i, "In review", 1) for i in range(5)], AHORA)
    # Assert
    assert excede_wip(m) == {"In review": 3}
