def test_add_note_201_and_list_notes(client, make_token):
    token = make_token()
    created = client.post(
        "/cases",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": "s4", "owner_area": "PSY", "title": "Caso N", "description": "Desc", "priority": "LOW"},
    ).json()
    case_id = created["id"]

    r = client.post(
        f"/cases/{case_id}/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "NOTE", "content": "Primera nota"},
    )
    assert r.status_code == 201
    note = r.json()
    assert note["case_id"] == case_id
    assert note["content"] == "Primera nota"

    r2 = client.get(f"/cases/{case_id}/notes", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    notes = r2.json()
    assert isinstance(notes, list)
    assert any(n["id"] == note["id"] for n in notes)


def test_timeline_200_has_events(client, make_token):
    token = make_token()
    created = client.post(
        "/cases",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": "s5", "owner_area": "PSY", "title": "Caso T", "description": "Desc", "priority": "HIGH"},
    ).json()
    case_id = created["id"]

    # add note -> adds timeline event
    client.post(
        f"/cases/{case_id}/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "NOTE", "content": "Nota para timeline"},
    )

    r = client.get(f"/cases/{case_id}/timeline", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    events = r.json()
    assert isinstance(events, list)
    assert len(events) >= 2  # created + note_added
