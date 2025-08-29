from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent   
from typing import Dict, Any
import logging
import os
import traceback
from src.app.responses.main_agent_response import MainAgentResponse
from src.app.agents.artifacts.prompt_hub import PromptHub
from pydantic import BaseModel
logger = logging.getLogger(__name__)

class MainAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=os.getenv("MAIN_AGENT_MODEL"), 
                              max_completion_tokens=30000,
                            #   reasoning_effort="low",
                              temperature=0, 
                              api_key=os.getenv("PROVIDER_API_KEY"), 
                            #   base_url=os.getenv("PROVIDER_BASE_URL")
                              )
        self.tools = []
        self.agent = None 
        self.prompt_hub = PromptHub()
        
    def _generate_agent(self, response_format: BaseModel = None) -> None:
        """
        Purpose: Generate an agent that will be used to analyze the data.
        Args:
            response_format: BaseModel - The response format of the agent.
        Returns:
            None
        """
        self.agent = create_react_agent(model=self.llm,
                                        tools=self.tools,
                                        response_format=response_format)
        
    def _generate_section_analysis(self,
                                   news: str,
                                   srag_data: dict[str, Any],
                                   section_name: str,
                                   sections: list[str]) -> Dict[str, Any]:
        """
        Args:
            news: str - The news to be analyzed.
            srag_data: dict[str, Any] - The data to be used in the analysis.
            section_name: str - The name of the section to be analyzed.
            sections: list[str] - The list of sections that were already analyzed.
        Returns:
            Dict[str, Any] - The analysis of the section.
        """
        prompt_template = self.prompt_hub.get_prompt_template(prompt_name="sections_analysis_prompt_template")
        prompt_value = prompt_template.invoke({"srag_news": news, 
                                         "srag_data": srag_data,
                                         "sections": sections, 
                                         "section_name": section_name})
        self._generate_agent()
        response = self.agent.invoke(prompt_value)
        return response
    
    def _generate_final_report(self, sections: list[str]) -> Dict[str, Any]:
        """
        Args:
            sections: list[str] - The list of sections that were already analyzed and their analysis.
        Returns:
            Dict[str, Any] - The final report.
        """
        prompt_template = self.prompt_hub.get_prompt_template(prompt_name="final_report_prompt_template")
        prompt_value = prompt_template.invoke({"sections": sections})
        self._generate_agent(response_format=MainAgentResponse)
        response = self.agent.invoke(prompt_value).get("structured_response")
        return response
 
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process messages through the agent and return updated state."""

        try:
            logger.info("Executing main agent")
            news = state["news"]
            srag_data = state["data"]
            sections = state["sections"]
            
            concluded_sections = {}
            logger.info("Generating sections analysis")
            for  section in sections:
                data = srag_data
                if section == "p-last-30-days-analysis":
                    data = srag_data["monthly"]
                elif section == "p-last-12-months-analysis":
                    data = srag_data["one_year_interval"]
                section_analysis = self._generate_section_analysis(news, data, section, concluded_sections.keys())
                concluded_sections[section] = section_analysis
                logger.info(f"Section {section} analysis generated")
            logger.info("Generating final report")
            final_report = self._generate_final_report(concluded_sections)
            state["report"] = final_report
            state["sections"] = concluded_sections
            state["news"] = news
            state["data"] = srag_data
            state["stage"] = "end"
            return state
        except Exception as e:
            logger.error(f"Main agent error: {e}")
            traceback.print_exc()
            # Create proper error message as AIMessage
            state["stage"] = "error"
            return state
        