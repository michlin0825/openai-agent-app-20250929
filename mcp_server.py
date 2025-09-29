from tavily import TavilyClient
import os

class MCPTavilyServer:
    def __init__(self):
        self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    def search_web(self, query, max_results=None):
        if max_results is None:
            max_results = int(os.getenv("MAX_SEARCH_RESULTS", "3"))
        try:
            response = self.client.search(query=query, max_results=max_results)
            return response.get("results", [])
        except Exception as e:
            print(f"Tavily search error: {e}")
            return []
