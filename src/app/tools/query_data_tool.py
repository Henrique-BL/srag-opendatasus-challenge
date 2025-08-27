from langchain_core.tools import BaseTool
from typing import Type, Literal, Optional
from pydantic import BaseModel, Field
from src.utils.db import get_db_connection

connection = get_db_connection()
cursor = connection.cursor()


def _fetch_total_cases(start_date: str, end_date: str, group_by: str) -> str:
    time_period_filter = f" AND data_preenchimento BETWEEN '{start_date}' AND '{end_date}'" if start_date and end_date else ""
    query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
               COUNT(*) FROM influd_data 
               {time_period_filter}
               GROUP BY {group_by}"""
    cursor.execute(query)
    result = cursor.fetchall()
    response = ""
    for row in result:
        response += f"Total de Casos em {row[0]}: {row[1]}\n"
    return response

def _fetch_vaccination_rate(start_date: str = None, 
                            end_date: str = None, 
                            group_by: str = "year") -> str:
    time_period_filter = f" AND data_preenchimento BETWEEN '{start_date}' AND '{end_date}'" if start_date and end_date else ""
    query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
               COUNT(vacina_covid) AS total_vacinados_covid,
               COUNT(vacina_gripe) AS total_vacinados_gripe
			   FROM influd_data
			   WHERE vacina_covid = 1 AND vacina_gripe = 1
			   {time_period_filter}
			   GROUP BY {group_by}"""

    cursor.execute(query)
    result = cursor.fetchall()
    response = ""
    for row in result:
        response += f"Total de Vacinados para covid em {row[0]}: {row[1]}\n"
        response += f"Total de Vacinados para gripe em {row[0]}: {row[2]}\n"
    return response

def _fetch_uti_occupancy_rate(start_date: str = None, end_date: str = None, group_by: str = "year") -> str:
    time_period_filter = f" AND data_preenchimento BETWEEN '{start_date}' AND '{end_date}'" if start_date and end_date else ""
    query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
               COUNT(internado_uti) AS total_internados_uti
			   from influd_data
			   WHERE internado_uti = 1
			   {time_period_filter}
			   GROUP BY {group_by}"""
    cursor.execute(query)
    result = cursor.fetchall()
    response = ""
    for row in result:
        response += f"Total de Internados em UTI em {row[0]}: {row[1]}\n"
    return response

def _fetch_mortality_rate(start_date: str = None, end_date: str = None, group_by: str = "year") -> str:
    time_period_filter = f" AND data_preenchimento BETWEEN '{start_date}' AND '{end_date}'" if start_date and end_date else ""
    query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
               COUNT(evolucao) AS total_obitos
			   from influd_data
			   WHERE evolucao = 2
			   {time_period_filter}
			   GROUP BY {group_by}"""
    cursor.execute(query)
    result = cursor.fetchall()
    response = ""
    for row in result:
        response += f"Total de Óbitos em {row[0]}: {row[1]}\n"
    return response

class QueryDataToolInput(BaseModel):
    data_to_fetch: Literal["total_cases", "vaccination_rate", "uti_occupancy_rate", "mortality_rate", "all"] = Field(description="The data to be fetched")
    start_date: Optional[str] = Field(description="The start date of the data to be fetched")
    end_date: Optional[str] = Field(description="The end date of the data to be fetched")
    group_by: Optional[str] = Field(description="The group by of the data to be fetched")

class QueryDataTool(BaseTool):
    name: str = "query_data"
    description: str = "A tool to query the data"
    args_schema: Type[BaseModel] = QueryDataToolInput
    
    def _run(self, input:QueryDataToolInput) -> str:
        try:
            match input.data_to_fetch:  
                case "total_cases":
                    return _fetch_total_cases(input.start_date, input.end_date, input.group_by)
                case "vaccination_rate":
                    return _fetch_vaccination_rate(input.start_date, input.end_date, input.group_by)
                case "uti_occupancy_rate":
                    return _fetch_uti_occupancy_rate(input.start_date, input.end_date, input.group_by)
                case "mortality_rate":
                    return _fetch_mortality_rate(input.start_date, input.end_date, input.group_by)
                case "all":
                    return f"Total de Casos: {_fetch_total_cases(input.start_date, input.end_date, input.group_by)}\n" + \
                    f"Total de Vacinados para covid: {_fetch_vaccination_rate(input.start_date, input.end_date, input.group_by)}\n" + \
                    f"Total de Vacinados para gripe: {_fetch_vaccination_rate(input.start_date, input.end_date, input.group_by)}\n" + \
                    f"Total de Internados em UTI: {_fetch_uti_occupancy_rate(input.start_date, input.end_date, input.group_by)}\n" + \
                    f"Total de Óbitos: {_fetch_mortality_rate(input.start_date, input.end_date, input.group_by)}"
                case _:
                    return "Data to fetch is invalid"   
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            cursor.close()
            connection.close()
        