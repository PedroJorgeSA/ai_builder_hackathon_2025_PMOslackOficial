"""
Agente LangGraph para Slack usando MCP Customizado
"""

import os
import json
import http.client
import re
from datetime import datetime
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
import operator
from urllib.parse import quote
from intent_classifier_agent import IntentClassifierAgent

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
TRELLO_API_KEY = os.getenv('TRELLO_API_KEY')
TRELLO_TOKEN = os.getenv('TRELLO_TOKEN')
TRELLO_BOARD_ID = os.getenv('TRELLO_BOARD_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_OWNER = os.getenv('GITHUB_OWNER')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# Estado do grafo
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    question: str
    trello_data: dict
    github_data: dict
    context: dict
    response: str

class SlackLangGraphAgent:
    """Agente LangGraph para Slack com MCP"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=OPENAI_API_KEY)
        self.slack_token = SLACK_BOT_TOKEN
        self.trello_key = TRELLO_API_KEY
        self.trello_token = TRELLO_TOKEN
        self.github_token = GITHUB_TOKEN
        self.intent_classifier = IntentClassifierAgent()  # Agent classificador
        
    def get_trello_data(self):
        """Obtém dados do Trello via MCP"""
        try:
            conn = http.client.HTTPSConnection("api.trello.com")
            
            # Obter informações do quadro
            url = f"/1/boards/{TRELLO_BOARD_ID}?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            board = json.loads(response.read().decode())
            
            # Obter lists
            url = f"/1/boards/{TRELLO_BOARD_ID}/lists?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            lists = json.loads(response.read().decode())
            
            # Obter cards
            url = f"/1/boards/{TRELLO_BOARD_ID}/cards?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            cards = json.loads(response.read().decode())
            
            conn.close()
            
            # Organizar dados
            trello_data = {
                'board_name': board['name'],
                'lists': {}
            }
            
            for lst in lists:
                list_cards = [card for card in cards if card['idList'] == lst['id']]
                trello_data['lists'][lst['name']] = {
                    'total_cards': len(list_cards),
                    'cards': [{'name': card['name'], 'id': card['id']} for card in list_cards]
                }
            
            return trello_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_github_data(self):
        """Obtém dados do GitHub via MCP"""
        try:
            conn = http.client.HTTPSConnection("api.github.com")
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'LangGraph-Agent'
            }
            
            # Informações do repositório
            conn.request("GET", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}", headers=headers)
            response = conn.getresponse()
            repo = json.loads(response.read().decode())
            
            # Últimos commits
            conn.request("GET", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page=5", headers=headers)
            response = conn.getresponse()
            commits = json.loads(response.read().decode())
            
            # Issues abertas
            conn.request("GET", f"/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues?state=open", headers=headers)
            response = conn.getresponse()
            issues = json.loads(response.read().decode())
            
            conn.close()
            
            github_data = {
                'repository': repo['full_name'],
                'description': repo.get('description', 'Sem descrição'),
                'language': repo.get('language', 'N/A'),
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'open_issues': repo['open_issues_count'],
                'recent_commits': [
                    {
                        'message': c['commit']['message'].split('\n')[0],
                        'author': c['commit']['author']['name'],
                        'date': c['commit']['author']['date']
                    }
                    for c in commits[:5]
                ],
                'open_issues_list': [
                    {
                        'number': issue['number'],
                        'title': issue['title'],
                        'state': issue['state']
                    }
                    for issue in issues[:5]
                ]
            }
            
            return github_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def update_trello_card(self, card_name, new_name=None, new_description=None):
        """Atualiza um card no Trello"""
        try:
            # Obter cards
            conn = http.client.HTTPSConnection("api.trello.com")
            url = f"/1/boards/{TRELLO_BOARD_ID}/cards?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            cards = json.loads(response.read().decode())
            
            # Encontrar o card
            card_id = None
            for card in cards:
                if card['name'].lower() == card_name.lower():
                    card_id = card['id']
                    break
            
            if not card_id:
                return f"Card '{card_name}' não encontrado"
            
            # Preparar parâmetros de atualização
            params = {
                'key': self.trello_key,
                'token': self.trello_token
            }
            
            if new_name:
                params['name'] = new_name
            if new_description:
                params['desc'] = new_description
            
            # Atualizar o card (com URL encoding)
            url = f"/1/cards/{card_id}"
            query_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
            conn.request("PUT", f"{url}?{query_string}")
            response = conn.getresponse()
            card = json.loads(response.read().decode())
            
            conn.close()
            
            updates = []
            if new_name:
                updates.append(f"nome para '{new_name}'")
            if new_description:
                updates.append("descrição")
            
            return f"Card '{card_name}' atualizado: {', '.join(updates)}"
            
        except Exception as e:
            return f"Erro ao atualizar card: {str(e)}"
    
    def delete_trello_card(self, card_name):
        """Deleta um card no Trello"""
        try:
            # Obter cards
            conn = http.client.HTTPSConnection("api.trello.com")
            url = f"/1/boards/{TRELLO_BOARD_ID}/cards?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            cards = json.loads(response.read().decode())
            
            # Encontrar o card
            card_id = None
            for card in cards:
                if card['name'].lower() == card_name.lower():
                    card_id = card['id']
                    break
            
            if not card_id:
                return f"❌ Card '{card_name}' não encontrado"
            
            # Deletar o card usando a API do Trello (método de chamada MCP)
            url = f"/1/cards/{card_id}?key={self.trello_key}&token={self.trello_token}"
            conn.request("DELETE", url)
            response = conn.getresponse()
            result = response.read().decode()
            
            conn.close()
            
            if response.status == 200:
                return f"✅ Card '{card_name}' deletado com sucesso!"
            else:
                return f"❌ Erro ao deletar card: {result}"
            
        except Exception as e:
            return f"❌ Erro ao deletar card: {str(e)}"
    
    def move_trello_card(self, card_name, target_list_name):
        """Move um card para outra lista no Trello"""
        try:
            # Obter cards
            conn = http.client.HTTPSConnection("api.trello.com")
            url = f"/1/boards/{TRELLO_BOARD_ID}/cards?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            cards = json.loads(response.read().decode())
            
            # Encontrar o card
            card_id = None
            for card in cards:
                if card['name'].lower() == card_name.lower():
                    card_id = card['id']
                    break
            
            if not card_id:
                return f"❌ Card '{card_name}' não encontrado"
            
            # Obter lists
            url = f"/1/boards/{TRELLO_BOARD_ID}/lists?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            lists = json.loads(response.read().decode())
            
            # Encontrar a lista de destino
            target_list_id = None
            for lst in lists:
                if lst['name'].lower() == target_list_name.lower():
                    target_list_id = lst['id']
                    break
            
            if not target_list_id:
                return f"❌ Lista '{target_list_name}' não encontrada"
            
            # Mover o card
            url = f"/1/cards/{card_id}?key={self.trello_key}&token={self.trello_token}"
            params = f"idList={target_list_id}"
            conn.request("PUT", f"{url}&{params}")
            response = conn.getresponse()
            result = json.loads(response.read().decode())
            
            conn.close()
            
            if response.status == 200:
                return f"✅ Card '{card_name}' movido para '{target_list_name}' com sucesso!"
            else:
                return f"❌ Erro ao mover card: {result}"
            
        except Exception as e:
            return f"❌ Erro ao mover card: {str(e)}"
    
    def create_trello_card(self, card_name, target_list_name=None):
        """Cria um card no Trello"""
        try:
            # Obter lists
            conn = http.client.HTTPSConnection("api.trello.com")
            url = f"/1/boards/{TRELLO_BOARD_ID}/lists?key={self.trello_key}&token={self.trello_token}"
            conn.request("GET", url)
            response = conn.getresponse()
            lists = json.loads(response.read().decode())
            
            # Encontrar a lista de destino
            target_list_id = None
            if target_list_name:
                for lst in lists:
                    if lst['name'].lower() == target_list_name.lower():
                        target_list_id = lst['id']
                        break
                
                if not target_list_id:
                    return f"❌ Lista '{target_list_name}' não encontrada"
            else:
                # Se não especificou lista, usa a primeira (geralmente Backlog)
                target_list_id = lists[0]['id']
                target_list_name = lists[0]['name']
            
            # Criar o card (com URL encoding)
            encoded_name = quote(card_name)
            url = f"/1/cards?key={self.trello_key}&token={self.trello_token}&name={encoded_name}&idList={target_list_id}"
            conn.request("POST", url)
            response = conn.getresponse()
            result = json.loads(response.read().decode())
            
            conn.close()
            
            if response.status == 200:
                return f"✅ Card '{card_name}' criado na lista '{target_list_name}' com sucesso!"
            else:
                return f"❌ Erro ao criar card: {result}"
            
        except Exception as e:
            return f"❌ Erro ao criar card: {str(e)}"
    
    # Nós do grafo
    def collect_context(self, state: AgentState) -> AgentState:
        """Coleta contexto dos MCPs"""
        print(f"{datetime.now().strftime('%H:%M:%S')} - Coletando contexto dos MCPs...")
        
        trello_data = self.get_trello_data()
        github_data = self.get_github_data()
        
        state["trello_data"] = trello_data
        state["github_data"] = github_data
        
        context = {
            'trello': trello_data,
            'github': github_data,
            'timestamp': datetime.now().isoformat()
        }
        
        state["context"] = context
        
        return state
    
    def generate_response(self, state: AgentState) -> AgentState:
        """Gera resposta usando LLM com contexto"""
        print(f"{datetime.now().strftime('%H:%M:%S')} - Gerando resposta...")
        
        question = state["question"]
        context = state["context"]
        
        # Criar prompt com contexto
        system_prompt = f"""Você é um assistente de PMO (Project Management Office) especializado em Trello e GitHub.
Você recebe dados atualizados em tempo real dos MCPs e deve responder de forma clara e objetiva.

Contexto atual dos MCPs:
{json.dumps(context, indent=2, ensure_ascii=False)}
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        # Gerar resposta
        response = self.llm.invoke(messages)
        state["response"] = response.content
        
        print(f"{datetime.now().strftime('%H:%M:%S')} - Resposta gerada")
        
        return state
    
    def build_graph(self) -> StateGraph:
        """Constrói o grafo LangGraph"""
        workflow = StateGraph(AgentState)
        
        # Adicionar nós
        workflow.add_node("collect_context", self.collect_context)
        workflow.add_node("generate_response", self.generate_response)
        
        # Definir fluxo
        workflow.set_entry_point("collect_context")
        workflow.add_edge("collect_context", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def execute_classified_action(self, action: dict) -> str:
        """Executa uma ação classificada pelo Intent Classifier"""
        mcp = action.get("mcp")
        action_name = action.get("action")
        parameters = action.get("parameters", {})
        
        print(f"  Executando: [{mcp.upper()}] {action_name}")
        
        try:
            # Ações do Trello
            if mcp == "trello":
                if action_name == "create_card":
                    return self.create_trello_card(
                        parameters.get("card_name"),
                        parameters.get("target_list")
                    )
                elif action_name == "move_card":
                    return self.move_trello_card(
                        parameters.get("card_name"),
                        parameters.get("target_list")
                    )
                elif action_name == "update_card":
                    return self.update_trello_card(
                        parameters.get("card_name"),
                        parameters.get("new_name"),
                        parameters.get("new_description")
                    )
                elif action_name == "delete_card":
                    return self.delete_trello_card(parameters.get("card_name"))
                elif action_name == "list_cards":
                    trello_data = self.get_trello_data()
                    if parameters.get("list_name"):
                        list_name = parameters["list_name"]
                        cards = trello_data.get("lists", {}).get(list_name, {})
                        count = cards.get("total_cards", 0)
                        return f"📊 Lista '{list_name}': {count} cards"
                    else:
                        total = sum(lst.get("total_cards", 0) for lst in trello_data.get("lists", {}).values())
                        return f"📊 Total de cards no quadro: {total}"
            
            # Ações do GitHub
            elif mcp == "github":
                github_data = self.get_github_data()
                
                if action_name == "list_commits":
                    commits = github_data.get("recent_commits", [])
                    limit = parameters.get("limit", 5)
                    result = f"📝 Últimos {limit} commits:\n"
                    for i, commit in enumerate(commits[:limit], 1):
                        result += f"{i}. {commit['message']} - {commit['author']}\n"
                    return result
                elif action_name == "list_issues":
                    issues = github_data.get("open_issues_list", [])
                    result = f"🐛 Issues abertas ({github_data.get('open_issues', 0)}):\n"
                    for issue in issues[:5]:
                        result += f"#{issue['number']}: {issue['title']}\n"
                    return result
                elif action_name == "get_repo_info":
                    return (f"📦 Repositório: {github_data.get('repository')}\n"
                           f"⭐ Stars: {github_data.get('stars')}\n"
                           f"🔱 Forks: {github_data.get('forks')}\n"
                           f"💻 Linguagem: {github_data.get('language')}")
            
            # Queries gerais
            elif mcp == "query":
                if action_name == "get_status":
                    trello_data = self.get_trello_data()
                    github_data = self.get_github_data()
                    
                    result = "📊 STATUS DO PROJETO\n\n"
                    result += "🎯 Trello:\n"
                    for list_name, list_data in trello_data.get("lists", {}).items():
                        result += f"  • {list_name}: {list_data.get('total_cards', 0)} cards\n"
                    
                    result += "\n💻 GitHub:\n"
                    result += f"  • Commits recentes: {len(github_data.get('recent_commits', []))}\n"
                    result += f"  • Issues abertas: {github_data.get('open_issues', 0)}\n"
                    
                    return result
            
            return f"❌ Ação '{action_name}' não implementada para {mcp}"
            
        except Exception as e:
            return f"❌ Erro ao executar {action_name}: {str(e)}"
    
    def process_question(self, question: str) -> str:
        """Processa uma pergunta e retorna resposta"""
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - Processando pergunta: {question}")
        
        # ETAPA 1: Classificar intenção com o Intent Classifier
        print("🔍 Classificando intenção...")
        classification = self.intent_classifier.classify_intent(question)
        
        print(f"📋 {self.intent_classifier.get_action_summary(classification)}")
        
        # Se requer confirmação, retornar sugestão
        if classification.get("requires_confirmation"):
            return classification.get("suggested_response", "Preciso de mais informações.")
        
        # ETAPA 2: Executar ações classificadas
        actions = classification.get("actions", [])
        
        if not actions:
            # Fallback para lógica antiga se não houver ações
            return self._process_with_legacy_logic(question)
        
        # Se houver uma única ação, executar diretamente
        if len(actions) == 1:
            return self.execute_classified_action(actions[0])
        
        # Se houver múltiplas ações, executar todas e combinar resultados
        results = []
        for action in sorted(actions, key=lambda x: x.get("priority", 999)):
            result = self.execute_classified_action(action)
            results.append(result)
        
        return "\n\n".join(results)
    
    def _process_with_legacy_logic(self, question: str) -> str:
        """Processa com a lógica antiga (fallback)"""
        question_lower = question.lower()
        
        # Detectar ações e executar automaticamente
        action_result = None
        
        # Atualizar status usando linguagem natural
        if not action_result:
            # Mapeamento de frases para listas (ordem importa: mais específicas primeiro)
            status_map = [
                ('finalizado completamente', 'Concluído'),
                ('está sendo feito', 'Em Desenvolvimento'),
                ('estou fazendo', 'Em Desenvolvimento'),
                ('precisa revisar', 'Revisão de código'),
                ('para revisar', 'Revisão de código'),
                ('está pronto', 'Revisão de código'),
                ('em andamento', 'Em Desenvolvimento'),
                ('precisa fazer', 'A Fazer'),
                ('para fazer', 'A Fazer'),
                ('vou fazer', 'A Fazer'),
                ('concluído', 'Concluído'),
                ('terminei', 'Revisão de código'),
                ('finalizado', 'Revisão de código'),
                ('completo', 'Revisão de código'),
                ('revisão', 'Revisão de código'),
                ('comecei', 'Em Desenvolvimento'),
                ('iniciado', 'Em Desenvolvimento'),
                ('pronto', 'Concluído'),
                ('feito', 'Concluído'),
                ('fazer', 'A Fazer')
            ]
            
            for phrase, target_list in status_map:
                if phrase in question_lower:
                    # Tentar extrair o nome do card
                    # Padrão 1: "meu card Nome está..."
                    match = re.search(r'(?:meu )?card\s+(.+?)\s+(?:está|precisa|vou|para|em|comecei|terminei|iniciado|finalizado|completo|concluído|feito|pronto)', question_lower)
                    if not match:
                        # Padrão 2: "estou fazendo Nome"
                        match = re.search(r'(?:estou fazendo|comecei|terminei|vou fazer)\s+(?:o |card )?(.+)', question_lower)
                    if not match:
                        # Padrão 3: "Nome está..."
                        match = re.search(r'^(.+?)\s+(?:está|precisa|em)', question_lower)
                    
                    if match:
                        card_name = match.group(1).strip()
                        # Remover palavras comuns que podem estar no nome
                        card_name = re.sub(r'^(o |a |meu |minha |card |o card |a card )', '', card_name)
                        # Remover a frase de status se capturada
                        card_name = re.sub(r'\s+(está|precisa|vou|para|em|sendo).*$', '', card_name)
                        action_result = self.move_trello_card(card_name, target_list)
                        break
        
        # Criar card
        if not action_result and ('criar' in question_lower or 'adicionar' in question_lower):
            # Tentar padrão 1: "criar card Nome na lista Lista"
            match = re.search(r'criar\s+card\s+(.+?)\s+na lista\s+(.+)', question_lower)
            if match:
                card_name = match.group(1).strip()
                list_name = match.group(2).strip()
                action_result = self.create_trello_card(card_name, list_name)
            else:
                # Tentar padrão 2: "criar card Nome em Lista"
                match = re.search(r'criar\s+card\s+(.+?)\s+em\s+(.+)', question_lower)
                if match:
                    card_name = match.group(1).strip()
                    list_name = match.group(2).strip()
                    action_result = self.create_trello_card(card_name, list_name)
                else:
                    # Tentar padrão 3: "criar card Nome" (sem lista específica)
                    match = re.search(r'criar\s+card\s+(.+)', question_lower)
                    if match:
                        card_name = match.group(1).strip()
                        action_result = self.create_trello_card(card_name, None)
        
        # Mover card
        if not action_result and ('mover' in question_lower or 'transferir' in question_lower):
            match = re.search(r'(?:mover|transferir)\s+(?:card|o card)?\s*(.+?)\s+para\s+(.+)', question)
            if match:
                card_name = match.group(1).strip()
                list_name = match.group(2).strip()
                action_result = self.move_trello_card(card_name, list_name)
        
        # Editar card (verificar antes de deletar)
        if not action_result and ('editar' in question_lower or 'atualizar' in question_lower):
            match = re.search(r'(?:editar|atualizar)\s+(?:o )?card\s+["\']?([^"\']+)["\']?\s+(?:para|com nome)\s+["\']?([^"\']+)["\']?', question)
            if match:
                card_name = match.group(1).strip()
                new_name = match.group(2).strip()
                action_result = self.update_trello_card(card_name, new_name=new_name)
        
        # Deletar card(s) - apenas se não foi outra ação
        if not action_result and ('deletar' in question_lower or 'remover' in question_lower or 'excluir' in question_lower):
            # Tentar diferentes padrões
            # Padrão 1: "exclua o card N. Nome do Card (ID: xxx)"
            match = re.search(r'(?:deletar|remover|excluir)\s+(?:a |o )?card\s+\d+\.\s*([^(]+?)(?:\s*\([^)]+\))?\.?\s*$', question)
            if match:
                card_name = match.group(1).strip()
                action_result = self.delete_trello_card(card_name)
            else:
                # Padrão 2: "excluir todos os cards com o nome X"
                match = re.search(r'(?:deletar|remover|excluir)\s+(?:todos (?:os )?)?cards?\s+(?:com (?:o )?nome\s+)?["\']?([^"\']+)["\']?', question)
                if match:
                    card_name = match.group(1).strip()
                    action_result = self.delete_trello_card(card_name)
                else:
                    # Padrão 3: "excluir card X"
                    match = re.search(r'(?:deletar|remover|excluir)\s+(?:o )?card\s+["\']?([^"\']+)["\']?', question)
                    if match:
                        card_name = match.group(1).strip()
                        action_result = self.delete_trello_card(card_name)
        
        # Se uma ação foi executada, retornar resultado
        if action_result:
            print(f"Ação executada: {action_result}")
            return action_result
        
        # Caso contrário, gerar resposta contextualizada usando LangGraph
        initial_state = {
            "messages": [],
            "question": question,
            "trello_data": {},
            "github_data": {},
            "context": {},
            "response": ""
        }
        
        # Compilar grafo e executar
        graph = self.build_graph()
        final_state = graph.invoke(initial_state)
        
        return final_state["response"]
    
    def post_to_slack(self, channel_id: str, message: str) -> bool:
        """Posta mensagem no Slack"""
        try:
            conn = http.client.HTTPSConnection("slack.com")
            headers = {
                'Authorization': f'Bearer {self.slack_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'channel': channel_id,
                'text': message
            }
            
            conn.request("POST", "/api/chat.postMessage", json.dumps(data), headers)
            response = conn.getresponse()
            result = json.loads(response.read().decode())
            
            conn.close()
            return result['ok']
            
        except Exception as e:
            print(f"Erro ao postar no Slack: {e}")
            return False

# Função principal para loop
def run_slack_bot():
    """Executa o bot do Slack em loop"""
    print("=" * 60)
    print("LANGGRAPH AGENT PARA SLACK")
    print("=" * 60)
    print("Aguardando mensagens do Slack...")
    print("Pressione Ctrl+C para parar")
    print("=" * 60)
    
    agent = SlackLangGraphAgent()
    import time
    import re
    
    # Timestamp de inicialização + controle de mensagens processadas
    startup_time = time.time()
    processed_messages = set()  # Apenas para mensagens APÓS startup_time
    print(f"Bot inicializado em: {datetime.fromtimestamp(startup_time).strftime('%Y-%m-%d %H:%M:%S')}")
    print("Processando apenas mensagens NOVAS (após inicialização)...")
    print("Aguardando novas menções...")
    
    try:
        while True:
            try:
                # Listar canais
                conn = http.client.HTTPSConnection("slack.com")
                headers = {
                    'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
                    'Content-Type': 'application/json'
                }
                conn.request("GET", "/api/conversations.list", headers=headers)
                response = conn.getresponse()
                data = json.loads(response.read().decode())
                
                if not data.get('ok'):
                    time.sleep(10)
                    continue
                
                # Processar cada canal
                for channel in data.get('channels', []):
                    if not channel.get('is_member'):
                        continue
                    
                    # Obter histórico (últimas 10 mensagens para verificar novas)
                    conn = http.client.HTTPSConnection("slack.com")
                    conn.request("GET", f"/api/conversations.history?channel={channel['id']}&limit=10", headers=headers)
                    response = conn.getresponse()
                    history = json.loads(response.read().decode())
                    
                    if not history.get('ok'):
                        continue
                    
                    # Processar apenas mensagens APÓS o startup_time E que não foram processadas
                    new_messages = []
                    for message in history.get('messages', []):
                        msg_ts = float(message.get('ts', '0'))
                        msg_id = f"{channel['id']}_{message.get('ts', '')}"
                        
                        # Apenas processar mensagens novas (após inicialização) e não processadas
                        if msg_ts > startup_time and msg_id not in processed_messages:
                            new_messages.append(message)
                    
                    if new_messages:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] #{channel['name']}: {len(new_messages)} nova(s) mensagem(ns)")
                    
                    # Processar mensagens novas (ordem cronológica: mais antigas primeiro)
                    for message in reversed(new_messages):
                        text = message.get('text', '')
                        msg_ts = message.get('ts', '')
                        msg_id = f"{channel['id']}_{msg_ts}"
                        
                        # Marcar como processada IMEDIATAMENTE para evitar duplicação
                        processed_messages.add(msg_id)
                        
                        # Verificar se o bot foi mencionado
                        if '<@' in text:
                            user_mentions = re.findall(r'<@([A-Z0-9]+)>', text)
                            
                            if user_mentions:
                                # Extrair pergunta removendo menções
                                question = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
                                question = re.sub(r'\bbot\b', '', question, flags=re.IGNORECASE).strip()
                                
                                if question:
                                    print(f"\n{'='*60}")
                                    print(f"NOVA MENCAO em #{channel['name']}")
                                    print(f"Pergunta: {question}")
                                    print(f"{'='*60}")
                                    
                                    # Processar com LangGraph
                                    try:
                                        response = agent.process_question(question)
                                        
                                        # Enviar resposta
                                        if agent.post_to_slack(channel['id'], response):
                                            print(f"[OK] Resposta enviada para #{channel['name']}")
                                        else:
                                            print(f"[ERRO] Falha ao enviar resposta")
                                    except Exception as e:
                                        print(f"[ERRO] Ao processar: {e}")
                
                conn.close()
                time.sleep(5)  # Verificar a cada 5 segundos
                
            except Exception as e:
                print(f"Erro na iteracao: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\nBot encerrado pelo usuario")
        import sys
        sys.exit(0)

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("ERRO: OPENAI_API_KEY nao encontrada no arquivo .env")
    else:
        run_slack_bot()

