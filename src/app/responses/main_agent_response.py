from pydantic import BaseModel, Field


class MainAgentResponse(BaseModel):
    p_aumento_dos_casos: str = Field(
        description="Cases increases analysis text paragraph. Must be 200 words or less."
    )
    p_taxa_de_mortalidade: str = Field(
        description="Mortality rate analysis text paragraph. Must be 200 words or less."
    )
    p_taxa_de_ocupacao_uti: str = Field(
        description="UTI occupancy rate analysis text paragraph. Must be 200 words or less."
    )
    p_taxa_de_vacinacao: str = Field(
        description="Vaccination rate analysis text paragraph. Must be 200 words or less."
    )
    p_last_30_days_analysis: str = Field(
        description="Last 30 days analysis text paragraph. Must be 200 words or less."
    )
    p_last_12_months_analysis: str = Field(
        description="Last 12 months analysis text paragraph. Must be 200 words or less."
    )
