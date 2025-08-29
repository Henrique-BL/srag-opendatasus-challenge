from typing import Dict, Any
import logging
import psycopg2
from ..utils.db import get_db_connection

logger = logging.getLogger(__name__)


def create_database(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Purpose: Create a new database 'srag_brasil' that will be used to store the data.
    """
    try:
        admin_conn = get_db_connection("postgres")
        admin_cursor = admin_conn.cursor()
        command = "CREATE DATABASE srag_brasil"
        admin_conn.set_session(autocommit=True)
        admin_cursor.execute(command)
        logger.info("Database created successfully...")
        state["stage"] = "database_created"
        return state
    except psycopg2.errors.DuplicateDatabase:
        logger.info("Database already exists, continuing...")
        state["stage"] = "database_already_exists"
        return state
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        state["stage"] = "error"
        return state
    finally:
        admin_cursor.close()
        admin_conn.close()


def create_table(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Purpose: Force the creation of a new empty table 'influd_data' that will be
    used to store the data.
    """
    try:
        conn = get_db_connection("srag_brasil")
        cursor = conn.cursor()
        drop_table_sql = "DROP TABLE IF EXISTS srag_brasil.public.influd_data;"

        create_table_sql = """
        CREATE TABLE srag_brasil.public.influd_data (
            id BIGSERIAL,                    
            origin_id BIGINT,             
            data_preenchimento DATE,
            vacina_covid INTEGER,
            vacina_gripe INTEGER,
            internado_hospital INTEGER,
            data_internacao_hospital DATE,
            internado_uti INTEGER,
            data_entrada_uti DATE,
            data_saida_uti DATE,
            diagnostico_final INTEGER,
            evolucao INTEGER,
            data_evolucao DATE,
            data_primeiro_sintoma DATE,
            PRIMARY KEY (id, origin_id)   
        )
        """

        cursor.execute(drop_table_sql)
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info("Table created successfully...")
        state["stage"] = "table_created"
        return state
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        state["stage"] = "error"
        return state
    finally:
        cursor.close()
        conn.close()
