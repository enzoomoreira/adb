"""
Schemas Pydantic para validacao de configuracoes de indicadores.

Fornece validacao em runtime para garantir que configuracoes de indicadores
estejam corretas antes de fazer requisicoes a APIs externas.
"""

from typing import Literal, Any
from pydantic import BaseModel, Field, field_validator, ValidationError


# Tipos de frequencia suportados
FrequencyType = Literal["daily", "monthly", "quarterly", "yearly"]


class IndicatorConfig(BaseModel):
    """
    Schema base para configuracao de indicador.

    Campos comuns a todos os tipos de indicadores.
    """
    name: str = Field(..., min_length=1, description="Nome do indicador")
    frequency: FrequencyType = Field(..., description="Frequencia dos dados")
    description: str | None = Field(None, description="Descricao do indicador")

    model_config = {"extra": "allow"}  # Permite campos extras


class SGSIndicatorConfig(IndicatorConfig):
    """
    Schema para indicadores SGS (Banco Central).

    Campos:
        code: Codigo numerico da serie no SGS
        name: Nome do indicador
        frequency: Frequencia (daily, monthly, etc)
        description: Descricao opcional
    """
    code: int = Field(..., gt=0, description="Codigo SGS da serie")


class IPEAIndicatorConfig(IndicatorConfig):
    """
    Schema para indicadores IPEA.

    Campos:
        code: Codigo string da serie no IPEADATA
        name: Nome do indicador
        frequency: Frequencia (monthly, etc)
        description: Descricao opcional
        unit: Unidade de medida (ex: "pessoas", "%")
        source: Fonte dos dados (ex: "MTE/CAGED")
    """
    code: str = Field(..., min_length=1, description="Codigo IPEA da serie")
    unit: str | None = Field(None, description="Unidade de medida")
    source: str | None = Field(None, description="Fonte dos dados")

    @field_validator("code")
    @classmethod
    def validate_ipea_code(cls, v: str) -> str:
        """Valida que codigo IPEA nao esta vazio."""
        if not v.strip():
            raise ValueError("Codigo IPEA nao pode estar vazio")
        return v.strip()


class SIDRAIndicatorConfig(IndicatorConfig):
    """
    Schema para indicadores SIDRA (IBGE).

    Campos:
        code: Codigo numerico da tabela SIDRA
        name: Nome do indicador
        frequency: Frequencia (monthly, quarterly, etc)
        parameters: Parametros da consulta SIDRA
        description: Descricao opcional
    """
    code: int = Field(..., gt=0, description="Codigo da tabela SIDRA")
    parameters: dict[str, Any] = Field(..., description="Parametros da consulta SIDRA")

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v: dict) -> dict:
        """Valida campos obrigatorios dos parametros SIDRA."""
        required_fields = [
            "agregados",
            "periodos",
            "variaveis",
            "nivel_territorial",
            "localidades",
        ]
        missing = [f for f in required_fields if f not in v]
        if missing:
            raise ValueError(f"Parametros SIDRA faltando campos: {missing}")
        return v


def validate_indicator_config(
    config: dict[str, dict],
    schema_class: type[IndicatorConfig],
) -> dict[str, IndicatorConfig]:
    """
    Valida um dicionario de configuracoes de indicadores.

    Args:
        config: Dicionario {chave: config_dict}
        schema_class: Classe do schema a usar (SGSIndicatorConfig, etc)

    Returns:
        Dicionario {chave: schema_validado}

    Raises:
        ValueError: Se alguma configuracao for invalida, indicando qual key falhou

    Example:
        from adb.bacen.sgs.indicators import SGS_CONFIG
        validated = validate_indicator_config(SGS_CONFIG, SGSIndicatorConfig)
    """
    validated = {}
    for key, value in config.items():
        try:
            validated[key] = schema_class.model_validate(value)
        except ValidationError as e:
            raise ValueError(f"Erro validando indicador '{key}': {e}") from e
    return validated
