from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Any
from src.app.agents.main_agent import MainAgent
from datetime import datetime, timedelta
from src.app.tools.tavily_search_tool import TavilySearchTool
from src.app.tools.query_data_tool import QueryDataTool
from pylatex import Document, Section, Subsection, Command, Figure, MiniPage
from pylatex.utils import NoEscape
from dateutil.relativedelta import relativedelta
import logging
import asyncio
import matplotlib.pyplot as plt
from io import StringIO
import pandas as pd
import locale

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
logger = logging.getLogger(__name__)


class ReportState(TypedDict):
    report_date: str
    report: dict[str, Any]
    sections: list[str]
    data: dict[str, Any]
    news: list[str]
    stage: str


def _build_report(state: ReportState):
    # Define document class
    p_aumento_dos_casos = state["report"].p_aumento_dos_casos
    p_taxa_de_mortalidade = state["report"].p_taxa_de_mortalidade
    p_taxa_de_ocupacao_uti = state["report"].p_taxa_de_ocupacao_uti
    p_taxa_de_vacinacao = state["report"].p_taxa_de_vacinacao
    p_last_30_days_analysis = state["report"].p_last_30_days_analysis
    p_last_12_months_analysis = state["report"].p_last_12_months_analysis

    report_date_obj = datetime.strptime(state["report_date"], "%Y-%m-%d")
    formatted_date = report_date_obj.strftime("%d de %B de %Y")

    ##Latex Configuration
    geometry_options = {"margin": "1in"}
    doc = Document(documentclass="article", geometry_options=geometry_options)

    # Add required packages
    doc.packages.append(NoEscape(r"\usepackage[utf8]{inputenc}"))
    doc.packages.append(NoEscape(r"\usepackage[titletoc,title]{appendix}"))
    doc.packages.append(NoEscape(r"\usepackage{graphicx,float}"))

    # Title
    doc.preamble.append(
        Command(
            "title",
            NoEscape(r"\textbf{RELATÓRIO TÉCNICO DE SAÚDE PÚBLICA - SRAG BRASIL}"),
        )
    )
    doc.preamble.append(Command("date", formatted_date))
    doc.append(NoEscape(r"\maketitle"))

    # Section: Análise
    with doc.create(Section("Análise")):
        with doc.create(Subsection("Geral")):
            doc.append(p_aumento_dos_casos + "\n")
            doc.append(p_taxa_de_mortalidade + "\n")
            doc.append(p_taxa_de_ocupacao_uti + "\n")
            doc.append(p_taxa_de_vacinacao + "\n")

            # with doc.create(Figure(position="H")) as fig:
            #     for caption, label in [
            #         ("Total de Casos", "fig:casos-total-por-ano"),
            #         ("Total de Óbitos", "fig:obitos-total-por-ano"),
            #         ("Ocupação de UTI", "fig:uti-total-por-ano"),
            #         ("Taxa de Vacinação", "fig:vacinacao-total-por-ano"),
            #     ]:
            #         with doc.create(MiniPage(width=NoEscape("0.45\\textwidth"))) as mini:
            #             mini.append(NoEscape(r"\centering"))
            #             mini.append(NoEscape(r"\includegraphics[width=\textwidth]{dubs.jpg}"))
            #             mini.append(NoEscape(fr"\caption{{{caption}}}"))
            #             mini.append(NoEscape(fr"\label{{{label}}}"))

        with doc.create(Subsection("Relação Mensal e Anual")):
            doc.append(p_last_30_days_analysis + "\n")
            doc.append(p_last_12_months_analysis + "\n")
            with doc.create(Figure(position="H")) as fig:
                for caption, label, graphic in [
                    (
                        "Análise Mensal",
                        "fig:casos-30-dias",
                        "../graphics/monthly-analysis.png",
                    ),
                    (
                        "Análise Anual",
                        "fig:casos-12-meses",
                        "../graphics/yearly-analysis.png",
                    ),
                ]:
                    with doc.create(
                        MiniPage(width=NoEscape("0.45\\textwidth"))
                    ) as mini:
                        mini.append(NoEscape(r"\centering"))
                        mini.append(
                            NoEscape(
                                f"""\includegraphics[width=\\textwidth]{{{graphic}}}"""
                            )
                        )
                        mini.append(NoEscape(rf"\caption{{{caption}}}"))
                        mini.append(NoEscape(rf"\label{{{label}}}"))

    # Generate PDF
    doc.generate_pdf("src/data/reports/relatorio_influenza", clean_tex=False)


def _create_graphics(state: ReportState) -> ReportState:
    def _get_dataframe(csv_data: str) -> pd.DataFrame:
        df = pd.read_csv(StringIO(csv_data))
        return df

    def _create_and_save_chart(df: pd.DataFrame, filename: str, title: str) -> str:
        # Create the plot
        plt.figure(figsize=(10, 6))

        # Example: Create a bar chart or line plot
        if len(df.columns) == 2:
            df.plot(x=df.columns[0], y=df.columns[1], kind="bar")
        else:
            df.plot()

        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the figure
        path = f"src/data/graphics/{filename}.png"
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()  # Important: close the figure to free memory

        return path

    try:
        monthly = state["data"].get("monthly", "")
        one_year_interval = state["data"].get("one_year_interval", "")

        graphics_paths = []

        if monthly:
            df_monthly = _get_dataframe(monthly)
            path = _create_and_save_chart(
                df_monthly, "monthly-analysis", "Análise Diária - Últimos 30 dias"
            )
            graphics_paths.append(path)

        if one_year_interval:
            df_yearly = _get_dataframe(one_year_interval)
            path = _create_and_save_chart(
                df_yearly, "yearly-analysis", "Análise Mensal - Últimos 12 meses"
            )
            graphics_paths.append(path)

        state["graphics"] = graphics_paths
        return state
    except Exception as e:
        logger.error(f"Error creating graphics: {e}")
        return state


def _get_srag_news(state: ReportState) -> ReportState:
    try:
        logger.info(f"Getting news for {state['report_date']}")
        start_date = state["report_date"]
        end_date = (
            datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=15)
        ).strftime("%Y-%m-%d")
        search_tool = TavilySearchTool()
        news = asyncio.run(
            search_tool.ainvoke({"start_date": start_date, "end_date": end_date})
        )
        logger.info(f"Fetched {len(news)} news")
        state["news"] = news
        return state
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        return {"error": "Error getting news", "stage": "error"}


def _get_srag_data(state: ReportState) -> ReportState:
    try:
        query_tool = QueryDataTool()
        report_date = datetime.strptime(state["report_date"], "%Y-%m-%d")
        all_years_start_date = (report_date - relativedelta(years=4)).strftime(
            "%Y-%m-%d"
        )
        all_years_end_date = report_date.strftime("%Y-%m-%d")
        all_years = query_tool.invoke(
            {
                "data_to_fetch": "all",
                "start_date": all_years_start_date,
                "end_date": all_years_end_date,
            }
        )
        monthly = query_tool.invoke(
            {
                "data_to_fetch": "total_cases",
                "start_date": (report_date - relativedelta(months=1)).strftime(
                    "%Y-%m-%d"
                ),
                "end_date": report_date.strftime("%Y-%m-%d"),
                "group_by": "day",
            }
        )
        one_year_interval = query_tool.invoke(
            {
                "data_to_fetch": "total_cases",
                "start_date": (report_date - relativedelta(years=1)).strftime(
                    "%Y-%m-%d"
                ),
                "end_date": report_date.strftime("%Y-%m-%d"),
                "group_by": "month",
            }
        )
        state["data"] = {
            "all_years": all_years,
            "monthly": monthly,
            "one_year_interval": one_year_interval,
        }
        return state

    except Exception as e:
        logger.error(f"Error getting SRAG data: {e}")
        return {"error": "Error getting SRAG data", "stage": "error"}


graph = StateGraph(state_schema=ReportState)
graph.add_node("insert_news", _get_srag_news)
graph.add_node("insert_data", _get_srag_data)
graph.add_node("main_agent", MainAgent().execute)
graph.add_node("create_graphics", _create_graphics)
graph.add_node("build_report", _build_report)
graph.add_edge(START, "insert_data")
graph.add_edge("insert_news", "insert_data")
graph.add_edge("insert_data", "main_agent")
graph.add_edge("main_agent", "create_graphics")
graph.add_edge("create_graphics", "build_report")
graph.add_edge("build_report", END)

compiled_graph = graph.compile()
