def score_audit(website: str|None, findings:dict, issues:list[str]) -> tuple[int,str,str]:
    if not website: return 100,"High","No Website"
    penalties = 0
    weights={"https":10,"mobile":8,"whatsapp":5,"contact_form":5,"booking":5,"favicon":2,"privacy":3,"sitemap":3,"structured_data":4}
    for key, weight in weights.items():
        if not findings.get(key, False): penalties += weight
    perf=int(findings.get("performance", 60)); seo=int(findings.get("seo", 60))
    score=min(100, penalties + max(0,70-perf)//2 + max(0,70-seo)//2 + min(20,len(issues)*2))
    return score, "High" if score>=70 else "Medium" if score>=40 else "Low", "Website Needs Improvement"
