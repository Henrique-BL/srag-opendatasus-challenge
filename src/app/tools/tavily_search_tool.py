from langchain_core.tools import BaseTool
from typing import Type, Literal
from pydantic import BaseModel, Field
from tavily import TavilyClient
import asyncio
import logging
import os
logger = logging.getLogger(__name__)

queries = ["Evolução da Influenza A Brasil", 
           "Evolução do vírus H5N1 no Brasil",
           "Evolução do Vírus Sincicial Respiratório Brasil", 
           "Evolução da SRAG Brasil"]

class TavilySearchToolInput(BaseModel):
    start_date: str = Field(description="2025-01-01")
    end_date: str = Field(description="2025-01-01")
    search_depth: Literal["basic", "advanced"] = Field(description="basic")
    max_results: int = Field(description="10")

class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = "A tool to search the web"
    args_schema: Type[BaseModel] = TavilySearchToolInput
    
    def _run(self, input:TavilySearchToolInput) -> str:
        try:
            sources = ["https://agencia.fiocruz.br",
                    "https://agenciabrasil.ebc.com.br"
                    "https://www.cnnbrasil.com.br",
                    "https://www.cnnbrasil.com.br/tudo-sobre/influenza",
                    "https://www.cnnbrasil.com.br/tudo-sobre/influenza-a"]
            client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            logger.info(f"Searching for {queries}")
            responses = [ client.search(q, 
                                    include_domains=sources,
                                    start_date=input.start_date,
                                    end_date=input.end_date,
                                    search_depth=input.search_depth,
                                    topic="news",
                                    max_results=input.max_results,
                                    country="brazil")
                        for q in queries]
            logger.info(f"Search results with {len(responses)} news")
            return responses
        except Exception as e:
            logger.error(f"Error searching for {queries}: {e}")
            return {"error": "Data not found"}
        
    async def _arun(self, input:TavilySearchToolInput) -> str:
        try:
            sources = ["https://agencia.fiocruz.br",
                    "https://agenciabrasil.ebc.com.br"
                    "https://www.cnnbrasil.com.br",
                    "https://www.cnnbrasil.com.br/tudo-sobre/influenza",
                    "https://www.cnnbrasil.com.br/tudo-sobre/influenza-a"]
            client = TavilyClient(api_key="tavily_api_key")
            logger.info(f"Searching for {queries}")
            # Perform the search queries concurrently, passing the entire query dictionary
            responses = await asyncio.gather(*[client.search(q, 
                                    include_domains=sources,   
                                    start_date=input.start_date,
                                    end_date=input.end_date,
                                    search_depth=input.search_depth,
                                    topic="news",
                                    max_results=input.max_results,
                                    country="brazil") for q in queries])
            # Filter URLs with a score greater than 0.5. Alternatively, you can use a re-ranking model or an LLM to identify the most relevant sources, or cluster your documents and extract content only from the most relevant cluster
            results = []
            for response in responses:
                answer = response.get('answer')
                for result in response.get('results', []):
                    if isinstance(response, Exception):
                        continue
                    if result.get('score', 0) > 0.7:
                        title = result.get('title')
                        # content = result.get('content')
                        results.append({"title":title, "content":answer})
            logger.info(f"Finished searching with {len(results)} news")
            return results 
        except Exception as e:
            logger.error(f"Error searching for {queries}: {e}")
            return {"error": "Data not found"}