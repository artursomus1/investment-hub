"""
Agente de Investimentos - Somus Capital
========================================
Ponto de entrada único.

Uso:
    python executar.py

Pré-requisitos:
    1. Configure o .env com BRAPI_TOKEN e GEMINI_API_KEY
    2. Coloque o PDF XP Performance em COLETA DE DADOS/
    3. Execute: python executar.py
    4. O relatório será gerado em SAIDA DE DADOS/
"""

import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
_project_dir = Path(__file__).resolve().parent
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))


def main():
    print()
    print("=" * 60)
    print("  AGENTE DE INVESTIMENTOS - SOMUS CAPITAL")
    print("  Análise Automatizada de Carteira XP Performance")
    print("=" * 60)

    try:
        from agente_investimentos.main import run
        result = run()
        print(f"\nRelatório gerado com sucesso: {result['detailed_path']}")
    except KeyboardInterrupt:
        print("\n\nExecução cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
