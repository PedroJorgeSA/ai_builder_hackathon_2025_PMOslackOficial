# 🚀 MCP Customizado Trello + Slack

Um servidor MCP (Model Context Protocol) customizado que integra Trello e Slack, permitindo operações unificadas entre as duas plataformas.

## ✨ Funcionalidades

### 📋 Trello
- **Listar quadros** - Visualizar todos os quadros do usuário
- **Consultar cards** - Ver cards organizados por lista
- **Criar cards** - Adicionar novos cards
- **Mover cards** - Transferir cards entre listas

### 💬 Slack
- **Listar canais** - Ver todos os canais disponíveis
- **Histórico de mensagens** - Consultar mensagens de canais
- **Postar mensagens** - Enviar mensagens para canais

### 🔗 Integração
- **Criar card + notificar no Slack** - Operação unificada
- **Sincronização automática** - Notificações em tempo real

## 🛠️ Instalação

1. **Instalar dependências:**
   ```bash
   npm install
   ```

2. **Configurar credenciais no `mcp.json`:**
   ```json
   {
     "mcpServers": {
       "custom-trello-slack": {
         "command": "node",
         "args": ["./mcp-custom-server.js"],
         "env": {
           "TRELLO_API_KEY": "sua-api-key",
           "TRELLO_TOKEN": "seu-token",
           "TRELLO_BOARD_ID": "id-do-quadro",
           "SLACK_BOT_TOKEN": "seu-bot-token",
           "SLACK_TEAM_ID": "id-do-time"
         }
       }
     }
   }
   ```

## 🎯 Ferramentas Disponíveis

### Trello
- `trello_get_boards` - Lista quadros
- `trello_get_cards` - Lista cards de um quadro
- `trello_create_card` - Cria novo card
- `trello_move_card` - Move card entre listas

### Slack
- `slack_list_channels` - Lista canais
- `slack_get_channel_history` - Histórico de canal
- `slack_post_message` - Posta mensagem

### Integração
- `trello_slack_integration` - Cria card + notifica no Slack

## 🚀 Uso

Após configurar o `mcp.json`, reinicie o Cursor e use as ferramentas através do chat:

```
"Liste meus cards do Trello"
"Crie um card chamado 'Nova tarefa'"
"Poste uma mensagem no canal #geral"
"Crie um card e notifique no Slack"
```

## 📝 Exemplo de Uso

```javascript
// Criar card e notificar no Slack
{
  "cardName": "Nova funcionalidade",
  "cardDescription": "Implementar nova feature",
  "listId": "id-da-lista",
  "slackChannelId": "id-do-canal",
  "slackMessage": "🎯 Nova tarefa criada: Nova funcionalidade"
}
```

## 🔧 Configuração

### Trello
1. Acesse: https://trello.com/app-key
2. Copie sua API Key
3. Gere um token com as permissões necessárias

### Slack
1. Crie um app em: https://api.slack.com/apps
2. Configure as permissões necessárias
3. Instale o app no workspace
4. Copie o Bot Token

## 📊 Status

- ✅ Estrutura do MCP criada
- ✅ Funções do Trello implementadas
- ✅ Funções do Slack implementadas
- ✅ Integração configurada
- ✅ Dependências instaladas
- ✅ Configuração atualizada

## 🎉 Pronto para usar!

Reinicie o Cursor e comece a usar o MCP customizado!
