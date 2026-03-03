"""Exceções customizadas do agente de investimentos."""


class AgenteError(Exception):
    """Erro base do agente."""


class PDFExtractionError(AgenteError):
    """Erro ao extrair dados do PDF."""


class APIError(AgenteError):
    """Erro em chamada de API externa."""


class CacheError(AgenteError):
    """Erro no sistema de cache."""


class AnalysisError(AgenteError):
    """Erro durante análise de ativos."""


class ReportError(AgenteError):
    """Erro na geração do relatório."""
