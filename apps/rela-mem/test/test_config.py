import json

import pytest
from pydantic import ValidationError


def configuration():
    return {
        "identity": {
            "user": {"person_id": "removel", "display_name": "鱼梦"},
            "agent": {"person_id": "icarus", "display_name": "Icarus"},
        },
        "postgres": {"schema": "rela_mem_test"},
    }


def test_load_config_keeps_identity_and_hides_secrets(tmp_path):
    from config import load_settings

    path = tmp_path / "settings.json"
    path.write_text(json.dumps(configuration()), encoding="utf-8")
    settings = load_settings(path, {
        "RELA_MEM_API_TOKEN": "test-token-not-for-production",
        "RELA_MEM_FALKORDB_PASSWORD": "graph-test-password",
        "RELA_MEM_PG_PASSWORD": "pg-test-password",
    })
    assert settings.identity.user.person_id == "removel"
    assert settings.identity.agent.person_id == "icarus"
    assert settings.postgres.schema_name == "rela_mem_test"
    assert "pg-test-password" not in repr(settings)
    assert "test-token-not-for-production" not in repr(settings)


@pytest.mark.parametrize("change", [
    {"unexpected": True},
    {"postgres": {"schema": "public; DROP SCHEMA public"}},
    {"identity": {"user": {"person_id": "same", "display_name": "me"},
                  "agent": {"person_id": "same", "display_name": "bot"}}},
])
def test_invalid_configuration_is_rejected(tmp_path, change):
    from config import load_settings

    config = configuration() | change
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_settings(path, {"RELA_MEM_API_TOKEN": "token", "RELA_MEM_FALKORDB_PASSWORD": "pw", "RELA_MEM_PG_PASSWORD": "pw"})


def test_standalone_configuration_does_not_assume_repository_depth(tmp_path, monkeypatch):
    import config

    path = tmp_path / "settings.json"
    path.write_text(json.dumps(configuration()), encoding="utf-8")
    monkeypatch.setattr(config, "__file__", "/app/src/config.py")
    monkeypatch.setenv("RELA_MEM_CONFIG", str(path))
    monkeypatch.setenv("RELA_MEM_API_TOKEN", "test-token")
    monkeypatch.setenv("RELA_MEM_FALKORDB_PASSWORD", "graph-password")
    monkeypatch.setenv("RELA_MEM_PG_PASSWORD", "pg-password")
    assert config.load_settings().identity.user.person_id == "removel"


def test_missing_secret_is_not_silently_accepted(tmp_path):
    from config import load_settings

    path = tmp_path / "settings.json"
    path.write_text(json.dumps(configuration()), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_settings(path, {})
