"""
Script para testar geração de gráficos localmente
Execute: python test_graficos.py
"""

import os
import sys

# Adicionar path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from utils.statistics import (
    get_github_commits_stats,
    generate_commits_report,
    generate_commits_chart,
    generate_commits_timeline,
    get_trello_cards_stats,
    generate_trello_report,
    generate_trello_pie_chart
)

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_github_charts():
    """Testa gráficos do GitHub"""
    print("=" * 50)
    print("🧪 TESTANDO GRÁFICOS DO GITHUB")
    print("=" * 50)
    
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPO')
    
    if not github_repo:
        print("❌ GITHUB_REPO não configurado no .env")
        return
    
    print(f"📊 Repositório: {github_repo}\n")
    
    # 1. Buscar estatísticas
    print("1️⃣ Buscando estatísticas...")
    stats = get_github_commits_stats(github_token, github_repo, limit=100)
    
    if not stats:
        print("❌ Erro ao buscar estatísticas")
        return
    
    print(f"✅ {stats['total_commits']} commits analisados")
    print(f"✅ {stats['total_authors']} contribuidores\n")
    
    # 2. Gerar relatório textual
    print("2️⃣ Gerando relatório textual...")
    report = generate_commits_report(stats)
    print(report)
    print()
    
    # 3. Gerar gráfico de barras
    print("3️⃣ Gerando gráfico de barras (ranking)...")
    chart_buffer = generate_commits_chart(stats)
    
    if chart_buffer:
        # Salvar localmente
        with open('grafico_ranking_commits.png', 'wb') as f:
            f.write(chart_buffer.getvalue())
        print("✅ Gráfico salvo: grafico_ranking_commits.png")
    else:
        print("❌ Erro ao gerar gráfico de barras")
    
    print()
    
    # 4. Gerar gráfico de linha (evolução)
    print("4️⃣ Gerando gráfico de linha (evolução temporal)...")
    timeline_buffer, timeline_stats = generate_commits_timeline(github_token, github_repo, days=30)
    
    if timeline_buffer:
        # Salvar localmente
        with open('grafico_evolucao_commits.png', 'wb') as f:
            f.write(timeline_buffer.getvalue())
        print("✅ Gráfico salvo: grafico_evolucao_commits.png")
        print(f"   • Total: {timeline_stats['total_commits']} commits")
        print(f"   • Média/dia: {timeline_stats['avg_per_day']}")
        print(f"   • Máximo em 1 dia: {timeline_stats['max_in_day']}")
    else:
        print("❌ Erro ao gerar gráfico de linha")
    
    print()


def test_trello_charts():
    """Testa gráficos do Trello"""
    print("=" * 50)
    print("🧪 TESTANDO GRÁFICOS DO TRELLO")
    print("=" * 50)
    
    api_key = os.getenv('TRELLO_API_KEY')
    token = os.getenv('TRELLO_TOKEN')
    board_id = os.getenv('TRELLO_BOARD_ID')
    
    if not all([api_key, token, board_id]):
        print("❌ Credenciais do Trello não configuradas no .env")
        return
    
    print(f"📊 Board ID: {board_id}\n")
    
    # 1. Buscar estatísticas
    print("1️⃣ Buscando estatísticas...")
    stats = get_trello_cards_stats(api_key, token, board_id)
    
    if not stats:
        print("❌ Erro ao buscar estatísticas")
        return
    
    print(f"✅ {stats['total_cards']} cards analisados")
    print(f"✅ {stats['total_lists']} listas\n")
    
    # 2. Gerar relatório textual
    print("2️⃣ Gerando relatório textual...")
    report = generate_trello_report(stats)
    print(report)
    print()
    
    # 3. Gerar gráfico de pizza
    print("3️⃣ Gerando gráfico de pizza (distribuição)...")
    chart_buffer = generate_trello_pie_chart(stats)
    
    if chart_buffer:
        # Salvar localmente
        with open('grafico_trello_pizza.png', 'wb') as f:
            f.write(chart_buffer.getvalue())
        print("✅ Gráfico salvo: grafico_trello_pizza.png")
    else:
        print("❌ Erro ao gerar gráfico de pizza")
    
    print()


def main():
    """Função principal"""
    print("\n")
    print("╔════════════════════════════════════════════╗")
    print("║   🧪 TESTE DE GRÁFICOS ESTATÍSTICOS       ║")
    print("╚════════════════════════════════════════════╝")
    print("\n")
    
    # Verificar se matplotlib está instalado
    try:
        import matplotlib
        import numpy
        print("✅ matplotlib instalado")
        print("✅ numpy instalado\n")
    except ImportError as e:
        print("❌ Bibliotecas não instaladas!")
        print("Execute: pip install matplotlib numpy")
        print(f"Erro: {e}\n")
        return
    
    # Testar gráficos do GitHub
    try:
        test_github_charts()
    except Exception as e:
        print(f"❌ Erro ao testar GitHub: {e}\n")
    
    print("\n")
    
    # Testar gráficos do Trello
    try:
        test_trello_charts()
    except Exception as e:
        print(f"❌ Erro ao testar Trello: {e}\n")
    
    print("\n")
    print("=" * 50)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 50)
    print("\n📁 Gráficos gerados:")
    print("   • grafico_ranking_commits.png")
    print("   • grafico_evolucao_commits.png")
    print("   • grafico_trello_pizza.png")
    print("\n📂 Abra os arquivos PNG para ver os gráficos!")
    print("\n")


if __name__ == '__main__':
    main()

