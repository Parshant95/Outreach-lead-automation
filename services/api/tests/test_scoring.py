from app.services.scoring import score_audit

def test_no_website_is_highest_priority():
    assert score_audit(None, {}, []) == (100, "High", "No Website")

def test_issue_heavy_website_scores_higher():
    score, priority, _ = score_audit("https://example.com", {"https": True, "performance": 30, "seo": 25}, ["a", "b", "c"])
    assert score >= 70
    assert priority == "High"
