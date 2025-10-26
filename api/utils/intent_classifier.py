"""
Intent Classifier para processar linguagem natural
Adaptado para Vercel Serverless Functions
"""

import json
import os
import re

def classify_intent(text):
    """
    Classifica a intenção do usuário a partir do texto
    Retorna: { 'intent': str, 'params': dict }
    """
    text_lower = text.lower()
    
    # Remover menção ao bot
    text_lower = re.sub(r'<@[A-Z0-9]+>', '', text_lower).strip()
    
    # Intent: Listar commits do GitHub
    if any(word in text_lower for word in ['commit', 'commits', 'histórico', 'historico']):
        # Extrair número de commits
        match = re.search(r'(\d+)\s*(?:último|últimos|ultima|ultimas|último|últimos)?', text_lower)
        limit = int(match.group(1)) if match else 5
        
        return {
            'intent': 'github_commits',
            'params': {
                'limit': limit
            },
            'confidence': 0.95
        }
    
    # Intent: Criar card no Trello
    if any(word in text_lower for word in ['criar', 'adicionar', 'novo card', 'nova tarefa']):
        # Extrair nome do card
        patterns = [
            r'criar (?:um )?(?:card|tarefa) (?:chamado |chamada )?["\']?(.+?)["\']?$',
            r'adicionar (?:um )?(?:card|tarefa) ["\']?(.+?)["\']?$',
            r'novo (?:card|tarefa) ["\']?(.+?)["\']?$',
            r'criar ["\']?(.+?)["\']? no (?:trello|quadro)',
        ]
        
        card_name = None
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                card_name = match.group(1).strip()
                break
        
        if not card_name:
            # Tentar extrair tudo depois de "criar"
            match = re.search(r'criar (.+)', text_lower)
            if match:
                card_name = match.group(1).strip()
        
        return {
            'intent': 'trello_create_card',
            'params': {
                'card_name': card_name or 'Nova tarefa'
            },
            'confidence': 0.9 if card_name else 0.6
        }
    
    # Intent: Listar cards do Trello
    if any(word in text_lower for word in ['listar', 'mostrar', 'ver', 'quais', 'cards', 'tarefas']):
        if any(word in text_lower for word in ['card', 'tarefa', 'trello', 'quadro']):
            return {
                'intent': 'trello_list_cards',
                'params': {},
                'confidence': 0.9
            }
    
    # Intent: Deletar card
    if any(word in text_lower for word in ['deletar', 'excluir', 'remover', 'apagar']):
        if any(word in text_lower for word in ['card', 'tarefa']):
            # Extrair nome do card
            patterns = [
                r'(?:deletar|excluir|remover|apagar) (?:o )?(?:card |tarefa )?["\']?(.+?)["\']?$',
                r'(?:deletar|excluir|remover|apagar) ["\']?(.+?)["\']?$',
            ]
            
            card_name = None
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    card_name = match.group(1).strip()
                    break
            
            return {
                'intent': 'trello_delete_card',
                'params': {
                    'card_name': card_name
                },
                'confidence': 0.9 if card_name else 0.6
            }
    
    # Intent: Mover card
    if any(word in text_lower for word in ['mover', 'mudar', 'transferir']):
        # Extrair nome do card e lista destino
        card_match = re.search(r'(?:mover|mudar|transferir) (?:o )?(?:card |tarefa )?["\']?(.+?)["\']? (?:para|pra)', text_lower)
        list_match = re.search(r'(?:para|pra) (?:a lista )?["\']?(.+?)["\']?$', text_lower)
        
        return {
            'intent': 'trello_move_card',
            'params': {
                'card_name': card_match.group(1).strip() if card_match else None,
                'target_list': list_match.group(1).strip() if list_match else None
            },
            'confidence': 0.85 if (card_match and list_match) else 0.5
        }
    
    # Intent: Listar listas do quadro
    if any(word in text_lower for word in ['listas', 'colunas']):
        if any(word in text_lower for word in ['listar', 'mostrar', 'ver', 'quais']):
            return {
                'intent': 'trello_list_lists',
                'params': {},
                'confidence': 0.9
            }
    
    # Intent: Atualizar/editar card
    if any(word in text_lower for word in ['atualizar', 'editar', 'modificar', 'alterar']):
        if any(word in text_lower for word in ['card', 'tarefa', 'descrição', 'descricao']):
            card_match = re.search(r'(?:card |tarefa )?["\']?(.+?)["\']?(?:com|para)', text_lower)
            
            return {
                'intent': 'trello_update_card',
                'params': {
                    'card_name': card_match.group(1).strip() if card_match else None
                },
                'confidence': 0.8
            }
    
    # Intent: Status de card (linguagem natural)
    status_patterns = {
        'em desenvolvimento': ['fazendo', 'trabalhando', 'desenvolvendo', 'em andamento', 'comecei'],
        'revisão': ['pronto', 'terminei', 'concluí', 'revisar', 'review'],
        'concluído': ['concluído', 'concluido', 'feito', 'finalizado', 'completo'],
        'a fazer': ['vou fazer', 'para fazer', 'fazer depois']
    }
    
    for status, keywords in status_patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            # Extrair nome do card
            card_match = re.search(r'(?:card|tarefa) ["\']?(.+?)["\']? (?:está|esta|ta|ficou)', text_lower)
            if not card_match:
                card_match = re.search(r'(?:meu|o) (?:card|tarefa) ["\']?(.+?)["\']?', text_lower)
            
            return {
                'intent': 'trello_update_status',
                'params': {
                    'card_name': card_match.group(1).strip() if card_match else None,
                    'status': status
                },
                'confidence': 0.8
            }
    
    # Intent: Ajuda
    if any(word in text_lower for word in ['ajuda', 'help', 'ajudar', 'comandos', 'o que você faz']):
        return {
            'intent': 'help',
            'params': {},
            'confidence': 1.0
        }
    
    # Intent: Saudação
    if any(word in text_lower for word in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'e ai', 'e aí']):
        return {
            'intent': 'greeting',
            'params': {},
            'confidence': 0.95
        }
    
    # Intent desconhecido
    return {
        'intent': 'unknown',
        'params': {},
        'confidence': 0.0
    }


def classify_with_openai(text):
    """
    Classificação avançada usando OpenAI (opcional)
    Usa GPT para entender contextos mais complexos
    """
    import urllib.request
    
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    if not openai_key:
        # Fallback para classificação baseada em regras
        return classify_intent(text)
    
    try:
        # Preparar prompt para o GPT
        system_prompt = """Você é um classificador de intenções para um bot PMO.
Analise o texto do usuário e retorne um JSON com:
- intent: uma das opções (github_commits, trello_create_card, trello_list_cards, trello_move_card, trello_delete_card, trello_list_lists, trello_update_card, trello_update_status, help, greeting, unknown)
- params: parâmetros extraídos do texto
- confidence: confiança de 0 a 1

Exemplos:
"me diga os últimos 5 commits" -> {"intent": "github_commits", "params": {"limit": 5}, "confidence": 0.95}
"criar card Nova Feature" -> {"intent": "trello_create_card", "params": {"card_name": "Nova Feature"}, "confidence": 0.9}
"deletar card Bug Antigo" -> {"intent": "trello_delete_card", "params": {"card_name": "Bug Antigo"}, "confidence": 0.9}
"mover card X para Em Progresso" -> {"intent": "trello_move_card", "params": {"card_name": "X", "target_list": "Em Progresso"}, "confidence": 0.9}
"""

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,
            "max_tokens": 200
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            'https://api.openai.com/v1/chat/completions',
            data=data,
            headers={
                'Authorization': f'Bearer {openai_key}',
                'Content-Type': 'application/json'
            }
        )
        
        response = urllib.request.urlopen(req, timeout=10)
        result = json.loads(response.read())
        
        # Extrair resposta do GPT
        content = result['choices'][0]['message']['content']
        
        # Parse JSON da resposta
        try:
            classification = json.loads(content)
            return classification
        except:
            # Se GPT não retornou JSON válido, usar classificação baseada em regras
            return classify_intent(text)
    
    except Exception as e:
        print(f"Erro ao usar OpenAI: {e}")
        # Fallback para classificação baseada em regras
        return classify_intent(text)


def extract_parameters(text, intent):
    """
    Extrai parâmetros específicos baseado no intent
    """
    params = {}
    text_lower = text.lower()
    
    if intent == 'github_commits':
        match = re.search(r'(\d+)', text_lower)
        params['limit'] = int(match.group(1)) if match else 5
    
    elif intent == 'trello_create_card':
        # Extrair nome do card
        patterns = [
            r'criar (?:card |um card )?["\']?(.+?)["\']?$',
            r'adicionar ["\']?(.+?)["\']?$',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                params['card_name'] = match.group(1).strip()
                break
    
    return params

