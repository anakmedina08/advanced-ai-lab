"""Pruebas del cargador de skills (formato Agent Skills / reglas de OpenCode)."""

import pytest

from sb_asistente.model import skills


def escribir(raiz, carpeta, nombre, frontmatter, cuerpo="Instrucciones."):
    archivo = raiz / carpeta / nombre / "SKILL.md"
    archivo.parent.mkdir(parents=True)
    archivo.write_text(f"---\n{frontmatter}\n---\n{cuerpo}\n", encoding="utf-8")
    return archivo


def test_descubre_en_las_tres_rutas(tmp_path):
    escribir(tmp_path, ".claude/skills", "a-uno", "name: a-uno\ndescription: Uno")
    escribir(tmp_path, ".agents/skills", "b-dos", "name: b-dos\ndescription: Dos")
    escribir(tmp_path, ".opencode/skills", "c-tres", "name: c-tres\ndescription: Tres")
    encontradas, errores = skills.descubrir(tmp_path)
    assert [s.nombre for s in encontradas] == ["a-uno", "b-dos", "c-tres"] and errores == []


def test_nombre_debe_coincidir_con_carpeta(tmp_path):
    escribir(tmp_path, ".claude/skills", "carpeta", "name: otro\ndescription: X")
    assert "debe ser igual" in skills.descubrir(tmp_path)[1][0]


@pytest.mark.parametrize("nombre", ["Mayus", "doble--guion", "-inicio", "fin-", "con_guion_bajo"])
def test_nombres_invalidos(tmp_path, nombre):
    escribir(tmp_path, ".claude/skills", nombre, f"name: {nombre}\ndescription: X")
    assert skills.descubrir(tmp_path)[1]


def test_sin_frontmatter_es_error(tmp_path):
    archivo = tmp_path / ".claude/skills/sin/SKILL.md"
    archivo.parent.mkdir(parents=True)
    archivo.write_text("solo texto", encoding="utf-8")
    assert "frontmatter" in skills.descubrir(tmp_path)[1][0]


def test_descripcion_vacia_es_error(tmp_path):
    escribir(tmp_path, ".claude/skills", "vacia", 'name: vacia\ndescription: ""')
    assert skills.descubrir(tmp_path)[1]


def test_nombre_repetido_entre_rutas(tmp_path):
    escribir(tmp_path, ".claude/skills", "igual", "name: igual\ndescription: A")
    escribir(tmp_path, ".agents/skills", "igual", "name: igual\ndescription: B")
    encontradas, errores = skills.descubrir(tmp_path)
    assert len(encontradas) == 1 and "ya existe" in errores[0]


def test_solo_las_de_uso_asistente_llegan_al_chat(tmp_path):
    escribir(tmp_path, ".claude/skills", "dev", "name: dev\ndescription: D")
    escribir(tmp_path, ".claude/skills", "chat", "name: chat\ndescription: C\nmetadata:\n  uso: asistente")
    assert [s.nombre for s in skills.skills_asistente(tmp_path)] == ["chat"]


def test_instrucciones_de_skill_de_desarrollo_no_se_entregan(tmp_path):
    escribir(tmp_path, ".claude/skills", "dev", "name: dev\ndescription: D")
    with pytest.raises(KeyError):
        skills.instrucciones("dev", tmp_path)


def test_instrucciones_se_recortan(tmp_path):
    escribir(
        tmp_path,
        ".claude/skills",
        "larga",
        "name: larga\ndescription: L\nmetadata:\n  uso: asistente",
        "x" * 9000,
    )
    assert len(skills.instrucciones("larga", tmp_path)) == skills.MAX_INSTRUCCIONES


def test_nueva_skill_sale_valida(tmp_path):
    archivo = skills.nueva_skill("mi-skill", "Hace algo útil", "asistente", tmp_path)
    skill, cuerpo = skills.leer_skill(archivo)
    assert skill.para_asistente and "## Qué hace" in cuerpo


def test_nueva_skill_rechaza_duplicado_y_nombre_invalido(tmp_path):
    skills.nueva_skill("mi-skill", "X", raiz=tmp_path)
    with pytest.raises(skills.SkillError):
        skills.nueva_skill("mi-skill", "X", raiz=tmp_path)
    with pytest.raises(skills.SkillError):
        skills.nueva_skill("Mal Nombre", "X", raiz=tmp_path)


def test_skills_del_repositorio_son_validas():
    encontradas, errores = skills.descubrir()
    assert errores == []
    assert {"respuesta-cliente", "comparar-seguros", "explicar-simple"} <= {
        s.nombre for s in encontradas if s.para_asistente
    }


def test_enlace_simbolico_de_npx_skills_no_duplica(tmp_path):
    escribir(tmp_path, ".agents/skills", "externa", "name: externa\ndescription: De terceros")
    (tmp_path / ".claude/skills").mkdir(parents=True)
    (tmp_path / ".claude/skills/externa").symlink_to(tmp_path / ".agents/skills/externa")
    encontradas, errores = skills.descubrir(tmp_path)
    assert [s.nombre for s in encontradas] == ["externa"] and errores == []
    assert not encontradas[0].para_asistente  # entra como desarrollo hasta que el equipo la marque
