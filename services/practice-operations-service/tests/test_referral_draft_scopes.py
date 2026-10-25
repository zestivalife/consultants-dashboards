from pathlib import Path


def test_draft_referral_list_preserves_requested_scopes_before_consent():
    source = (Path(__file__).parents[1] / "app" / "main.py").read_text()
    assert "external_referral_shared_scopes s" in source
    assert "jsonb_agg(s.scope_code ORDER BY s.scope_code)" in source
