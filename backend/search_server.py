from fastmcp import FastMCP
import requests

mcp = FastMCP("search-server")


@mcp.tool()
def search_web(query: str) -> str:
    """
    Search the web and return summarized information.
    """
    try:
        # Simple DuckDuckGo API (no key needed)
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json"
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data.get("Abstract"):
            return data["Abstract"]

        elif data.get("RelatedTopics"):
            results = data["RelatedTopics"][:3]
            texts = [r.get("Text", "") for r in results if "Text" in r]
            return "\n".join(texts)

        else:
            return "No useful results found. Use general knowledge."

    except Exception as e:
        return f"Search failed: {str(e)}"
    

if __name__ == "__main__":
    mcp.run()