from langchain_core.tools import BaseTool
from typing import Type, Literal
from pydantic import BaseModel, Field
from tavily import TavilyClient

sources = ["https://agencia.fiocruz.br",
           "https://agenciabrasil.ebc.com.br"
           "https://www.cnnbrasil.com.br"]

class TavilySearchToolInput(BaseModel):
    query: str = Field(description="Relatório de notícias sobre a SRAG Brasil")
    start_date: str = Field(description="2025-01-01")
    end_date: str = Field(description="2025-01-01")
    search_depth: Literal["basic", "advanced"] = Field(description="basic")
    max_results: int = Field(description="10")

class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = "A tool to search the web"
    args_schema: Type[BaseModel] = TavilySearchToolInput
    
    def _run(self, input:TavilySearchToolInput) -> str:
        client = TavilyClient(api_key="tavily_api_key")
        response = client.search(input.query, 
                                 sources=sources,
                                 start_date=input.start_date,
                                 end_date=input.end_date,
                                 search_depth=input.search_depth,
                                 topic="news",
                                 max_results=input.max_results)
        return response.results
    
