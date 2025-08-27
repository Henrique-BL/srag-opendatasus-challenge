from pydantic import BaseModel, Field

class SummarizerAgentResponse(BaseModel):
    p_aumento_dos_casos: str = Field(description="Paragraph explaning the relation between cases uprises or decreases with the healthcare news")
    p_taxa_de_mortalidade: str = Field(description="Paragraph explaning the relation between mortality rate uprises or decreases with the healthcare news")
    p_taxa_de_ocupacao_uti: str = Field(description="Paragraph explaning the relation between UTI occupancy rate uprises or decreases with the healthcare news")
    p_taxa_de_vacinacao: str = Field(description="Paragraph explaning the relation between vaccination rate uprises or decreases with the healthcare news")