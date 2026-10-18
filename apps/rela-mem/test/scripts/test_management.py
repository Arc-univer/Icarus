from pathlib import Path
import subprocess
import sys


APP = Path(__file__).resolve().parents[2]


def test_management_script_can_validate_config_without_database(tmp_path):
    import json
    import os

    config = tmp_path / "settings.json"
    config.write_text(json.dumps({"identity": {"user": {"person_id": "me", "display_name": "我"}}}), encoding="utf-8")
    result = subprocess.run([sys.executable, str(APP / "scripts/manage.py"), "check-config"],
        env=os.environ | {"RELA_MEM_CONFIG": str(config), "RELA_MEM_API_TOKEN": "not-public",
                         "RELA_MEM_FALKORDB_PASSWORD": "graph-secret", "RELA_MEM_PG_PASSWORD": "pg-secret"},
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "configuration valid" in result.stdout
    assert "graph-secret" not in result.stdout + result.stderr


def test_management_help_has_explicit_init_and_smoke_operations():
    result = subprocess.run([sys.executable, str(APP / "scripts/manage.py"), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "init-graph" in result.stdout and "init-postgres" in result.stdout


def test_compose_configuration_requires_secrets_and_has_isolated_ports(tmp_path):
    import os

    result = subprocess.run(["docker", "compose", "-f", str(APP / "docker-compose.yaml"), "config", "--format", "json"],
        env=os.environ | {"ICARUS_DATA_DIR": str(tmp_path), "RELA_MEM_API_TOKEN": "test-token",
                         "RELA_MEM_FALKORDB_PASSWORD": "graph-pw", "RELA_MEM_PG_PASSWORD": "pg-pw"},
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    import json
    services = json.loads(result.stdout)["services"]
    assert set(services) == {"rela-mem", "falkordb", "postgres"}
    assert services["rela-mem"]["ports"][0]["published"] == "8767"
    assert services["falkordb"]["ports"][0]["published"] == "16379"
    assert services["postgres"]["ports"][0]["published"] == "15432"
    assert all(v.get("type") == "bind" for s in services.values() for v in s.get("volumes", []))
