from duckduckgo_search import DDGS

MAX_RESULTS = 3


def search_web(query: str) -> str:
    """
    Search DuckDuckGo and return a spoken summary of the top results.
    Used as a fallback when Groq says it doesn't know something.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_RESULTS))
    except Exception as e:
        print(f"[DDG error] {e}")
        return "I couldn't reach the web search right now."

    if not results:
        return "I couldn't find any web results for that."

    snippets = []
    for r in results:
        body = (r.get("body") or "").strip()
        if body:
            snippets.append(body)

    if not snippets:
        return "I found results but couldn't extract readable text from them."

    combined = " ".join(snippets)
    if len(combined) > 500:
        combined = combined[:500].rsplit(" ", 1)[0] + "..."

    return f"Here's what I found on the web: {combined}"