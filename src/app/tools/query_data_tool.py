from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class QueryDataToolInput(BaseModel):
    query: str = Field(description="The query to be executed")

class QueryDataTool(BaseTool):
    name: str = "query_data"
    description: str = "A tool to query the data"
    args_schema: Type[BaseModel] = QueryDataToolInput
    
    def _run(self, input:QueryDataToolInput) -> str:
        return f"Query executed: {input.query}"
    
