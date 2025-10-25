"""
Agent Classificador de Intenções
Analisa mensagens em linguagem natural e identifica ações para MCPs (Trello e GitHub)
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class IntentClassifierAgent:
    """
    Agent responsável por classificar intenções de mensagens e mapear para ações específicas
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,  # Baixa temperatura para respostas mais determinísticas
            api_key=OPENAI_API_KEY
        )
        
        # Definição de ações disponíveis para cada MCP
        self.available_actions = {
            "trello": [
                "create_card",
                "move_card",
                "update_card",
                "delete_card",
                "list_cards",
                "get_card_details"
            ],
            "github": [
                "create_issue",
                "list_issues",
                "get_repo_info",
                "list_commits",
                "comment_on_issue"
            ],
            "query": [
                "get_status",
                "get_summary",
                "analyze_project"
            ]
        }
    
    def classify_intent(self, message: str) -> Dict:
        """
        Classifica a intenção da mensagem e retorna ações estruturadas
        
        Args:
            message: Mensagem em linguagem natural do usuário
            
        Returns:
            Dict com estrutura:
            {
                "intent_type": "action" | "query" | "ambiguous",
                "confidence": float (0-1),
                "actions": [
                    {
                        "mcp": "trello" | "github",
                        "action": "nome_da_acao",
                        "parameters": {...},
                        "priority": int (1-10)
                    }
                ],
                "reasoning": "Explicação da classificação",
                "requires_confirmation": bool
            }
        """
        
        system_prompt = self._get_system_prompt()
        
        user_message = f"""
Analise a seguinte mensagem e identifique as ações necessárias:

MENSAGEM: "{message}"

Retorne APENAS um JSON válido seguindo o formato especificado.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            # Parse da resposta JSON
            result = json.loads(response.content)
            
            # Validar estrutura
            if not self._validate_result(result):
                return self._create_error_response(message)
            
            return result
            
        except json.JSONDecodeError:
            # Se o LLM não retornar JSON válido, tentar extrair
            return self._fallback_parse(response.content, message)
    
    def _get_system_prompt(self) -> str:
        """Retorna o prompt do sistema para o classificador"""
        return f"""Você é um agente especializado em classificar intenções de usuários e mapear para ações específicas em sistemas de gerenciamento de projetos (Trello) e controle de versão (GitHub).

## AÇÕES DISPONÍVEIS

### Trello
{json.dumps(self.available_actions["trello"], indent=2)}

### GitHub
{json.dumps(self.available_actions["github"], indent=2)}

### Query (Consultas)
{json.dumps(self.available_actions["query"], indent=2)}

## TIPOS DE INTENÇÃO

1. **action**: Usuário quer executar uma ação específica
   - Criar, mover, deletar cards
   - Criar issues, listar commits
   
2. **query**: Usuário quer consultar informações
   - Status do projeto
   - Resumo de atividades
   - Análise de dados
   
3. **ambiguous**: Intenção não está clara
   - Precisa de mais informações
   - Múltiplas interpretações possíveis

## REGRAS DE CLASSIFICAÇÃO

1. Identifique TODAS as ações mencionadas na mensagem
2. Para cada ação, extraia os parâmetros necessários
3. Se parâmetros faltarem, marque como "requires_confirmation: true"
4. Atribua prioridade (1-10) para ações múltiplas
5. Explique seu raciocínio de forma clara

## FORMATO DE RESPOSTA (JSON)

{{
  "intent_type": "action | query | ambiguous",
  "confidence": 0.95,
  "actions": [
    {{
      "mcp": "trello",
      "action": "create_card",
      "parameters": {{
        "card_name": "Nome extraído da mensagem",
        "target_list": "Backlog"
      }},
      "priority": 1,
      "reasoning": "Usuário solicitou criação de card explicitamente"
    }}
  ],
  "reasoning": "Análise geral da mensagem",
  "requires_confirmation": false,
  "suggested_response": "Resposta sugerida ao usuário"
}}

## EXEMPLOS

**Exemplo 1:**
Mensagem: "criar card Bug na API na lista Backlog"
Resultado:
{{
  "intent_type": "action",
  "confidence": 0.98,
  "actions": [
    {{
      "mcp": "trello",
      "action": "create_card",
      "parameters": {{
        "card_name": "Bug na API",
        "target_list": "Backlog"
      }},
      "priority": 1,
      "reasoning": "Comando explícito de criação com nome e lista especificados"
    }}
  ],
  "reasoning": "Intenção clara de criar um card no Trello com todos os parâmetros fornecidos",
  "requires_confirmation": false,
  "suggested_response": "Card 'Bug na API' será criado na lista 'Backlog'"
}}

**Exemplo 2:**
Mensagem: "o card de login está pronto para revisão"
Resultado:
{{
  "intent_type": "action",
  "confidence": 0.90,
  "actions": [
    {{
      "mcp": "trello",
      "action": "move_card",
      "parameters": {{
        "card_name": "login",
        "target_list": "Revisão de código"
      }},
      "priority": 1,
      "reasoning": "Usuário indica status de conclusão, implica movimentação para revisão"
    }}
  ],
  "reasoning": "Mensagem em linguagem natural indicando mudança de status",
  "requires_confirmation": false,
  "suggested_response": "Card 'login' será movido para 'Revisão de código'"
}}

**Exemplo 3:**
Mensagem: "quantos cards temos no backlog e quais foram os últimos commits?"
Resultado:
{{
  "intent_type": "query",
  "confidence": 0.95,
  "actions": [
    {{
      "mcp": "trello",
      "action": "list_cards",
      "parameters": {{
        "list_name": "Backlog",
        "count_only": true
      }},
      "priority": 1,
      "reasoning": "Primeira parte da pergunta sobre contagem de cards"
    }},
    {{
      "mcp": "github",
      "action": "list_commits",
      "parameters": {{
        "limit": 5
      }},
      "priority": 2,
      "reasoning": "Segunda parte sobre commits recentes"
    }}
  ],
  "reasoning": "Duas consultas independentes, uma para Trello e outra para GitHub",
  "requires_confirmation": false,
  "suggested_response": "Vou buscar a quantidade de cards no Backlog e os últimos commits para você"
}}

**Exemplo 4:**
Mensagem: "crie uma issue urgente"
Resultado:
{{
  "intent_type": "action",
  "confidence": 0.75,
  "actions": [
    {{
      "mcp": "github",
      "action": "create_issue",
      "parameters": {{
        "title": null,
        "labels": ["urgent"],
        "body": null
      }},
      "priority": 1,
      "reasoning": "Falta título e descrição da issue"
    }}
  ],
  "reasoning": "Intenção clara mas parâmetros incompletos",
  "requires_confirmation": true,
  "suggested_response": "Para criar a issue urgente, preciso do título e descrição. Pode fornecer?"
}}

Seja preciso, analítico e sempre retorne JSON válido.
"""
    
    def _validate_result(self, result: Dict) -> bool:
        """Valida a estrutura do resultado"""
        required_keys = ["intent_type", "confidence", "actions", "reasoning"]
        
        if not all(key in result for key in required_keys):
            return False
        
        if result["intent_type"] not in ["action", "query", "ambiguous"]:
            return False
        
        if not isinstance(result["actions"], list):
            return False
        
        # Validar cada ação
        for action in result["actions"]:
            if not all(key in action for key in ["mcp", "action", "parameters"]):
                return False
        
        return True
    
    def _create_error_response(self, message: str) -> Dict:
        """Cria resposta de erro padronizada"""
        return {
            "intent_type": "ambiguous",
            "confidence": 0.0,
            "actions": [],
            "reasoning": f"Não foi possível classificar a mensagem: '{message}'",
            "requires_confirmation": True,
            "suggested_response": "Desculpe, não entendi. Pode reformular?"
        }
    
    def _fallback_parse(self, content: str, message: str) -> Dict:
        """Tenta extrair informações mesmo se não for JSON válido"""
        # Implementação simplificada de fallback
        return self._create_error_response(message)
    
    def get_action_summary(self, classification: Dict) -> str:
        """
        Retorna um resumo textual da classificação para logging
        """
        intent = classification["intent_type"]
        confidence = classification["confidence"]
        actions_count = len(classification["actions"])
        
        summary = f"Intenção: {intent.upper()} (confiança: {confidence:.0%})\n"
        summary += f"Ações identificadas: {actions_count}\n"
        
        for i, action in enumerate(classification["actions"], 1):
            mcp = action["mcp"]
            action_name = action["action"]
            priority = action.get("priority", 0)
            summary += f"  {i}. [{mcp.upper()}] {action_name} (prioridade: {priority})\n"
        
        if classification.get("requires_confirmation"):
            summary += "\n⚠️ REQUER CONFIRMAÇÃO DO USUÁRIO\n"
        
        return summary


# Função de teste
def test_classifier():
    """Testa o classificador com exemplos"""
    classifier = IntentClassifierAgent()
    
    test_cases = [
        "criar card Bug na API na lista Backlog",
        "mover card Login para Revisão de código",
        "quantos cards temos?",
        "o card de autenticação está pronto",
        "crie uma issue sobre o erro 404",
        "me mostre os últimos commits e cards em andamento"
    ]
    
    print("=" * 60)
    print("TESTE DO CLASSIFICADOR DE INTENÇÕES")
    print("=" * 60)
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n[TESTE {i}] Mensagem: {message}")
        print("-" * 60)
        
        result = classifier.classify_intent(message)
        print(classifier.get_action_summary(result))
        print(f"Raciocínio: {result['reasoning']}")


if __name__ == "__main__":
    test_classifier()

