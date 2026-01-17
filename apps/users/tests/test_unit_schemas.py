from apps.users.app.api.schemas import ProfileUpdate


def test_profile_update_accepts_partial():
    p = ProfileUpdate.model_validate({"full_name": "X"})
    assert p.full_name == "X"
