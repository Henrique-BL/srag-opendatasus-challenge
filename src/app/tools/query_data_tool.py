from langchain_core.tools import BaseTool
from typing import Type, Literal, Optional, Union
from pydantic import BaseModel, Field
from src.utils.db import get_db_connection, verify_data_exists
from psycopg2._psycopg import cursor
from src.utils.formatting import create_response_message
import traceback
import logging

logger = logging.getLogger(__name__)

def _get_month_from_number(number: float) -> str:
    """
    Get the month name from the number.
    Args:
        number: float - The number of the month.
    Returns:
        str - The month.
    """
    months = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    return months[int(number) - 1]


def _get_csv_data(
    result: list[tuple[float, int]], columns: list[str], time_period: str
) -> str:
    """
    Purpose: Get the csv data from the result.
    Args:
        result: list[tuple[float, int]] - The result of the query.
        columns: list[str] - The columns of the data to be fetched.
        time_period: str - The time period of the data to be fetched.
    Returns:
        str - Csv string with columns 'group_by' and the columns of the data to be fetched.
    """
    time_period_translation = {"month": "Mês", "year": "Ano", "day": "Dia"}
    csv_data = f"{time_period_translation[time_period]},{','.join(columns)}\n"
    for row in result:
        data = _get_month_from_number(row[0]) if time_period == "month" else row[0]
        csv_data += f"{data},{','.join(map(str, row[1:]))}\n"
    return csv_data

def verify_report_date(report_date: str) -> str:
    """
    Purpose: Verify if the report date exists in the database.
    Args:
        report_date: str - The report date.
    Returns:
        str - The report date.
    """
    logger.info(f"Verifying if report date {report_date} exists in the database")
    try:
        connection = get_db_connection()
        most_recent_date = report_date
        cursor = connection.cursor()
        verify = verify_data_exists(cursor, "influd_data", ["data_preenchimento"],
                                report_date)
        if not verify:
            logger.error(f"Report date {report_date} not found in the database, returning most recent date")
            query = "SELECT MAX(data_preenchimento) FROM influd_data"
            cursor.execute(query)
            most_recent_date = cursor.fetchone()[0]
            logger.info(f"Report Date not found, trying with most recent date: {most_recent_date}")

        return most_recent_date
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error verifying report date: {str(e)}")
        return verify
    finally:
        cursor.close()
        connection.close()

def _fetch_total_cases(
    cursor: cursor, start_date: str, end_date: str, group_by: str
) -> str:
    """
    Purpose: Fetch the total cases from the database.
    Args:
        cursor: cursor - The cursor to the database.
        start_date: str - The start date of the data to be fetched.
        end_date: str - The end date of the data to be fetched.
        group_by: str - The group by of the data to be fetched.
    Returns:
        str - Csv string with columns 'group_by' and 'total_casos'.
    """
    try:
        time_period_filter = (
            f"WHERE data_preenchimento BETWEEN '{start_date}' AND '{end_date}'"
            if start_date and end_date
            else ""
        )
        query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
                COUNT(*) FROM influd_data 
                {time_period_filter}
                GROUP BY {group_by}"""
        cursor.execute(query)
        result = cursor.fetchall()
        csv_data = _get_csv_data(result, ["Total de Casos"], group_by)
        return csv_data
    except Exception as e:
        traceback.print_exc()
        logger.error({str(e)})
        return f"No data was retrived for total cases with start date: {start_date} and end date: {end_date} and group by: {group_by}"


def _fetch_vaccination_rate(
    cursor: cursor, start_date: str, end_date: str, group_by: str
) -> str:
    """
    Purpose: Fetch the vaccination rate from the database.
    Args:
        cursor: cursor - The cursor to the database.
        start_date: str - The start date of the data to be fetched.
        end_date: str - The end date of the data to be fetched.
        group_by: str - The group by of the data to be fetched.
    Returns:
        str - Csv string with columns 'group_by' and 'total_vacinados_covid' and 'total_vacinados_gripe'.
    """
    try:
        time_period_filter = (
            f" AND data_preenchimento BETWEEN '{start_date}' AND '{end_date}'"
            if start_date and end_date
            else ""
        )
        query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
                COUNT(vacina_covid) AS total_vacinados_covid,
                COUNT(vacina_gripe) AS total_vacinados_gripe
                FROM influd_data
                WHERE vacina_covid = 1 AND vacina_gripe = 1
                {time_period_filter}
                GROUP BY {group_by}"""

        cursor.execute(query)
        result = cursor.fetchall()
        csv_data = _get_csv_data(
            result,
            ["Total de Vacinados para covid", "Total de Vacinados para gripe"],
                group_by,
            )
        return csv_data
    except Exception as e:
        traceback.print_exc()
        logger.error(f"No data was retrived for vaccination rate: {str(e)}")
        return f"No data was retrived for vaccination rate with start date: {start_date} and end date: {end_date} and group by: {group_by}"

def _fetch_uti_occupancy_rate(
    cursor: cursor, start_date: str, end_date: str, group_by: str
) -> str:
    """
    Purpose: Fetch the uti occupancy rate from the database.
    Args:
        cursor: cursor - The cursor to the database.
        start_date: str - The start date of the data to be fetched.
        end_date: str - The end date of the data to be fetched.
        group_by: str - The group by of the data to be fetched.
    Returns:
        str - Csv string with columns 'group_by' and 'total_internados_uti'.
    """
    try:
        time_period_filter = (
            f" AND data_preenchimento BETWEEN '{start_date}' AND '{end_date}'"
            if start_date and end_date
            else ""
        )
        query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
                COUNT(internado_uti) AS total_internados_uti
                from influd_data
                WHERE internado_uti = 1
                {time_period_filter}
                GROUP BY {group_by}"""
        cursor.execute(query)
        result = cursor.fetchall()
        csv_data = _get_csv_data(result, ["Total de Internados em UTI"], group_by)
        return csv_data
    except Exception as e:
        traceback.print_exc()
        logger.error(f"No data was retrived for uti occupancy rate: {str(e)}")
        return f"No data was retrived for uti occupancy rate with start date: {start_date} and end date: {end_date} and group by: {group_by}"


def _fetch_mortality_rate(
    cursor: cursor, start_date: str, end_date: str, group_by: str
) -> str:
    """
    Purpose: Fetch the mortality rate from the database.
    Args:
        cursor: cursor - The cursor to the database.
        start_date: str - The start date of the data to be fetched.
        end_date: str - The end date of the data to be fetched.
        group_by: str - The group by of the data to be fetched.
    Returns:
        str - Csv string with columns 'group_by' and 'total_obitos'.
    """
    try:
        time_period_filter = (
            f" AND data_preenchimento BETWEEN '{start_date}' AND '{end_date}'"
            if start_date and end_date
            else ""
        )
        query = f"""SELECT DATE_PART('{group_by}', data_preenchimento) AS {group_by},
                COUNT(evolucao) AS total_obitos
                from influd_data
                WHERE evolucao = 2
                {time_period_filter}
                GROUP BY {group_by}"""
        cursor.execute(query)
        result = cursor.fetchall()
        csv_data = _get_csv_data(result, ["Total de Óbitos"], group_by)
        return csv_data
    except Exception as e:
        traceback.print_exc()
        logger.error(f"No data was retrived for mortality rate: {str(e)}")
        return f"No data was retrived for mortality rate with start date: {start_date} and end date: {end_date} and group by: {group_by}"


class QueryDataToolInput(BaseModel):
    data_to_fetch: Literal[
        "total_cases", "vaccination_rate", "uti_occupancy_rate", "mortality_rate", "all"
    ] = Field(description="The data to be fetched")
    start_date: Optional[str] = Field(
        None, description="The start date of the data to be fetched"
    )
    end_date: Optional[str] = Field(
        None, description="The end date of the data to be fetched"
    )
    group_by: Optional[Literal["month", "year", "day"]] = Field(
        None, description="The group by of the data to be fetched"
    )


class QueryDataTool(BaseTool):
    """
    Purpose: A tool to query the data from the database.
    Args:
        data_to_fetch: Literal["total_cases", "vaccination_rate", "uti_occupancy_rate", "mortality_rate", "all"] - The data to be fetched.
        start_date: str | None - The start date of the data to be fetched.
        end_date: str | None - The end date of the data to be fetched.
        group_by: Literal["month", "year", "day"] | None - The group by of the data to be fetched.
    Returns:
        str | dict[str, str] - The data fetched from the database.
    """

    name: str = "query_data"
    description: str = "A tool to query the data"
    args_schema: Type[BaseModel] = QueryDataToolInput

    def _run(
        self,
        data_to_fetch: str = "all",
        start_date: str = None,
        end_date: str = None,
        group_by: str = "year",
    ) -> str:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            data = None
            match data_to_fetch:
                case "total_cases":
                    data = _fetch_total_cases(cursor, start_date, end_date, group_by)
                case "vaccination_rate":
                    data = _fetch_vaccination_rate(
                        cursor, start_date, end_date, group_by
                    )
                case "uti_occupancy_rate":
                    data = _fetch_uti_occupancy_rate(
                        cursor, start_date, end_date, group_by
                    )
                case "mortality_rate":
                    data = _fetch_mortality_rate(cursor, start_date, end_date, group_by)
                case "all":
                    data = {
                        "total_cases": _fetch_total_cases(
                            cursor, start_date, end_date, group_by
                        ),
                        "vaccination_rate": _fetch_vaccination_rate(
                            cursor, start_date, end_date, group_by
                        ),
                        "uti_occupancy_rate": _fetch_uti_occupancy_rate(
                            cursor, start_date, end_date, group_by
                        ),
                        "mortality_rate": _fetch_mortality_rate(
                            cursor, start_date, end_date, group_by
                        ),
                    }
                case _:
                    logger.error("Data type to fetch is invalid")
                    return create_response_message("error",
                                                   "Data type to fetch is invalid")
            response = create_response_message("success", data)
            return response
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error querying data: {str(e)}")
            return create_response_message("error", 
                                           f"Error querying data: {str(e)}")
        finally:
            cursor.close()
            connection.close()
