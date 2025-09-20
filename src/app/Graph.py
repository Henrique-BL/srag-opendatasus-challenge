from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Any
from src.app.agents.main_agent import MainAgent
from datetime import datetime, timedelta
from src.app.tools.tavily_search_tool import TavilySearchTool
from src.app.tools.query_data_tool import QueryDataTool, verify_report_date
from pylatex import Document, Section, Subsection, Command, Figure, MiniPage
from pylatex.utils import NoEscape
from dateutil.relativedelta import relativedelta
from io import StringIO
import logging
import asyncio
import matplotlib.pyplot as plt
import pandas as pd
import locale
import traceback

logger = logging.getLogger(__name__)


# Set Portuguese Brazil locale with fallback options
try:
    logger.info("Setting locale to pt_BR.UTF-8")
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except locale.Error:
    try:
        logger.info("Setting locale to pt_BR")
        locale.setlocale(locale.LC_ALL, "pt_BR")
    except locale.Error:
        try:
            logger.info("Setting locale to C.UTF-8")
            locale.setlocale(locale.LC_ALL, "C.UTF-8")
        except locale.Error:
            # Fallback to system default
            logger.info("Setting locale to system default")
            locale.setlocale(locale.LC_ALL, "")
            
class ReportState(TypedDict):
    report_date: str
    report: dict[str, Any]
    sections: list[str]
    data: dict[str, Any]
    news: list[str]
    stage: str


def _build_report(state: ReportState):
    try:
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
        state["stage"] = "success"
        return state
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error building report: {e}")
        state["stage"] = "error"
        return state


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
        state["stage"] = "success"
        return state
    except Exception as e:
        logger.error(f"Error creating graphics: {e}")
        state["stage"] = "error"
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
        if news.get("status") == "error":
            state["stage"] = "error"
        else:
            state["stage"] = "success"
        state["news"] = news.get("response")
        return state
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        state["stage"] = "error"
        return state


def _get_srag_data(state: ReportState) -> ReportState:
    try:
        report_date = verify_report_date(state["report_date"])
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
        if (
            all_years.get("status") == "error"
            or monthly.get("status") == "error"
            or one_year_interval.get("status") == "error"
        ):
            state["stage"] = "error"
        else:
            state["stage"] = "success"
        state["data"] = {
            "all_years": all_years.get("response")
            if all_years.get("status") == "success"
            else [],
            "monthly": monthly.get("response")
            if monthly.get("status") == "success"
            else [],
            "one_year_interval": one_year_interval.get("response")
            if one_year_interval.get("status") == "success"
            else [],
        }
        return state

    except Exception as e:
        logger.error(f"Error getting SRAG data: {e}")
        traceback.print_exc()
        state["stage"] = "error"
        return state


def _verify_step(state: ReportState) -> str:
    """Verification function that checks if we should continue or end the process"""
    if state.get("stage") == "error":
        logger.error("Error detected, ending process")
        return "END"
    elif state.get("stage") == "fatal_error":
        logger.error("Fatal error detected, ending process")
        return "END"
    else:
        return "CONTINUE"


def _create_node_with_verification(node_name, node_func):
    """Wrapper that adds verification logic after node execution"""

    def wrapped_node(state: ReportState) -> ReportState:
        # Execute the original node function
        logger.info(f"Node {node_name} started")
        result_state = node_func(state)
        # Log the current stage for debugging
        logger.info(
            f"Node {node_name} completed with stage: {result_state.get('stage', 'unknown')}"
        )

        return result_state

    return wrapped_node


def add_sequence_with_verification(
    graph: StateGraph, nodes_and_funcs: list[tuple[str, callable]]
):
    """
    Custom helper that mimics add_sequence but adds verification after each node
    """
    for i, (node_name, node_func) in enumerate(nodes_and_funcs):
        # Add the node with verification wrapper
        graph.add_node(node_name, _create_node_with_verification(node_name, node_func))
        # Add conditional edges for verification
        if i == 0:
            # First node - set as entry point
            graph.set_entry_point(node_name)
        if i < len(nodes_and_funcs) - 1:
            # Not the last node - connect to next
            next_node = nodes_and_funcs[i + 1][0]
            graph.add_conditional_edges(
                node_name, _verify_step, {"CONTINUE": next_node, "END": END}
            )
        else:
            # Last node - connect to END
            graph.add_conditional_edges(
                node_name, _verify_step, {"CONTINUE": END, "END": END}
            )


# Create the graph
graph = StateGraph(state_schema=ReportState)
main_agent = MainAgent()
# Use our custom sequence builder with verification
nodes_sequence = [
    ("insert_data", _get_srag_data),
    ("insert_news", _get_srag_news),
    ("main_agent", main_agent.execute),
    ("create_graphics", _create_graphics),
    ("build_report", _build_report),
]

add_sequence_with_verification(graph, nodes_sequence)

compiled_graph = graph.compile()
