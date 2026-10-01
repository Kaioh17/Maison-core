from app.api.services.ai_service import retrieve_docs


def test_retrieval_picks_relevant_chunk():
    assert "Growth" in retrieve_docs("how much is the growth plan and take rate?", k=1)
    assert "/tenant/settings/branding" in retrieve_docs("change my logo and branding colors", k=1)
    assert retrieve_docs("zzzz qqqq")  # never empty
