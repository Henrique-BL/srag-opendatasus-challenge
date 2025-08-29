from langchain_core.tools import BaseTool
from typing import Type, Literal
from pydantic import BaseModel, Field
from tavily import TavilyClient, AsyncTavilyClient
import asyncio
import logging
import os
import traceback
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

queries = ["Evolução da Influenza A Brasil", 
           "Evolução do vírus H5N1 no Brasil",
           "Evolução do Vírus Sincicial Respiratório Brasil", 
           "Evolução da SRAG Brasil"
           ]

class TavilySearchToolInput(BaseModel):
    start_date: str = Field(..., description="Start date for the search")
    end_date: str = Field(..., description="End date for the search")
    search_depth: Literal["basic", "advanced"] = Field(default="advanced", description="Search depth level")
    max_results: int = Field(default=3, description="Number of results to return")

class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = "A tool to search the web for news about influenza and others healthcare topics in Brazil"
    args_schema: Type[BaseModel] = TavilySearchToolInput
    
    def _run(self, start_date:str = None,
                   end_date:str = None, 
                   search_depth:Literal["basic", "advanced"] = "basic",
                   max_results:int = 3) -> str:
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
                                    start_date=start_date,
                                    end_date=end_date,
                                    search_depth=search_depth,
                                    topic="news",
                                    max_results=max_results,
                                    country="brazil")
                        for q in queries]
            logger.info(f"Search results with {len(responses)} news")
            return responses
        except Exception as e:
            logger.error(f"Error searching for {queries}: {e}")
            return {"error": "Data not found"}
        
    async def _arun(self, start_date:str = None,
                          end_date:str = None, 
                          search_depth:Literal["basic", "advanced"] = "basic",
                          max_results:int = 3) -> str:
        print(f"Searching for {start_date} to {end_date} with {search_depth} depth and {max_results} results")
        try:
            sources = ["https://agencia.fiocruz.br",
                    "https://agenciabrasil.ebc.com.br"
                    "https://www.cnnbrasil.com.br",
                    "https://www.cnnbrasil.com.br/tudo-sobre/influenza",
                    "https://www.cnnbrasil.com.br/tudo-sobre/influenza-a"]
            client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            logger.info(f"Searching for {queries}")
            # Perform the search queries concurrently, passing the entire query dictionary
            responses = await asyncio.gather(*[client.search(q, 
                                    include_domains=sources,   
                                    start_date=start_date,
                                    end_date=end_date,
                                    search_depth=search_depth,
                                    include_answer=True,
                                    topic="news",
                                    max_results=max_results,
                                    country="brazil") for q in queries])
            # Filter URLs with a score greater than 0.5. Alternatively, you can use a re-ranking model or an LLM to identify the most relevant sources, or cluster your documents and extract content only from the most relevant cluster
            for i, q in enumerate(queries):
                logger.info(f"Total search results for {q}: {len(responses[i])}")
            results = []
            for response in responses:
                answer = response.get('answer')
                for result in response.get('results', []):
                    if isinstance(response, Exception):
                        continue
                    if result.get('score', 0) > 0.1:
                        title = result.get('title')
                        # content = result.get('content')
                        results.append({"title":title, "content":answer})
            logger.info(f"Search results after score filtering: {len(results)} news")
            return results 
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error searching for {queries}: {e}")
            return {"error": "Data not found"}
        