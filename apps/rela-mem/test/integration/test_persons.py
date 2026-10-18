import pytest
from conftest import person

pytestmark = pytest.mark.integration


def test_person_alias_search_and_identity_resolution(client):
    first = person(client, aliases=[{"namespace": "qq", "value": " QQ 12345 "}, {"namespace": "name", "value": "小张"}])
    second = person(client, "张珊", [{"namespace": "name", "value": "小张"}])
    assert client.get("/v1/identity/resolve", params={"namespace": "qq", "value": "12345"}).json()["person"]["person_id"] == first
    assert client.get("/v1/identity/resolve", params={"namespace": "qq", "value": "999"}).json() == {"person": None}
    assert client.get("/v1/identity/resolve", params={"namespace": "name", "value": "小张"}).status_code == 400
    matches = client.get("/v1/persons", params={"query": "小张"}).json()["items"]
    assert {p["person_id"] for p in matches} == {first, second}


def test_alias_conflict_rolls_back_person_creation(client):
    first = person(client, aliases=[{"namespace": "qq", "value": "12345"}])
    response = client.post("/v1/persons", json={"display_name": "不应残留", "aliases": [{"namespace": "qq", "value": "12345"}]})
    assert response.status_code == 409, response.text
    assert client.get("/v1/persons", params={"query": "不应残留"}).json()["items"] == []
    aliases = client.get(f"/v1/persons/{first}").json()["person"]["aliases"]
    assert client.delete(f"/v1/persons/{first}/aliases/{aliases[0]['alias_id']}").status_code == 204
    person(client, "重新绑定", [{"namespace": "qq", "value": "12345"}])


def test_archive_pagination_and_invalid_person_inputs(client):
    for name in ("张三", "李四", "王五"):
        person(client, name)
    first = client.get("/v1/persons", params={"limit": 2}).json()
    second = client.get("/v1/persons", params={"limit": 2, "cursor": first["next_cursor"]}).json()
    assert not ({p["person_id"] for p in first["items"]} & {p["person_id"] for p in second["items"]})
    target = person(client, "归档人物")
    assert client.patch(f"/v1/persons/{target}", json={"status": "archived"}).status_code == 200
    assert client.get(f"/v1/persons/{target}").status_code == 404
    assert client.get(f"/v1/persons/{target}", params={"include_archived": True}).status_code == 200
    assert client.post("/v1/persons", json={"display_name": "x", "kind": "user"}).status_code == 400
    assert client.patch("/v1/persons/removel", json={"kind": "human"}).status_code == 400
