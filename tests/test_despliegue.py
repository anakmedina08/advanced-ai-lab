"""Build, Registry y deploy al Droplet (SPEC-075): la configuración es coherente y sin secretos.

Cada prueba sigue Arrange / Act / Assert y solo lee archivos del repositorio (sin red ni Docker).
"""

import json
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
DEPLOY = RAIZ / "deploy"


def _yaml(ruta: Path) -> dict:
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def test_el_pipeline_sigue_lint_test_build_deploy():
    # Arrange / Act
    ci = _yaml(RAIZ / ".gitlab-ci.yml")
    # Assert
    assert ci["stages"] == ["lint", "test", "build", "deploy"]
    assert ci["build_api"]["stage"] == ci["build_frontend"]["stage"] == "build"
    assert ci["deploy"]["stage"] == "deploy"


def test_las_imagenes_se_publican_en_el_registry_con_el_tag_del_commit():
    # Arrange
    ci = _yaml(RAIZ / ".gitlab-ci.yml")
    # Act
    pasos = {job: " ".join(ci[job]["script"]) for job in ("build_api", "build_frontend")}
    # Assert
    assert "--password-stdin" in " ".join(ci[".docker"]["before_script"])
    for job, script in pasos.items():
        assert ci[job]["extends"] == ".docker"
        assert "$CI_REGISTRY_IMAGE" in script and ":$CI_COMMIT_SHORT_SHA" in script, job
        assert "docker push" in script, job


def test_el_deploy_es_automatico_en_main_manual_en_develop_y_nunca_simultaneo():
    # Arrange
    deploy = _yaml(RAIZ / ".gitlab-ci.yml")["deploy"]
    # Act
    reglas = {r["if"]: r.get("when", "on_success") for r in deploy["rules"]}
    # Assert
    assert reglas == {'$CI_COMMIT_BRANCH == "main"': "on_success", '$CI_COMMIT_BRANCH == "develop"': "manual"}
    assert deploy["resource_group"] == "produccion"
    assert deploy["interruptible"] is False


def test_el_deploy_lee_los_secretos_solo_de_variables_de_ci():
    # Arrange
    deploy = _yaml(RAIZ / ".gitlab-ci.yml")["deploy"]
    # Act
    pasos = " ".join(deploy["before_script"] + deploy["script"])
    # Assert: llave, known_hosts y .env de producción vienen de variables; el token va por stdin
    for variable in ("$SSH_KEY", "$SSH_KNOWN_HOSTS", "$ENV_PRODUCCION", "$CI_JOB_TOKEN"):
        assert variable in pasos, variable
    assert "StrictHostKeyChecking=no" not in pasos
    assert 'install -m 600 "$SSH_KEY"' not in pasos  # el contenido terminaría impreso en el log
    assert 'test -f "$ENV_PRODUCCION"' in pasos
    assert "curl --fail" in pasos and "/health" in pasos


def test_solo_caddy_publica_puertos_y_la_api_tiene_su_env_fuera_del_repo():
    # Arrange
    compose = _yaml(DEPLOY / "docker-compose.prod.yml")["services"]
    # Act
    con_puertos = {nombre for nombre, servicio in compose.items() if "ports" in servicio}
    # Assert
    assert con_puertos == {"caddy"}
    assert {"80:80", "443:443"} <= set(compose["caddy"]["ports"])
    assert compose["api"]["env_file"] == ["app.env"]
    assert compose["caddy"]["depends_on"]["api"]["condition"] == "service_healthy"


def test_caddy_enruta_el_frontend_y_la_api_con_https():
    # Arrange / Act
    caddy = (DEPLOY / "Caddyfile").read_text(encoding="utf-8")
    # Assert
    assert "{$DOMINIO} {" in caddy and "api.{$DOMINIO} {" in caddy
    assert "reverse_proxy frontend:80" in caddy and "reverse_proxy api:8000" in caddy
    assert "Strict-Transport-Security" in caddy


def test_el_script_de_despliegue_espera_healthy_y_cierra_la_sesion_del_registry():
    # Arrange / Act
    script = (DEPLOY / "desplegar.sh").read_text(encoding="utf-8")
    # Assert
    assert "set -eu" in script
    assert "--password-stdin" in script and "docker logout" in script
    assert "Health.Status" in script and "healthy" in script
    assert "--force-recreate caddy" in script and "sha256sum Caddyfile" in script


def test_el_servidor_queda_con_firewall_usuario_sin_root_y_ssh_solo_con_llave():
    # Arrange / Act
    script = (DEPLOY / "preparar-servidor.sh").read_text(encoding="utf-8")
    # Assert
    for regla in ("ufw allow OpenSSH", "ufw allow 80/tcp", "ufw allow 443/tcp", "ufw --force enable"):
        assert regla in script, regla
    assert "adduser --disabled-password" in script and "usermod -aG docker deploy" in script
    assert "PasswordAuthentication no" in script


def test_opencode_conecta_el_mcp_oficial_de_gitlab():
    # Arrange / Act
    mcp = json.loads((RAIZ / "opencode.json").read_text(encoding="utf-8"))["mcp"]["gitlab"]
    # Assert
    assert mcp == {"type": "remote", "url": "https://gitlab.com/api/v4/mcp", "enabled": True}


def test_ningun_archivo_de_despliegue_trae_secretos():
    # Arrange: incluye los subdirectorios de deploy/ (p. ej. openclaw/, SPEC-077)
    del_repo = [RAIZ / ".gitlab-ci.yml", RAIZ / "opencode.json"]
    archivos = [*(ruta for ruta in DEPLOY.rglob("*") if ruta.is_file()), *del_repo]
    plantillas = sorted(DEPLOY.rglob("*.env.example"))
    # Act / Assert
    assert not list(DEPLOY.rglob("*.env")), "los .env de despliegue viven solo en el servidor"
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        assert "PRIVATE KEY" not in texto and "sk-ant-" not in texto, archivo.name
    assert plantillas, "debe haber al menos una plantilla .env.example"
    for plantilla in plantillas:
        for linea in plantilla.read_text(encoding="utf-8").splitlines():
            if linea.split("=")[0].endswith(("_KEY", "_TOKEN")):
                assert linea.endswith("="), f"{plantilla.name}: {linea}"


def test_yellowdata_es_el_sitio_publico_y_llama_a_la_api_por_la_red_interna():
    # Arrange
    compose = _yaml(DEPLOY / "docker-compose.prod.yml")["services"]
    caddy = (DEPLOY / "Caddyfile").read_text(encoding="utf-8")
    # Act
    yellowdata = compose["yellowdata"]
    # Assert
    assert yellowdata["image"].endswith("registry.gitlab.com/daalrasi/yellowdata:latest}")
    assert yellowdata["environment"]["ASSISTANT_API_URL"] == "http://api:8000"
    assert "ports" not in yellowdata
    assert "app.{$DOMINIO} {" in caddy and "reverse_proxy yellowdata:3000" in caddy
    assert "https://app." in compose["api"]["environment"]["FRONTEND_ORIGINS"]
