from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent   
from typing import Dict, Any
from langchain_core.messages import AIMessage
import logging
import os
import traceback

from src.app.tools.tavily_search_tool import TavilySearchTool

logger = logging.getLogger(__name__)

class SummarizerAgent:
    def __init__(self):
        self.system_prompt = "Observe as notícias e crie um resumo de cada um com as principais informações"
        self.llm = ChatOpenAI(model=os.getenv("SUMMARIZER_AGENT_MODEL"), 
                              temperature=0, 
                              api_key=os.getenv("PROVIDER_API_KEY"), 
                              base_url=os.getenv("PROVIDER_BASE_URL"))
        self.tools = [TavilySearchTool()]
        self.agent = create_react_agent(model=self.llm, tools=self.tools, prompt=self.system_prompt)
        
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process messages through the agent and return updated state."""
        messages = state["messages"]
        try:
            logger.info("Executing target agent with messages")
            agent_response = self.agent.invoke({"messages": messages})
            response = agent_response.get("messages", [])
            # Return state update with new messages
            state["messages"] = response
            state = self._increment_step_count(state)
            return state
        except Exception as e:
            logger.error(f"Target agent error: {e}")
            traceback.print_exc()
            # Create proper error message as AIMessage
            error_message = AIMessage(content="I'm sorry, I'm having trouble processing your request. Please try again.")
            state["messages"] = messages + [error_message]
            return state
    
        
    def _increment_step_count(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["step_count"] += 1
        return state