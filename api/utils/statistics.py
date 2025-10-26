"""
Módulo de Estatísticas com Matplotlib
Gera análises, tabelas e gráficos para o bot PMO
"""

import json
import os
from io import BytesIO
import base64
from datetime import datetime, timedelta
from collections import defaultdict

def get_github_commits_stats(github_token, github_repo, limit=100):
    """
    Analisa estatísticas de commits do GitHub
    Retorna dados processados para visualização
    """
    import urllib.request
    
    try:
        # Buscar commits
        url = f'https://api.github.com/repos/{github_repo}/commits?per_page={limit}'
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PMO-Bot'
        }
        
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        commits = json.loads(response.read())
        
        if not commits:
            return None
        
        # Processar dados dos commits
        commit_data = []
        for commit in commits:
            author = commit['commit']['author']['name']
            date = commit['commit']['author']['date'][:10]
            message = commit['commit']['message'].split('\n')[0]
            
            commit_data.append({
                'author': author,
                'date': date,
                'message': message
            })
        
        # Contar commits por autor
        author_counts = {}
        for commit in commit_data:
            author = commit['author']
            author_counts[author] = author_counts.get(author, 0) + 1
        
        # Ordenar por número de commits
        sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Calcular estatísticas
        total_commits = len(commit_data)
        total_authors = len(author_counts)
        avg_commits_per_author = total_commits / total_authors if total_authors > 0 else 0
        
        # Preparar dados para retorno
        stats = {
            'total_commits': total_commits,
            'total_authors': total_authors,
            'avg_commits_per_author': round(avg_commits_per_author, 2),
            'commits_by_author': sorted_authors,
            'repository': github_repo
        }
        
        return stats
    
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return None


def generate_commits_report(stats):
    """
    Gera relatório textual de estatísticas de commits
    """
    if not stats:
        return "❌ Não foi possível gerar estatísticas."
    
    lines = []
    lines.append(f"📊 *Estatísticas de Commits - {stats['repository']}*\n")
    lines.append(f"📈 *Resumo Geral:*")
    lines.append(f"• Total de commits analisados: *{stats['total_commits']}*")
    lines.append(f"• Total de contribuidores: *{stats['total_authors']}*")
    lines.append(f"• Média de commits por pessoa: *{stats['avg_commits_per_author']}*\n")
    
    lines.append(f"👥 *Ranking de Contribuidores:*")
    
    for i, (author, count) in enumerate(stats['commits_by_author'][:10], 1):
        percentage = (count / stats['total_commits']) * 100
        
        # Verificar se está acima ou abaixo da média
        if count > stats['avg_commits_per_author']:
            status = "🔥 Acima da média"
        elif count == stats['avg_commits_per_author']:
            status = "📊 Na média"
        else:
            status = "📉 Abaixo da média"
        
        lines.append(f"{i}. *{author}*")
        lines.append(f"   • Commits: {count} ({percentage:.1f}%)")
        lines.append(f"   • Status: {status}")
    
    if len(stats['commits_by_author']) > 10:
        remaining = len(stats['commits_by_author']) - 10
        lines.append(f"\n_... e mais {remaining} contribuidores_")
    
    return '\n'.join(lines)


def get_trello_cards_stats(api_key, token, board_id):
    """
    Analisa estatísticas de cards do Trello
    """
    import urllib.request
    
    try:
        # Buscar cards
        cards_url = f'https://api.trello.com/1/boards/{board_id}/cards?key={api_key}&token={token}'
        req = urllib.request.Request(cards_url)
        response = urllib.request.urlopen(req)
        cards = json.loads(response.read())
        
        # Buscar listas
        lists_url = f'https://api.trello.com/1/boards/{board_id}/lists?key={api_key}&token={token}'
        req = urllib.request.Request(lists_url)
        response = urllib.request.urlopen(req)
        lists = json.loads(response.read())
        
        # Mapear lista ID para nome
        list_names = {lst['id']: lst['name'] for lst in lists}
        
        # Contar cards por lista
        cards_by_list = {}
        for card in cards:
            list_id = card['idList']
            list_name = list_names.get(list_id, 'Desconhecida')
            cards_by_list[list_name] = cards_by_list.get(list_name, 0) + 1
        
        # Estatísticas
        total_cards = len(cards)
        total_lists = len(lists)
        avg_cards_per_list = total_cards / total_lists if total_lists > 0 else 0
        
        stats = {
            'total_cards': total_cards,
            'total_lists': total_lists,
            'avg_cards_per_list': round(avg_cards_per_list, 2),
            'cards_by_list': sorted(cards_by_list.items(), key=lambda x: x[1], reverse=True)
        }
        
        return stats
    
    except Exception as e:
        print(f"Erro ao buscar estatísticas do Trello: {e}")
        return None


def generate_trello_report(stats):
    """
    Gera relatório textual de estatísticas do Trello
    """
    if not stats:
        return "❌ Não foi possível gerar estatísticas."
    
    lines = []
    lines.append(f"📊 *Estatísticas do Quadro Trello*\n")
    lines.append(f"📈 *Resumo Geral:*")
    lines.append(f"• Total de cards: *{stats['total_cards']}*")
    lines.append(f"• Total de listas: *{stats['total_lists']}*")
    lines.append(f"• Média de cards por lista: *{stats['avg_cards_per_list']}*\n")
    
    lines.append(f"📋 *Distribuição por Lista:*")
    
    for i, (list_name, count) in enumerate(stats['cards_by_list'], 1):
        percentage = (count / stats['total_cards']) * 100 if stats['total_cards'] > 0 else 0
        
        # Gerar barra de progresso visual
        bar_length = int(percentage / 10)
        bar = '█' * bar_length + '░' * (10 - bar_length)
        
        lines.append(f"{i}. *{list_name}*")
        lines.append(f"   • Cards: {count} ({percentage:.1f}%)")
        lines.append(f"   • {bar}")
    
    return '\n'.join(lines)


def get_activity_summary(github_token, github_repo, trello_key, trello_token, board_id):
    """
    Gera resumo de atividades combinando GitHub e Trello
    """
    try:
        # Buscar últimos commits (últimos 7 dias)
        import urllib.request
        from datetime import datetime, timedelta
        
        # GitHub
        github_commits = 0
        if github_token and github_repo:
            url = f'https://api.github.com/repos/{github_repo}/commits?per_page=100'
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req)
            commits = json.loads(response.read())
            
            # Contar commits dos últimos 7 dias
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            github_commits = sum(1 for c in commits if c['commit']['author']['date'] >= seven_days_ago)
        
        # Trello
        trello_cards = 0
        if trello_key and trello_token and board_id:
            cards_url = f'https://api.trello.com/1/boards/{board_id}/cards?key={trello_key}&token={trello_token}'
            req = urllib.request.Request(cards_url)
            response = urllib.request.urlopen(req)
            cards = json.loads(response.read())
            trello_cards = len(cards)
        
        summary = {
            'github_commits_7days': github_commits,
            'trello_total_cards': trello_cards,
            'period': '7 dias'
        }
        
        return summary
    
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
        return None


def generate_activity_report(summary):
    """
    Gera relatório de resumo de atividades
    """
    if not summary:
        return "❌ Não foi possível gerar resumo."
    
    lines = []
    lines.append(f"📊 *Resumo de Atividades (últimos {summary['period']})*\n")
    
    lines.append(f"🐙 *GitHub:*")
    lines.append(f"• Commits nos últimos 7 dias: *{summary['github_commits_7days']}*\n")
    
    lines.append(f"📋 *Trello:*")
    lines.append(f"• Cards ativos no quadro: *{summary['trello_total_cards']}*\n")
    
    # Análise rápida
    if summary['github_commits_7days'] > 20:
        lines.append(f"💪 *Análise:* Equipe muito ativa no desenvolvimento!")
    elif summary['github_commits_7days'] > 10:
        lines.append(f"👍 *Análise:* Boa frequência de commits.")
    elif summary['github_commits_7days'] > 0:
        lines.append(f"⚠️ *Análise:* Poucos commits recentes.")
    else:
        lines.append(f"❌ *Análise:* Nenhum commit nos últimos 7 dias.")
    
    return '\n'.join(lines)


def generate_commits_chart(stats):
    """
    Gera gráfico de barras de commits por autor
    Retorna BytesIO com a imagem PNG
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Backend sem interface gráfica
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Preparar dados (top 10 contribuidores)
        authors = [author for author, _ in stats['commits_by_author'][:10]]
        commits = [count for _, count in stats['commits_by_author'][:10]]
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Cores: verde para acima da média, vermelho para abaixo
        colors = ['#2ecc71' if c > stats['avg_commits_per_author'] else '#e74c3c' for c in commits]
        
        # Gráfico de barras
        bars = ax.bar(range(len(authors)), commits, color=colors, alpha=0.8)
        
        # Linha da média
        ax.axhline(y=stats['avg_commits_per_author'], color='#3498db', linestyle='--', 
                   linewidth=2, label=f'Média: {stats["avg_commits_per_author"]:.1f}')
        
        # Configurações
        ax.set_xlabel('Contribuidores', fontsize=12, fontweight='bold')
        ax.set_ylabel('Número de Commits', fontsize=12, fontweight='bold')
        ax.set_title(f'Ranking de Commits - {stats["repository"]}', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(range(len(authors)))
        ax.set_xticklabels(authors, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        # Adicionar valores nas barras
        for i, (bar, value) in enumerate(zip(bars, commits)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(value)}',
                   ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Salvar em BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
    
    except Exception as e:
        print(f"Erro ao gerar gráfico: {e}")
        return None


def generate_commits_timeline(github_token, github_repo, days=30):
    """
    Gera gráfico de linha com evolução de commits ao longo do tempo
    Retorna BytesIO com a imagem PNG e dados das estatísticas
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import urllib.request
        import numpy as np
        
        # Buscar commits
        url = f'https://api.github.com/repos/{github_repo}/commits?per_page=100'
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PMO-Bot'
        }
        
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)
        commits = json.loads(response.read())
        
        # Processar commits por data
        commits_by_date = defaultdict(int)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for commit in commits:
            commit_date = datetime.strptime(
                commit['commit']['author']['date'][:10], 
                '%Y-%m-%d'
            )
            
            if commit_date >= cutoff_date:
                date_str = commit_date.strftime('%Y-%m-%d')
                commits_by_date[date_str] += 1
        
        # Preencher datas sem commits
        all_dates = []
        current_date = cutoff_date
        while current_date <= datetime.now():
            date_str = current_date.strftime('%Y-%m-%d')
            all_dates.append(date_str)
            if date_str not in commits_by_date:
                commits_by_date[date_str] = 0
            current_date += timedelta(days=1)
        
        # Ordenar por data
        sorted_dates = sorted(all_dates)
        sorted_counts = [commits_by_date[date] for date in sorted_dates]
        
        # Criar gráfico
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Linha de commits
        ax.plot(range(len(sorted_dates)), sorted_counts, 
                marker='o', linewidth=2, markersize=4, 
                color='#3498db', label='Commits por dia')
        
        # Área preenchida
        ax.fill_between(range(len(sorted_dates)), sorted_counts, 
                        alpha=0.3, color='#3498db')
        
        # Linha de tendência (média móvel de 7 dias)
        if len(sorted_counts) >= 7:
            moving_avg = np.convolve(sorted_counts, np.ones(7)/7, mode='valid')
            ax.plot(range(3, len(sorted_dates)-3), moving_avg, 
                   color='#e74c3c', linewidth=2, linestyle='--', 
                   label='Tendência (média 7 dias)')
        
        # Configurações
        ax.set_xlabel('Data', fontsize=12, fontweight='bold')
        ax.set_ylabel('Número de Commits', fontsize=12, fontweight='bold')
        ax.set_title(f'Evolução de Commits - Últimos {days} dias - {github_repo}', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Configurar eixo X (mostrar apenas algumas datas)
        step = max(1, len(sorted_dates) // 10)
        ax.set_xticks(range(0, len(sorted_dates), step))
        ax.set_xticklabels([sorted_dates[i][-5:] for i in range(0, len(sorted_dates), step)], 
                          rotation=45, ha='right')
        
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        
        # Salvar em BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Calcular estatísticas
        total = sum(sorted_counts)
        avg = total / len(sorted_counts) if sorted_counts else 0
        max_commits = max(sorted_counts) if sorted_counts else 0
        
        stats_data = {
            'total_commits': total,
            'avg_per_day': round(avg, 2),
            'max_in_day': max_commits,
            'days_analyzed': days
        }
        
        return buf, stats_data
    
    except Exception as e:
        print(f"Erro ao gerar timeline: {e}")
        return None, None


def generate_trello_pie_chart(stats):
    """
    Gera gráfico de pizza com distribuição de cards por lista
    Retorna BytesIO com a imagem PNG
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Preparar dados
        labels = [name for name, _ in stats['cards_by_list']]
        sizes = [count for _, count in stats['cards_by_list']]
        
        # Cores
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', 
                  '#9b59b6', '#1abc9c', '#34495e', '#e67e22']
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Gráfico de pizza
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors[:len(labels)],
                                           startangle=90, 
                                           textprops={'fontsize': 11, 'fontweight': 'bold'})
        
        # Melhorar aparência dos textos
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'Distribuição de Cards por Lista\nTotal: {stats["total_cards"]} cards', 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Salvar em BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
    
    except Exception as e:
        print(f"Erro ao gerar gráfico de pizza: {e}")
        return None


def upload_chart_to_slack(image_buffer, filename, channel, slack_token, initial_comment=""):
    """
    Faz upload de uma imagem (gráfico) para o Slack usando files.getUploadURLExternal (novo método)
    """
    try:
        import urllib.request
        import urllib.parse
        
        print(f"[UPLOAD] Iniciando upload de {filename} para canal {channel}")
        
        # Resetar buffer para leitura
        image_buffer.seek(0)
        image_data = image_buffer.read()
        file_size = len(image_data)
        
        print(f"[UPLOAD] Tamanho da imagem: {file_size} bytes")
        
        # PASSO 1: Obter URL de upload
        print(f"[UPLOAD] Passo 1: Solicitando URL de upload...")
        
        get_url_data = {
            'filename': filename,
            'length': file_size
        }
        
        url_request_body = urllib.parse.urlencode(get_url_data).encode()
        
        url = 'https://slack.com/api/files.getUploadURLExternal'
        headers = {
            'Authorization': f'Bearer {slack_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        req = urllib.request.Request(url, data=url_request_body, headers=headers)
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"[UPLOAD] ❌ Erro ao obter URL: {error_body}")
            return False
        
        if not result.get('ok'):
            error = result.get('error', 'desconhecido')
            print(f"[UPLOAD] ❌ Erro ao obter URL de upload: {error}")
            return False
        
        upload_url = result.get('upload_url')
        file_id = result.get('file_id')
        
        print(f"[UPLOAD] ✅ URL de upload obtida")
        print(f"[UPLOAD] File ID: {file_id}")
        
        # PASSO 2: Upload do arquivo para a URL obtida
        print(f"[UPLOAD] Passo 2: Fazendo upload do arquivo...")
        
        req = urllib.request.Request(
            upload_url,
            data=image_data,
            headers={'Content-Type': 'image/png'},
            method='POST'
        )
        
        try:
            urllib.request.urlopen(req, timeout=30)
            print(f"[UPLOAD] ✅ Arquivo enviado com sucesso")
        except Exception as e:
            print(f"[UPLOAD] ❌ Erro ao fazer upload: {e}")
            return False
        
        # PASSO 3: Completar o upload e compartilhar no canal
        print(f"[UPLOAD] Passo 3: Compartilhando no canal...")
        
        complete_data = {
            'files': json.dumps([{'id': file_id, 'title': filename}]),
            'channel_id': channel
        }
        
        if initial_comment:
            complete_data['initial_comment'] = initial_comment
        
        complete_body = urllib.parse.urlencode(complete_data).encode()
        
        url = 'https://slack.com/api/files.completeUploadExternal'
        headers = {
            'Authorization': f'Bearer {slack_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        req = urllib.request.Request(url, data=complete_body, headers=headers)
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"[UPLOAD] ❌ Erro ao completar: {error_body}")
            return False
        
        print(f"[UPLOAD] Resposta final: {json.dumps(result, indent=2)}")
        
        if result.get('ok'):
            print(f"[UPLOAD] ✅ Upload completo e compartilhado!")
            return True
        else:
            error = result.get('error', 'desconhecido')
            print(f"[UPLOAD] ❌ Erro ao compartilhar: {error}")
            
            # Erros comuns com soluções
            if error == 'missing_scope':
                print(f"[UPLOAD] 🔑 SOLUÇÃO: Adicione 'files:write' e REINSTALE o app")
            elif error == 'invalid_auth':
                print(f"[UPLOAD] 🔐 SOLUÇÃO: Token inválido, atualize SLACK_BOT_TOKEN")
            elif error == 'channel_not_found':
                print(f"[UPLOAD] 📢 SOLUÇÃO: Canal não encontrado: {channel}")
            elif error == 'not_in_channel':
                print(f"[UPLOAD] 🚪 SOLUÇÃO: Bot não está no canal, use /invite")
            else:
                print(f"[UPLOAD] ℹ️ Erro: {error}")
                if 'needed' in result:
                    print(f"[UPLOAD] Permissões necessárias: {result['needed']}")
                if 'provided' in result:
                    print(f"[UPLOAD] Permissões fornecidas: {result['provided']}")
            
            return False
    
    except Exception as e:
        print(f"[UPLOAD] ❌ Exceção: {e}")
        import traceback
        traceback.print_exc()
        return False

