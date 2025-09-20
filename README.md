## Context
This project is based on the premise of generating a detailed report document using large language models. The data used is related to Brazilian SRAG Cases, containing the number of infected individuals, ICU occupation, vaccination, etc. The workflow is simple: there are two main functions TavilySearchTool and QueryDataTool, the first is responsible for getting data from news of trusted sources and the latter to get the real OpenDataSUS data from the database. Both tools are invoked directly (with no control of the LLM), with this we gain fine control of what data will be delivered and used to create the report. This structure can be better visualized at 
[Project Architecture](architecture.pdf).

### Optional Requirements
- UV Package Mananger (Suggested): useful to install and run the project without dependencies and python version conflict 
- PgAdmin or DBeaver: useful for analyzing the data that's being loaded.
- Docker Desktop: useful interface to execute Ollama commands directly at the container.
- Ollama Model: only if you're not going to use another cloud provider. Must be pulled inside docker container with the command "ollama pull {model_id}" 
- Nvidia GPU, NVIDIA Drivers: only if you're using Ollama. The Ollama configuration at docker-compose.yml is set to use a nvidia GPU with auto memory load. 

**Note**: to disable Ollama, update the PROVIDER_API_URL and the PROVIDER_API_KEY, also either remove the ollama from the docker-compose.yml or build only the database. Finally update the MAIN_AGENT_MODEL so that it stores the correct model id.

### Requirements

- Langsmith API KEY: necessary to store the prompt template and useful for analyzing the execution process.
- Docker: docker must be installed and running, it's necessary to run the Ollama server and instantiate the database.
- Tavily Search API KEY: necessary to perform web searches about SRAG.
- Python >= 3.11.9
- Latex (latexmk, pylatex)

### Attention
This projects was build over WSL. Docker is necessary for both database connections and to run OLLAMA locally so that the connection URL refer to the same enviroment. If there's a need to use other llm provider, comment out the API_URL field at app/agents/main_agent self.llm attribute and modify the API key of .env. 

### Steps
1 - Download the .csv files from the OpenDataSus repository located at https://opendatasus.saude.gov.br/dataset/srag-2021-a-2024 and rename each file to "INFLUD{year_with_two_digits}" and move them to "src/data/bronze"
**Note**: at the time of creation, the files contain data from 2021 to 2025.

2 - Install all dependencies (requirements.txt)
```bash
pip install -r requirements.txt
``` 
or use uv (recommended)

```bash
uv sync
``` 
3 - Install Latex 
Ubuntu (Linux)
```bash
sudo add-apt-repository universe
sudo apt update && sudo apt install -y texlive-full
``` 
or in case of a compact install 
```bash
sudo add-apt-repository universe
sudo apt update && sudo apt install -y latexmk
``` 
4 - Manually run each cell of the exploratory data analysis notebook at "src/eda". The final result must be a "src/data/silver" populated with data.

5 - Run the load process 
```bash
python -m Runner --load
``` 

```bash
uv run Runner.py --load
``` 
6 - Run the report generation process 
Suggested. using uv:
```bash
uv run Runner.py --generate-report today
``` 
Or you can use:
```bash
python -m Runner --generate-report today
``` 

**Note**: you can change 'today' to any other date (yyyy-mm-dd).

The final report can be found as a .pdf file under 'src/data/reports'
