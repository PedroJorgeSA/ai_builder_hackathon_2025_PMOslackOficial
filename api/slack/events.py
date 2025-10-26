"""
Slack Events API Handler
Processa eventos do Slack via webhook
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import hmac
import hashlib
import time

# Cache global de eventos processados (evitar duplicatas)
processed_events = set()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Ler corpo da requisição
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            # Verificar assinatura do Slack
            if not self.verify_slack_signature(body):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'Invalid signature')
                return
            
            # Parse JSON
            data = json.loads(body)
            
            # Responder a challenge do Slack (primeira vez)
            if 'challenge' in data:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'challenge': data['challenge']}).encode())
                return
            
            # IMPORTANTE: Responder OK IMEDIATAMENTE ao Slack (antes de processar)
            # Isso evita que o Slack faça retry por timeout
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
            
            # Processar evento DEPOIS de responder
            if data.get('type') == 'event_callback':
                event = data.get('event', {})
                
                # Verificar se já processamos este evento (evitar duplicatas)
                event_id = data.get('event_id')
                event_ts = event.get('event_ts', event.get('ts'))
                
                # Criar chave única para o evento
                event_key = f"{event_id}_{event_ts}"
                
                if event_key in processed_events:
                    print(f"[DEDUP] Evento duplicado ignorado: {event_key}")
                    return
                
                # Marcar como processado
                processed_events.add(event_key)
                
                # Limpar cache antigo (manter apenas últimos 100 eventos)
                if len(processed_events) > 100:
                    processed_events.pop()
                
                # Processar mensagem
                if event.get('type') == 'app_mention':
                    # Ignorar mensagens do próprio bot
                    if event.get('bot_id'):
                        print(f"[DEDUP] Mensagem do próprio bot ignorada")
                        return
                    
                    response = self.process_mention(event)
                    self.send_slack_response(response)
            
        except Exception as e:
            print(f"[ERROR] Erro ao processar evento: {e}")
            import traceback
            traceback.print_exc()
    
    def verify_slack_signature(self, body):
        """Verifica assinatura do Slack"""
        slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET', '')
        
        if not slack_signing_secret:
            return True  # Em dev, aceitar sem verificação
        
        timestamp = self.headers.get('X-Slack-Request-Timestamp', '')
        slack_signature = self.headers.get('X-Slack-Signature', '')
        
        # Verificar timestamp (evitar replay attacks)
        if abs(time.time() - float(timestamp)) > 60 * 5:
            return False
        
        # Calcular assinatura
        sig_basestring = f'v0:{timestamp}:{body.decode()}'
        my_signature = 'v0=' + hmac.new(
            slack_signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(my_signature, slack_signature)
    
    def process_mention(self, event):
        """Processa menção ao bot com classificação de intent"""
        text = event.get('text', '')
        user = event.get('user', '')
        channel = event.get('channel', '')
        
        print(f"[PROCESS] ===== NOVA MENÇÃO =====")
        print(f"[PROCESS] Texto RAW do evento: '{text}'")
        
        # Remover menção do bot do texto
        if '>' in text:
            text = text.split('>', 1)[-1].strip()
            print(f"[PROCESS] Texto após remover menção: '{text}'")
        
        # Importar classificador de intent
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        try:
            from utils.intent_classifier import classify_with_openai
            
            # Classificar intent usando IA
            classification = classify_with_openai(text)
            intent = classification.get('intent')
            params = classification.get('params', {})
            confidence = classification.get('confidence', 0)
            
            # Log para debug (aparece nos logs da Vercel)
            print(f"Intent detectado: {intent} (confiança: {confidence})")
            print(f"Parâmetros: {params}")
            
            # Rotear para handler apropriado baseado no intent
            if intent == 'github_commits':
                return self.handle_github_commits(channel, user, text, params)
            
            elif intent == 'trello_create_card':
                card_name = params.get('card_name')
                if card_name:
                    return self.handle_create_card(channel, user, f"criar card {card_name}")
                else:
                    return {
                        'channel': channel,
                        'text': f'<@{user}> Qual é o nome do card que você quer criar?'
                    }
            
            elif intent == 'trello_list_cards':
                return self.handle_list_cards(channel, user)
            
            elif intent == 'trello_move_card':
                card_name = params.get('card_name')
                target_list = params.get('target_list')
                if card_name and target_list:
                    return self.handle_move_card_to_list(channel, user, card_name, target_list)
                else:
                    return {
                        'channel': channel,
                        'text': f'<@{user}> ❌ Formato: `mover card Nome do Card para Nome da Lista`'
                    }
            
            elif intent == 'trello_delete_card':
                card_name = params.get('card_name')
                if card_name:
                    return self.handle_delete_card(channel, user, card_name)
                else:
                    return {
                        'channel': channel,
                        'text': f'<@{user}> Qual card você quer deletar?'
                    }
            
            elif intent == 'trello_list_lists':
                return self.handle_list_lists(channel, user)
            
            elif intent == 'trello_update_card':
                card_name = params.get('card_name')
                return {
                    'channel': channel,
                    'text': f'<@{user}> 🔄 Atualização de cards em desenvolvimento.\nPor enquanto, use: mover, deletar ou criar.'
                }
            
            elif intent == 'trello_update_status':
                card_name = params.get('card_name')
                status = params.get('status')
                return {
                    'channel': channel,
                    'text': f'<@{user}> 🔄 Atualizando status do card "{card_name}" para "{status}"...\n_Funcionalidade em desenvolvimento_'
                }
            
            elif intent == 'stats_commits':
                return self.handle_stats_commits(channel, user)
            
            elif intent == 'stats_trello':
                return self.handle_stats_trello(channel, user)
            
            elif intent == 'stats_activity':
                return self.handle_stats_activity(channel, user)
            
            elif intent == 'stats_general':
                return self.handle_stats_general(channel, user)
            
            elif intent == 'help':
                return self.show_help(channel, user)
            
            elif intent == 'greeting':
                return {
                    'channel': channel,
                    'text': f'<@{user}> Olá! 👋 Como posso ajudar? Digite "ajuda" para ver os comandos.'
                }
            
            else:
                # Intent desconhecido - tentar comandos diretos (fallback)
                return self.process_direct_commands(channel, user, text)
        
        except Exception as e:
            print(f"Erro no classificador: {e}")
            # Fallback para comandos diretos em caso de erro
            return self.process_direct_commands(channel, user, text)
    
    def process_direct_commands(self, channel, user, text):
        """Processa comandos diretos (fallback)"""
        text_lower = text.lower()
        
        # Comandos do GitHub
        if 'commit' in text_lower or 'commits' in text_lower:
            return self.handle_github_commits(channel, user, text_lower, {})
        
        # Comandos do Trello - Criar
        elif 'criar card' in text_lower or 'criar um card' in text_lower:
            return self.handle_create_card(channel, user, text)
        
        # Comandos do Trello - Listar
        elif 'listar' in text_lower or 'mostrar' in text_lower or 'ver cards' in text_lower:
            return self.handle_list_cards(channel, user)
        
        # Comandos do Trello - Mover
        elif 'mover' in text_lower or 'mover card' in text_lower:
            return self.handle_move_card(channel, user, text)
        
        # Ajuda
        elif 'ajuda' in text_lower or 'help' in text_lower or 'comandos' in text_lower:
            return self.show_help(channel, user)
        
        # Resposta padrão
        else:
            return {
                'channel': channel,
                'text': f'<@{user}> Olá! Digite "ajuda" para ver os comandos disponíveis.'
            }
    
    def handle_github_commits(self, channel, user, text, params=None):
        """Lista commits do GitHub"""
        import urllib.request
        import re
        
        github_token = os.environ.get('GITHUB_TOKEN')
        github_repo = os.environ.get('GITHUB_REPO')
        
        # Verificar se GITHUB_REPO está configurado
        if not github_repo or github_repo == 'owner/repo':
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Variável GITHUB_REPO não configurada.\n\n*Como configurar:*\n1. Vá em Settings → Environment Variables na Vercel\n2. Adicione `GITHUB_REPO` com valor `usuario/repositorio`\n3. Exemplo: `pedro-soares/meu-projeto`\n4. Faça Redeploy'
            }
        
        # Extrair número de commits (usar params do intent classifier ou regex)
        if params and 'limit' in params:
            limit = params['limit']
        else:
            match = re.search(r'(\d+)', text)
            limit = int(match.group(1)) if match else 5
        
        try:
            url = f'https://api.github.com/repos/{github_repo}/commits?per_page={limit}'
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'PMO-Bot'
            }
            
            # Adicionar token se disponível (necessário para repos privados)
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req)
            commits = json.loads(response.read())
            
            # Formatar resposta
            if commits:
                lines = [f'📊 *Últimos {len(commits)} commits de `{github_repo}`:*\n']
                for i, commit in enumerate(commits, 1):
                    msg = commit['commit']['message'].split('\n')[0]
                    author = commit['commit']['author']['name']
                    sha = commit['sha'][:7]
                    date = commit['commit']['author']['date'][:10]
                    lines.append(f'{i}. `{sha}` - {msg}\n   _{author} em {date}_')
                
                return {
                    'channel': channel,
                    'text': '\n'.join(lines)
                }
            else:
                return {
                    'channel': channel,
                    'text': f'<@{user}> Nenhum commit encontrado no repositório `{github_repo}`.'
                }
        
        except urllib.error.HTTPError as e:
            error_msg = f'<@{user}> ❌ Erro ao buscar commits: {e.code} {e.reason}\n\n'
            
            if e.code == 404:
                error_msg += f'*Repositório não encontrado:* `{github_repo}`\n\n'
                error_msg += '*Verifique:*\n'
                error_msg += '1. O nome está correto? Formato: `usuario/repositorio`\n'
                error_msg += '2. O repositório existe?\n'
                error_msg += f'3. Acesse: https://github.com/{github_repo}'
            elif e.code == 401:
                error_msg += '*Repositório privado requer token*\n'
                error_msg += 'Configure GITHUB_TOKEN nas variáveis de ambiente'
            else:
                error_msg += f'Código de erro: {e.code}'
            
            return {
                'channel': channel,
                'text': error_msg
            }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro inesperado: {str(e)}'
            }
    
    def handle_create_card(self, channel, user, text):
        """Cria card no Trello"""
        import urllib.request
        import re
        
        # Extrair nome do card
        match = re.search(r'criar (?:card |um card )?(.+)', text, re.IGNORECASE)
        if not match:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Formato: `criar card Nome do Card`'
            }
        
        card_name = match.group(1).strip()
        
        api_key = os.environ.get('TRELLO_API_KEY')
        token = os.environ.get('TRELLO_TOKEN')
        board_id = os.environ.get('TRELLO_BOARD_ID')
        
        if not all([api_key, token, board_id]):
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Credenciais do Trello não configuradas.'
            }
        
        try:
            # Buscar primeira lista do quadro
            lists_url = f'https://api.trello.com/1/boards/{board_id}/lists?key={api_key}&token={token}'
            req = urllib.request.Request(lists_url)
            response = urllib.request.urlopen(req)
            lists = json.loads(response.read())
            
            if not lists:
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Nenhuma lista encontrada no quadro.'
                }
            
            list_id = lists[0]['id']
            list_name = lists[0]['name']
            
            # Criar card
            create_url = f'https://api.trello.com/1/cards'
            params = {
                'key': api_key,
                'token': token,
                'name': card_name,
                'idList': list_id
            }
            
            data = '&'.join([f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items()])
            req = urllib.request.Request(create_url, data=data.encode(), method='POST')
            response = urllib.request.urlopen(req)
            card = json.loads(response.read())
            
            return {
                'channel': channel,
                'text': f'<@{user}> ✅ Card *"{card_name}"* criado na lista *{list_name}*!\n🔗 {card["shortUrl"]}'
            }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao criar card: {str(e)}'
            }
    
    def handle_list_cards(self, channel, user):
        """Lista cards do Trello"""
        import urllib.request
        
        api_key = os.environ.get('TRELLO_API_KEY')
        token = os.environ.get('TRELLO_TOKEN')
        board_id = os.environ.get('TRELLO_BOARD_ID')
        
        if not all([api_key, token, board_id]):
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Credenciais do Trello não configuradas.'
            }
        
        try:
            url = f'https://api.trello.com/1/boards/{board_id}/cards?key={api_key}&token={token}'
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)
            cards = json.loads(response.read())
            
            if cards:
                lines = [f'📋 *{len(cards)} cards encontrados:*\n']
                for i, card in enumerate(cards[:10], 1):  # Limitar a 10
                    lines.append(f'{i}. {card["name"]}')
                
                if len(cards) > 10:
                    lines.append(f'\n_... e mais {len(cards) - 10} cards_')
                
                return {
                    'channel': channel,
                    'text': '\n'.join(lines)
                }
            else:
                return {
                    'channel': channel,
                    'text': f'<@{user}> Nenhum card encontrado.'
                }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao listar cards: {str(e)}'
            }
    
    def handle_move_card_to_list(self, channel, user, card_name, target_list_name):
        """Move card para uma lista específica"""
        import urllib.request
        
        api_key = os.environ.get('TRELLO_API_KEY')
        token = os.environ.get('TRELLO_TOKEN')
        board_id = os.environ.get('TRELLO_BOARD_ID')
        
        if not all([api_key, token, board_id]):
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Credenciais do Trello não configuradas.'
            }
        
        try:
            # 1. Buscar o card pelo nome
            cards_url = f'https://api.trello.com/1/boards/{board_id}/cards?key={api_key}&token={token}'
            req = urllib.request.Request(cards_url)
            response = urllib.request.urlopen(req)
            cards = json.loads(response.read())
            
            # Encontrar card que contém o nome
            matching_cards = [c for c in cards if card_name.lower() in c['name'].lower()]
            
            if not matching_cards:
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Card "{card_name}" não encontrado.'
                }
            
            card = matching_cards[0]
            card_id = card['id']
            
            # 2. Buscar listas do quadro
            lists_url = f'https://api.trello.com/1/boards/{board_id}/lists?key={api_key}&token={token}'
            req = urllib.request.Request(lists_url)
            response = urllib.request.urlopen(req)
            lists = json.loads(response.read())
            
            # Encontrar lista destino
            matching_lists = [l for l in lists if target_list_name.lower() in l['name'].lower()]
            
            if not matching_lists:
                available_lists = ', '.join([f'"{l["name"]}"' for l in lists])
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Lista "{target_list_name}" não encontrada.\n\n*Listas disponíveis:* {available_lists}'
                }
            
            target_list = matching_lists[0]
            target_list_id = target_list['id']
            
            # 3. Mover o card
            move_url = f'https://api.trello.com/1/cards/{card_id}?key={api_key}&token={token}&idList={target_list_id}'
            req = urllib.request.Request(move_url, method='PUT')
            response = urllib.request.urlopen(req)
            
            return {
                'channel': channel,
                'text': f'<@{user}> ✅ Card *"{card["name"]}"* movido para *{target_list["name"]}*!'
            }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao mover card: {str(e)}'
            }
    
    def handle_delete_card(self, channel, user, card_name):
        """Deleta um card do Trello"""
        import urllib.request
        
        api_key = os.environ.get('TRELLO_API_KEY')
        token = os.environ.get('TRELLO_TOKEN')
        board_id = os.environ.get('TRELLO_BOARD_ID')
        
        if not all([api_key, token, board_id]):
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Credenciais do Trello não configuradas.'
            }
        
        try:
            # 1. Buscar o card pelo nome
            cards_url = f'https://api.trello.com/1/boards/{board_id}/cards?key={api_key}&token={token}'
            req = urllib.request.Request(cards_url)
            response = urllib.request.urlopen(req)
            cards = json.loads(response.read())
            
            # Encontrar card que contém o nome
            matching_cards = [c for c in cards if card_name.lower() in c['name'].lower()]
            
            if not matching_cards:
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Card "{card_name}" não encontrado.'
                }
            
            if len(matching_cards) > 1:
                card_list = '\n'.join([f'• {c["name"]}' for c in matching_cards[:5]])
                return {
                    'channel': channel,
                    'text': f'<@{user}> ⚠️ Encontrei {len(matching_cards)} cards com esse nome:\n\n{card_list}\n\nSeja mais específico!'
                }
            
            card = matching_cards[0]
            card_id = card['id']
            card_full_name = card['name']
            
            # 2. Deletar o card
            delete_url = f'https://api.trello.com/1/cards/{card_id}?key={api_key}&token={token}'
            req = urllib.request.Request(delete_url, method='DELETE')
            response = urllib.request.urlopen(req)
            
            return {
                'channel': channel,
                'text': f'<@{user}> ✅ Card *"{card_full_name}"* deletado com sucesso!'
            }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao deletar card: {str(e)}'
            }
    
    def handle_list_lists(self, channel, user):
        """Lista todas as listas (colunas) do quadro Trello"""
        import urllib.request
        
        api_key = os.environ.get('TRELLO_API_KEY')
        token = os.environ.get('TRELLO_TOKEN')
        board_id = os.environ.get('TRELLO_BOARD_ID')
        
        if not all([api_key, token, board_id]):
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Credenciais do Trello não configuradas.'
            }
        
        try:
            url = f'https://api.trello.com/1/boards/{board_id}/lists?key={api_key}&token={token}'
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req)
            lists = json.loads(response.read())
            
            if lists:
                lines = [f'📊 *{len(lists)} listas no quadro:*\n']
                for i, lst in enumerate(lists, 1):
                    # Buscar quantidade de cards em cada lista
                    cards_url = f'https://api.trello.com/1/lists/{lst["id"]}/cards?key={api_key}&token={token}'
                    req = urllib.request.Request(cards_url)
                    response = urllib.request.urlopen(req)
                    cards = json.loads(response.read())
                    
                    lines.append(f'{i}. *{lst["name"]}* ({len(cards)} cards)')
                
                return {
                    'channel': channel,
                    'text': '\n'.join(lines)
                }
            else:
                return {
                    'channel': channel,
                    'text': f'<@{user}> Nenhuma lista encontrada no quadro.'
                }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao listar listas: {str(e)}'
            }
    
    def handle_stats_commits(self, channel, user):
        """Gera estatísticas de commits do GitHub com gráficos"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        try:
            from utils.statistics import (
                get_github_commits_stats, 
                generate_commits_report,
                generate_commits_chart,
                generate_commits_timeline,
                upload_chart_to_slack
            )
            
            github_token = os.environ.get('GITHUB_TOKEN')
            github_repo = os.environ.get('GITHUB_REPO')
            slack_token = os.environ.get('SLACK_BOT_TOKEN')
            
            if not github_repo:
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ GITHUB_REPO não configurado.'
                }
            
            # Buscar estatísticas
            stats = get_github_commits_stats(github_token, github_repo, limit=100)
            
            if not stats:
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Não foi possível gerar estatísticas.'
                }
            
            # Gerar relatório textual
            report = generate_commits_report(stats)
            
            # Enviar relatório textual primeiro
            self.send_slack_response({
                'channel': channel,
                'text': f'{report}\n\n📊 _Gerando gráficos..._'
            })
            
            # Gerar e enviar gráfico de barras (ranking)
            success_count = 0
            errors = []
            
            chart_buffer = generate_commits_chart(stats)
            if chart_buffer and slack_token:
                result = upload_chart_to_slack(
                    chart_buffer, 
                    f'commits_ranking_{github_repo.replace("/", "_")}.png',
                    channel,
                    slack_token,
                    f'📊 Ranking de Commits - {github_repo}'
                )
                if result:
                    success_count += 1
                else:
                    errors.append("Erro ao enviar gráfico de ranking")
            elif not slack_token:
                errors.append("SLACK_BOT_TOKEN não configurado")
            
            # Gerar e enviar gráfico de linha (evolução temporal)
            timeline_buffer, timeline_stats = generate_commits_timeline(github_token, github_repo, days=30)
            if timeline_buffer and slack_token:
                comment = f'📈 Evolução de Commits (últimos 30 dias)\n'
                comment += f'• Total: {timeline_stats["total_commits"]} commits\n'
                comment += f'• Média/dia: {timeline_stats["avg_per_day"]}\n'
                comment += f'• Máximo em 1 dia: {timeline_stats["max_in_day"]}'
                
                result = upload_chart_to_slack(
                    timeline_buffer,
                    f'commits_timeline_{github_repo.replace("/", "_")}.png',
                    channel,
                    slack_token,
                    comment
                )
                if result:
                    success_count += 1
                else:
                    errors.append("Erro ao enviar gráfico de evolução")
            
            # Mensagem final
            if success_count == 2:
                return {
                    'channel': channel,
                    'text': '✅ Gráficos enviados com sucesso!'
                }
            elif success_count > 0:
                return {
                    'channel': channel,
                    'text': f'⚠️ {success_count} gráfico(s) enviado(s), mas houve problemas:\n• ' + '\n• '.join(errors)
                }
            else:
                error_msg = '\n• '.join(errors) if errors else 'Verifique os logs (vercel logs)'
                return {
                    'channel': channel,
                    'text': f'❌ Não foi possível enviar os gráficos.\n• {error_msg}\n\n*Verifique:*\n1. Bot tem permissão `files:write`?\n2. SLACK_BOT_TOKEN está configurado?'
                }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao gerar estatísticas: {str(e)}'
            }
    
    def handle_stats_trello(self, channel, user):
        """Gera estatísticas do Trello com gráficos"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        try:
            from utils.statistics import (
                get_trello_cards_stats, 
                generate_trello_report,
                generate_trello_pie_chart,
                upload_chart_to_slack
            )
            
            api_key = os.environ.get('TRELLO_API_KEY')
            token = os.environ.get('TRELLO_TOKEN')
            board_id = os.environ.get('TRELLO_BOARD_ID')
            slack_token = os.environ.get('SLACK_BOT_TOKEN')
            
            if not all([api_key, token, board_id]):
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Credenciais do Trello não configuradas.'
                }
            
            # Buscar estatísticas
            stats = get_trello_cards_stats(api_key, token, board_id)
            
            if not stats:
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Não foi possível gerar estatísticas.'
                }
            
            # Gerar relatório textual
            report = generate_trello_report(stats)
            
            # Enviar relatório
            self.send_slack_response({
                'channel': channel,
                'text': f'{report}\n\n📊 _Gerando gráfico..._'
            })
            
            # Gerar e enviar gráfico de pizza
            chart_buffer = generate_trello_pie_chart(stats)
            if chart_buffer and slack_token:
                result = upload_chart_to_slack(
                    chart_buffer,
                    'trello_distribution.png',
                    channel,
                    slack_token,
                    f'📊 Distribuição de Cards no Trello'
                )
                
                if result:
                    return {
                        'channel': channel,
                        'text': '✅ Gráfico enviado com sucesso!'
                    }
                else:
                    return {
                        'channel': channel,
                        'text': '❌ Erro ao enviar o gráfico.\n\n*Verifique:*\n1. Bot tem permissão `files:write`?\n2. SLACK_BOT_TOKEN está configurado?'
                    }
            elif not slack_token:
                return {
                    'channel': channel,
                    'text': '❌ SLACK_BOT_TOKEN não configurado.'
                }
            else:
                return {
                    'channel': channel,
                    'text': '❌ Erro ao gerar o gráfico.'
                }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao gerar estatísticas: {str(e)}'
            }
    
    def handle_stats_activity(self, channel, user):
        """Gera resumo de atividades"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        try:
            from utils.statistics import get_activity_summary, generate_activity_report
            
            github_token = os.environ.get('GITHUB_TOKEN')
            github_repo = os.environ.get('GITHUB_REPO')
            trello_key = os.environ.get('TRELLO_API_KEY')
            trello_token = os.environ.get('TRELLO_TOKEN')
            board_id = os.environ.get('TRELLO_BOARD_ID')
            
            # Buscar resumo
            summary = get_activity_summary(github_token, github_repo, trello_key, trello_token, board_id)
            
            if not summary:
                return {
                    'channel': channel,
                    'text': f'<@{user}> ❌ Não foi possível gerar resumo.'
                }
            
            # Gerar relatório
            report = generate_activity_report(summary)
            
            return {
                'channel': channel,
                'text': report
            }
        
        except Exception as e:
            return {
                'channel': channel,
                'text': f'<@{user}> ❌ Erro ao gerar resumo: {str(e)}'
            }
    
    def handle_stats_general(self, channel, user):
        """Mostra menu de estatísticas disponíveis"""
        help_text = f'''<@{user}> 📊 *Estatísticas Disponíveis:*

Digite um dos comandos abaixo:

• `estatística de commits` - Análise de commits por pessoa
• `estatística do trello` - Distribuição de cards por lista
• `resumo de atividades` - Atividades dos últimos 7 dias

_Escolha uma opção acima!_'''
        
        return {
            'channel': channel,
            'text': help_text
        }
    
    def show_help(self, channel, user):
        """Mostra ajuda com comandos disponíveis"""
        help_text = f'''<@{user}> 🤖 *Comandos Disponíveis:*

*GitHub:*
• `me diga os últimos 5 commits` - Lista commits
• `mostrar últimos 10 commits` - Lista commits

*Trello:*
• `criar card Nome do Card` - Cria um card
• `listar cards` - Lista todos os cards
• `mostrar cards` - Lista todos os cards
• `listar listas` - Lista todas as listas/colunas
• `mover card X para Lista Y` - Move card entre listas
• `deletar card Nome do Card` - Deleta um card

*Estatísticas:*
• `estatística de commits` - Análise de commits por pessoa
• `estatística do trello` - Distribuição de cards
• `resumo de atividades` - Resumo dos últimos 7 dias

*Ajuda:*
• `ajuda` ou `help` - Mostra esta mensagem

_Digite qualquer comando acima para começar!_'''
        
        return {
            'channel': channel,
            'text': help_text
        }
    
    def send_slack_response(self, response):
        """Envia resposta para o Slack"""
        import urllib.request
        
        slack_token = os.environ.get('SLACK_BOT_TOKEN')
        
        if not slack_token:
            return
        
        url = 'https://slack.com/api/chat.postMessage'
        headers = {
            'Authorization': f'Bearer {slack_token}',
            'Content-Type': 'application/json'
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(response).encode(),
            headers=headers
        )
        
        try:
            urllib.request.urlopen(req)
        except:
            pass

