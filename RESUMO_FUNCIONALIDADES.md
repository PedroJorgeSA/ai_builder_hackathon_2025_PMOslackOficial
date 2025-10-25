# Resumo das Funcionalidades do PMO Bot

## Visão Geral

O PMO Bot é um agente inteligente integrado ao Slack que gerencia cards do Trello usando linguagem natural e comandos diretos.

---

## Funcionalidades Implementadas

### 1. **Deletar Cards** ✓
Deletar um ou mais cards do quadro Trello.

**Exemplos:**
- `@bot excluir card Card solicitado`
- `@bot deletar card Tarefa de teste`
- `@bot remover todos os cards com o nome Backlog antigo`

---

### 2. **Mover Cards** ✓
Mover cards entre listas do quadro.

**Exemplos:**
- `@bot mover card Tarefa importante para Em Desenvolvimento`
- `@bot mover Card de teste para A Fazer`

---

### 3. **Criar Cards** ✓
Criar novos cards em listas específicas.

**Exemplos:**
- `@bot criar card Nova funcionalidade na lista Backlog`
- `@bot criar card Corrigir bug em A Fazer`
- `@bot criar card Reunião de planejamento` (cria no Backlog por padrão)

---

### 4. **Atualizar Status com Linguagem Natural** ✓

O bot entende frases naturais para mover cards automaticamente entre listas!

#### Para "Em Desenvolvimento":
- `@bot meu card Card solicitado está sendo feito`
- `@bot estou fazendo o Card de teste`
- `@bot comecei o card Implementar feature`
- `@bot card Bug crítico em andamento`

#### Para "Revisão de código":
- `@bot card Nova feature está pronto`
- `@bot terminei o Card de teste`
- `@bot card Corrigir bug precisa revisar`

#### Para "Concluído":
- `@bot card Feature X concluído`
- `@bot meu card Tarefa importante feito`

#### Para "A Fazer":
- `@bot vou fazer o card Nova tarefa`
- `@bot card Refatoração para fazer`

---

## Arquitetura

### Componentes Principais

1. **LangGraph Agent** (`langgraph_agent.py`)
   - Processa mensagens do Slack
   - Detecta comandos e linguagem natural
   - Executa ações no Trello
   - Gera respostas contextualizadas via GPT-4o-mini

2. **MCP Custom Server** (`mcp-custom-server.js`)
   - Fornece tools para Trello, Slack e GitHub
   - Expõe funções via protocolo MCP
   - Gerencia autenticação e requisições

3. **Configurações** (`mcp.json`)
   - Define o servidor MCP customizado
   - Armazena credenciais (via variáveis de ambiente)

---

## Integrações

### Trello
- ✓ Listar boards e cards
- ✓ Criar cards
- ✓ Mover cards entre listas
- ✓ Deletar cards
- ✓ Atualizar cards

### Slack
- ✓ Detectar menções ao bot
- ✓ Processar mensagens em tempo real
- ✓ Responder com contexto
- ✓ Enviar notificações

### GitHub
- ✓ Listar commits
- ✓ Listar issues
- ✓ Criar issues
- ✓ Obter informações do repositório

### OpenAI
- ✓ GPT-4o-mini para respostas contextualizadas
- ✓ LangGraph para orquestração de workflows
- ✓ Processamento de linguagem natural

---

## Tecnologias Utilizadas

- **Python 3.12+**
  - `langgraph` - Orquestração de agentes
  - `langchain-openai` - Integração com OpenAI
  - `python-dotenv` - Gerenciamento de variáveis de ambiente
  - `http.client` - Requisições HTTP

- **Node.js**
  - `@modelcontextprotocol/sdk` - Servidor MCP
  - `https` - Requisições HTTPS para APIs

- **APIs**
  - Trello REST API
  - Slack Web API
  - GitHub REST API
  - OpenAI API (GPT-4o-mini)

---

## Como Usar

### 1. Iniciar o Bot

```bash
python langgraph_agent.py
```

### 2. Mencionar o Bot no Slack

```
@bot [comando]
```

### 3. Comandos Disponíveis

Consulte `README_comandos_trello.md` para lista completa de comandos e exemplos.

---

## Logs e Debug

O bot exibe logs detalhados no console:

- Detecção de menções
- Identificação de comandos
- Extração de parâmetros (nome do card, lista, etc.)
- Execução de ações
- Respostas geradas

**Exemplo:**
```
Debug: Analisando pergunta para acoes: meu card X está sendo feito
Debug: Detectada atualização de status: 'está sendo feito' -> 'Em Desenvolvimento'
Debug: Card identificado: 'X'
✅ Card 'X' movido para 'Em Desenvolvimento' com sucesso!
```

---

## Documentação

- `README_comandos_trello.md` - Guia completo de comandos
- `RESUMO_FUNCIONALIDADES.md` - Este arquivo
- Código comentado em `langgraph_agent.py`

---

## Segurança

- Credenciais armazenadas em arquivo `.env`
- Tokens nunca expostos no código
- Validação de entrada do usuário
- Rate limiting nas APIs (respeitado)

---

## Próximas Melhorias Sugeridas

1. Adicionar suporte para múltiplos quadros Trello
2. Implementar comandos para GitHub (criar PRs, comentar em issues)
3. Adicionar análise de sentimento nas mensagens
4. Criar dashboards de métricas do projeto
5. Implementar notificações proativas (prazos, atualizações)
6. Suportar comandos de voz (integração com Slack Huddles)

---

**Desenvolvido para gerenciar projetos de forma inteligente e natural!** 🚀

