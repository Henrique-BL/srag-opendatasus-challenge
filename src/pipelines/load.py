from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Dict, Any
from .setup import create_table, create_database
import pandas as pd
import logging
from ..utils.db import get_db_connection


logging.basicConfig(
    level=logging.INFO,               
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

class LoadPipelineState(TypedDict):
    data: pd.DataFrame
    stage: str

def _insert_data(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Connect to the target database
        conn = get_db_connection("srag_brasil")
        cursor = conn.cursor()
        columns = [
                   "origin_id", 
                   "data_preenchimento",
                   "vacina_covid",
                   "vacina_gripe",
                   "internado_hospital",
                   "data_internacao_hospital",
                   "internado_uti", 
                   "data_entrada_uti",
                   "data_saida_uti", 
                   "diagnostico_final", 
                   "evolucao", 
                   "data_evolucao",
                   "data_primeiro_sintoma"]

        with open("src/data/silver/INFLUD21-25.csv", "r") as file:
            # Skip the header row by reading the first line
            next(file)
            cursor.copy_from(file, "influd_data", sep=';', null="", columns=columns)
        conn.commit()
        logger.info("Data inserted successfully.")
        state["stage"] = "data_ETL_completed"
        return state
    except Exception as e:
        logger.error(f"Error inserting data: {e}")
        conn.rollback()
        state["stage"] = "error"
        return state
    finally:
        cursor.close()
        conn.close()

graph = StateGraph(state_schema=LoadPipelineState)
graph.add_node("create_database", create_database)
graph.add_node("create_table", create_table)
graph.add_node("insert_data", _insert_data)
graph.add_edge(START, "create_database")
graph.add_edge("create_database", "create_table")
graph.add_edge("create_table", "insert_data")
graph.add_edge("insert_data", END)

compiled_graph = graph.compile()

if __name__ == "__main__":
    try:
        result = compiled_graph.invoke({"stage": "start", "data": pd.DataFrame()})
        logger.info(f"ETL pipeline completed with stage: {result.get('stage', 'unknown')}")
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")

