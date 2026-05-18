import json
import os

import requests
from smolagents.utils import truncate_content


class FinalAnswerTool:
    name = "final_answer"
    description = "Provides a final answer to the given problem."
    inputs = {
        "answer": {"type": "any", "description": "The final answer to the problem"}
    }
    output_type = "any"

    def __call__(self, answer):
        return answer


class WebSearchTool:
    name = "web_search"
    description = "Performs a web search using a free Chinese search API and returns the results. Use this for any web search needs."
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."}
    }
    output_type = "string"

    def __init__(self, max_results: int = 5, max_output_length: int = 8000):
        self.max_results = max_results
        self.max_output_length = max_output_length
        self.api_url = os.environ.get("SEARCH_API_URL", "https://open.feedcoopapi.com/search_api/web_search")
        self.api_key = os.environ.get("SEARCH_API_KEY", "")

    def __call__(self, query: str) -> str:
        try:
            body = {
                "Query": query,
                "SearchType": "web_summary",
                "Count": self.max_results,
                "Filter": {
                    "NeedContent": False,
                    "NeedUrl": True
                },
                "NeedSummary": True
            }

            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json=body,
                timeout=15,
                stream=True,  # Enable streaming for SSE
            )

            if response.status_code != 200:
                return f"Search API returned status {response.status_code}. Try again later."

            # Parse SSE (Server-Sent Events) format
            full_content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data:"):
                        full_content = line_str[5:]  # Remove "data:" prefix
                        break

            if not full_content:
                return "No results found! Try a less restrictive/shorter query."

            import json
            data = json.loads(full_content)
            
            # Check for API errors
            if "ResponseMetadata" in data and "Error" in data["ResponseMetadata"]:
                error = data["ResponseMetadata"]["Error"]
                error_msg = error.get("Message", str(error))
                if "invalid" in error_msg.lower() or "key" in error_msg.lower():
                    return "Search API key is invalid. Please check the APIKEY in config.py."
                return f"Search API error: {error_msg}"

            results = []

            # Parse API response based on actual structure
            if "Result" in data and isinstance(data["Result"], dict):
                web_results = data["Result"].get("WebResults", [])
                for item in web_results[:self.max_results]:
                    title = item.get("Title", "")
                    url = item.get("Url", "")
                    summary = item.get("Summary", "")
                    if title:
                        results.append(f"[{title}]({url})\n{summary}")

            if not results:
                return "No results found! Try a less restrictive/shorter query."

            output = "## Search Results\n\n" + "\n\n".join(results)
            return truncate_content(output, self.max_output_length)

        except requests.exceptions.Timeout:
            return "Search request timed out. Please try again later."
        except Exception as e:
            return f"Search failed: {type(e).__name__}: {e}"


class VisitWebpageTool:
    name = "visit_webpage"
    description = "Visits a webpage at the given url and reads its content as a markdown string. Use this to browse webpages."
    inputs = {
        "url": {
            "type": "string",
            "description": "The url of the webpage to visit.",
        }
    }
    output_type = "string"

    def __init__(self, max_output_length: int = 40000):
        self.max_output_length = max_output_length

    def __call__(self, url: str) -> str:
        try:
            import re
            import requests
            from markdownify import markdownify
            from requests.exceptions import RequestException
        except ImportError as e:
            raise ImportError(
                "You must install packages `markdownify` and `requests`."
            ) from e
        try:
            response = requests.get(url, timeout=20, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            })
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            markdown_content = markdownify(response.text).strip()
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
            return truncate_content(markdown_content, self.max_output_length)
        except requests.exceptions.Timeout:
            return "The request timed out. Please try again later or check the URL."
        except RequestException as e:
            return f"Error fetching the webpage: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
