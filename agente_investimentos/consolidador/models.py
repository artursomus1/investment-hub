"""Modelos de dados para consolidacao de carteiras multi-instituicao."""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ParsedAssetInst:
    """Ativo extraido de um relatorio de instituicao."""
    nome: str
    ticker: str  # quando disponivel (acoes), senao nome curto
    tipo: str  # Renda Fixa, Multimercado, Op. Estruturadas, Acao, FII, Opcao, Futuro, Curto Prazo
    subtipo: str  # CDB, LCA, CRA, CRI, Debenture, Fundo RF, etc.
    saldo_bruto: float
    saldo_liquido: float
    impostos: float
    alocacao_pct: float  # % do patrimonio da instituicao
    rent_mes: float  # % rentabilidade no mes
    rent_ano: float  # % rentabilidade no ano
    rent_12m: float  # % rentabilidade 12 meses
    indexador: str  # CDI, IPCA, PRE, etc.
    taxa: str  # ex: "96,08% CDI", "IPCA+8,04%"
    vencimento: str
    emissor: str
    instituicao: str  # Safra, BTG, XP, etc.


@dataclass
class InstitutionData:
    """Dados consolidados de uma unica instituicao."""
    nome: str  # Safra, BTG Pactual, XP, etc.
    cliente: str
    conta: str
    data_referencia: str
    patrimonio_bruto: float
    patrimonio_liquido: float
    impostos_totais: float
    rent_carteira_mes: float
    rent_carteira_ano: float
    rent_carteira_12m: float
    cdi_mes: float  # % CDI equivalente no mes
    cdi_ano: float
    perfil_investidor: str  # Conservador, Moderado, Arrojado
    ativos: List[ParsedAssetInst] = field(default_factory=list)
    distribuicao_tipo: Dict[str, float] = field(default_factory=dict)  # tipo -> % PL

    @property
    def num_ativos(self) -> int:
        return len(self.ativos)


@dataclass
class ConsolidatedPortfolio:
    """Carteira consolidada de todas as instituicoes."""
    instituicoes: List[InstitutionData] = field(default_factory=list)

    @property
    def patrimonio_bruto_total(self) -> float:
        return sum(i.patrimonio_bruto for i in self.instituicoes)

    @property
    def patrimonio_liquido_total(self) -> float:
        return sum(i.patrimonio_liquido for i in self.instituicoes)

    @property
    def impostos_totais(self) -> float:
        return sum(i.impostos_totais for i in self.instituicoes)

    @property
    def num_ativos_total(self) -> int:
        return sum(i.num_ativos for i in self.instituicoes)

    @property
    def num_instituicoes(self) -> int:
        return len(self.instituicoes)

    @property
    def todos_ativos(self) -> List[ParsedAssetInst]:
        result = []
        for inst in self.instituicoes:
            result.extend(inst.ativos)
        return result

    def rent_mes_ponderada(self) -> float:
        """Rentabilidade mensal ponderada pelo patrimonio."""
        total = self.patrimonio_bruto_total
        if total == 0:
            return 0.0
        return sum(
            i.rent_carteira_mes * i.patrimonio_bruto
            for i in self.instituicoes
        ) / total

    def rent_ano_ponderada(self) -> float:
        """Rentabilidade anual ponderada pelo patrimonio."""
        total = self.patrimonio_bruto_total
        if total == 0:
            return 0.0
        return sum(
            i.rent_carteira_ano * i.patrimonio_bruto
            for i in self.instituicoes
        ) / total

    def distribuicao_por_tipo(self) -> Dict[str, Dict]:
        """Distribuicao consolidada por tipo de ativo."""
        tipos = {}
        total = self.patrimonio_bruto_total
        for ativo in self.todos_ativos:
            t = ativo.tipo
            if t not in tipos:
                tipos[t] = {"count": 0, "saldo_bruto": 0.0, "saldo_liquido": 0.0}
            tipos[t]["count"] += 1
            tipos[t]["saldo_bruto"] += ativo.saldo_bruto
            tipos[t]["saldo_liquido"] += ativo.saldo_liquido
        for t in tipos:
            tipos[t]["alocacao"] = (tipos[t]["saldo_bruto"] / total * 100) if total else 0
        return dict(sorted(tipos.items(), key=lambda x: x[1]["saldo_bruto"], reverse=True))

    def distribuicao_por_instituicao(self) -> Dict[str, Dict]:
        """Distribuicao consolidada por instituicao."""
        total = self.patrimonio_bruto_total
        result = {}
        for inst in self.instituicoes:
            result[inst.nome] = {
                "patrimonio_bruto": inst.patrimonio_bruto,
                "patrimonio_liquido": inst.patrimonio_liquido,
                "num_ativos": inst.num_ativos,
                "alocacao": (inst.patrimonio_bruto / total * 100) if total else 0,
                "rent_mes": inst.rent_carteira_mes,
                "rent_ano": inst.rent_carteira_ano,
                "rent_12m": inst.rent_carteira_12m,
                "perfil": inst.perfil_investidor,
            }
        return result

    def ranking_risco_por_instituicao(self) -> List[Dict]:
        """Ranking de instituicoes por quantidade de ativos de risco."""
        _TIPOS_RISCO = {"Acao", "Multimercado", "Op. Estruturadas", "Opcao", "Futuro"}
        ranking = []
        for inst in self.instituicoes:
            risco_count = sum(1 for a in inst.ativos if a.tipo in _TIPOS_RISCO)
            risco_saldo = sum(a.saldo_bruto for a in inst.ativos if a.tipo in _TIPOS_RISCO)
            total_saldo = inst.patrimonio_bruto or 1
            ranking.append({
                "instituicao": inst.nome,
                "ativos_risco": risco_count,
                "saldo_risco": risco_saldo,
                "pct_risco": risco_saldo / total_saldo * 100,
                "ativos_total": inst.num_ativos,
            })
        ranking.sort(key=lambda x: x["pct_risco"], reverse=True)
        return ranking

    def piores_rentabilidades(self) -> List[Dict]:
        """Ativos com piores rentabilidades no ano."""
        ativos = [a for a in self.todos_ativos if a.rent_ano != 0]
        ativos.sort(key=lambda a: a.rent_ano)
        result = []
        for a in ativos[:10]:
            result.append({
                "nome": a.nome, "ticker": a.ticker, "tipo": a.tipo,
                "instituicao": a.instituicao,
                "saldo_bruto": a.saldo_bruto,
                "rent_mes": a.rent_mes, "rent_ano": a.rent_ano,
            })
        return result

    def melhores_rentabilidades(self) -> List[Dict]:
        """Ativos com melhores rentabilidades no ano."""
        ativos = [a for a in self.todos_ativos if a.rent_ano != 0]
        ativos.sort(key=lambda a: a.rent_ano, reverse=True)
        result = []
        for a in ativos[:10]:
            result.append({
                "nome": a.nome, "ticker": a.ticker, "tipo": a.tipo,
                "instituicao": a.instituicao,
                "saldo_bruto": a.saldo_bruto,
                "rent_mes": a.rent_mes, "rent_ano": a.rent_ano,
            })
        return result
