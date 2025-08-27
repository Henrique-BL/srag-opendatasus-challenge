from langchain import hub as prompts
from langchain_core.prompts import ChatPromptTemplate
import json

class PromptHub:
    def __init__(self, force_push: bool = False):
        self.prompts_file_path:str = "src/app/agents/artifacts/prompts.json"
        self.prompts_templates:dict[str, ChatPromptTemplate] = {}
        self._load_prompts_templates(force_push)
        
    def _push_prompt_template(self):
        try:
            with open(self.prompts_file_path, "r", encoding="utf-8") as f:
                self.prompts = json.load(f)
            for agent_name in self.prompts.keys():
                for prompt_name, prompt_data in self.prompts[agent_name].items():
                    prompt_template = ChatPromptTemplate.from_messages(
                        [("system", prompt_data["system"]), ("human", prompt_data["human"])]
                    )
                    prompts.push(prompt_name, prompt_template, tags=[agent_name])
        except Exception as e:
            print(f"Error pushing prompts: {e}")
        
    def _pull_prompts_templates(self):
        try:
            with open(self.prompts_file_path, "r", encoding="utf-8") as f:
                self.prompts = json.load(f)
            for agent_name in self.prompts.keys():
                for prompt_name, _ in self.prompts[agent_name].items():
                    self.prompts_templates[prompt_name] = prompts.pull(prompt_name)
        except Exception as e:
            print(f"Error pulling prompts: {e}")
            
    def _load_prompts_templates(self, force_push: bool = False):
        try:
            self._pull_prompts_templates()
                
            if self.prompts_templates is None or force_push:
                self._push_prompt_template()
                self._pull_prompts_templates()
        except Exception as e:
            print(f"Error loading prompts: {e}")

    def get_prompt_template(self, prompt_name: str) -> ChatPromptTemplate:
        return self.prompts_templates[prompt_name]
    
    def get_all_prompts_templates(self) -> dict[str, ChatPromptTemplate]:
        return self.prompts_templates
    