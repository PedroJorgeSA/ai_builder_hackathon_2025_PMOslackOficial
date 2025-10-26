# 🚀 Deploy na Vercel - Guia Completo

Deploy simples e rápido da sua solução MCP na Vercel.

## 🎯 Por que Vercel?

✅ **Vantagens:**
- Deploy em 2 minutos
- HTTPS automático
- Escala automaticamente
- Free tier generoso (100GB bandwidth)
- Zero configuração de servidor
- Integração com GitHub

⚠️ **Limitações:**
- Serverless (não mantém estado)
- Timeout de 10s por função (hobby plan)
- Melhor para webhook-based (não para polling contínuo)

---

## 📋 Pré-requisitos

1. Conta na Vercel (gratuita)
2. GitHub account (para CI/CD automático)
3. Credenciais configuradas:
   - Trello API Key e Token
   - Slack Bot Token
   - OpenAI API Key (opcional)
   - GitHub Token (opcional)

---

## 🚀 Deploy em 3 Passos

### Passo 1: Preparar o Projeto

No seu projeto, certifique-se de que os arquivos estão presentes:

```bash
# Verificar estrutura
ls -la api/
ls vercel.json
```

**Estrutura necessária:**
```
projeto/
├── api/
│   ├── health.js
│   ├── slack/
│   │   └── events.py
│   └── trello/
│       └── cards.js
├── vercel.json
└── package.json
```

### Passo 2: Deploy via CLI ou GitHub

#### Opção A: Via Vercel CLI (Mais Rápido)

```bash
# 1. Instalar Vercel CLI
npm install -g vercel

# 2. Login
vercel login

# 3. Deploy
vercel

# 4. Seguir as instruções interativas
```

#### Opção B: Via GitHub (Recomendado para Produção)

```bash
# 1. Criar repositório no GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/seu-usuario/seu-repo.git
git push -u origin main

# 2. Importar no Vercel
# - Acesse: https://vercel.com/new
# - Clique em "Import Git Repository"
# - Selecione seu repositório
# - Clique em "Deploy"
```

### Passo 3: Configurar Variáveis de Ambiente

No dashboard da Vercel:

1. Vá em **Settings** → **Environment Variables**
2. Adicione cada variável:

```env
TRELLO_API_KEY=sua-api-key
TRELLO_TOKEN=seu-token
TRELLO_BOARD_ID=id-do-quadro

SLACK_BOT_TOKEN=xoxb-seu-bot-token
SLACK_SIGNING_SECRET=seu-signing-secret

GITHUB_TOKEN=seu-github-token

OPENAI_API_KEY=sk-sua-key
```

3. Clique em **Save**
4. Faça **Redeploy** do projeto

---

## 🔧 Configurar Webhook do Slack

Sua aplicação na Vercel receberá eventos via webhook.

### 1. Obter URL da Vercel

Após o deploy, você terá uma URL tipo:
```
https://seu-projeto.vercel.app
```

### 2. Configurar no Slack

1. Acesse https://api.slack.com/apps
2. Selecione seu app
3. Vá em **Event Subscriptions**
4. Ative **Enable Events**
5. Em **Request URL**, coloque:
   ```
   https://seu-projeto.vercel.app/api/slack/events
   ```
6. Aguarde a verificação ✅
7. Em **Subscribe to bot events**, adicione:
   - `app_mention`
   - `message.channels`
8. Salve as mudanças

### 3. Testar

No Slack, mencione seu bot:
```
@bot olá
```

Deve receber uma resposta!

---

## 📡 Endpoints Disponíveis

Sua aplicação terá os seguintes endpoints:

### Health Check
```bash
GET https://seu-projeto.vercel.app/api/health
```

**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-26T...",
  "service": "MCP Custom Server",
  "version": "1.0.0"
}
```

### Webhook do Slack
```bash
POST https://seu-projeto.vercel.app/api/slack/events
```

Recebe eventos do Slack automaticamente.

### API do Trello
```bash
# Listar cards
GET https://seu-projeto.vercel.app/api/trello/cards

# Criar card
POST https://seu-projeto.vercel.app/api/trello/cards
Content-Type: application/json

{
  "name": "Nova tarefa",
  "desc": "Descrição",
  "listId": "id-da-lista"
}
```

---

## 🧪 Testar Localmente

Antes de fazer deploy, teste localmente:

```bash
# 1. Instalar Vercel CLI
npm install -g vercel

# 2. Criar .env local
cp env.template .env.local
nano .env.local  # Preencher credenciais

# 3. Rodar localmente
vercel dev

# Acesse: http://localhost:3000
```

---

## 📊 Monitoramento

### Ver Logs

No dashboard da Vercel:
1. Vá em **Deployments**
2. Clique no deployment ativo
3. Clique em **Functions**
4. Selecione uma função para ver logs

### Ou via CLI:
```bash
vercel logs
```

### Analytics

A Vercel fornece:
- Número de requisições
- Tempo de resposta
- Erros
- Bandwidth usado

Acesse em: **Analytics** no dashboard

---

## 🔄 Atualizar Deploy

### Automático (via GitHub)

Basta fazer push:
```bash
git add .
git commit -m "Atualização"
git push
```

A Vercel fará deploy automaticamente! 🎉

### Manual (via CLI)

```bash
vercel --prod
```

---

## 💰 Custos

### Free Tier (Hobby)
- ✅ Bandwidth: 100 GB/mês
- ✅ Builds: 100 horas/mês
- ✅ Serverless Functions: Ilimitadas
- ✅ Timeout: 10 segundos
- ✅ Domínios: Ilimitados

**Custo: $0/mês**

### Pro Plan
- 🚀 Bandwidth: 1 TB/mês
- 🚀 Timeout: 60 segundos
- 🚀 Mais recursos

**Custo: $20/mês**

Para a maioria dos casos, **Free Tier é suficiente!**

---

## 🔍 Troubleshooting

### Erro: "Invalid signature"

**Solução:** Configure `SLACK_SIGNING_SECRET` nas variáveis de ambiente

### Erro: "Credenciais não configuradas"

**Solução:** 
1. Adicione variáveis no dashboard da Vercel
2. Faça redeploy

### Timeout em requests

**Solução:**
- Free tier: 10s timeout (não dá para mudar)
- Upgrade para Pro: 60s timeout
- Otimize código para ser mais rápido

### Webhook do Slack não funciona

**Solução:**
1. Verifique URL no Slack: deve ter `/api/slack/events`
2. Teste health check: `https://seu-projeto.vercel.app/api/health`
3. Veja logs na Vercel

---

## 🎯 Exemplo Completo

### 1. Deploy
```bash
# Clone o projeto
git clone seu-repo
cd seu-repo

# Deploy
vercel
```

### 2. Configurar Variáveis

No dashboard da Vercel, adicione:
- `TRELLO_API_KEY`
- `TRELLO_TOKEN`
- `SLACK_BOT_TOKEN`
- etc.

### 3. Configurar Slack

URL do webhook:
```
https://seu-projeto.vercel.app/api/slack/events
```

### 4. Testar

```bash
# No Slack
@bot criar card Nova Tarefa
```

---

## 📚 Recursos Adicionais

- [Documentação Vercel](https://vercel.com/docs)
- [Vercel CLI](https://vercel.com/docs/cli)
- [Serverless Functions](https://vercel.com/docs/concepts/functions/serverless-functions)

---

## ✅ Checklist de Deploy

- [ ] Criar conta na Vercel
- [ ] Projeto tem estrutura correta (`api/` folder)
- [ ] `vercel.json` configurado
- [ ] Deploy via CLI ou GitHub
- [ ] Adicionar variáveis de ambiente
- [ ] Configurar webhook do Slack
- [ ] Testar health check
- [ ] Testar menção no Slack
- [ ] Monitorar logs

---

## 🎉 Pronto!

Sua aplicação está no ar em:
```
https://seu-projeto.vercel.app
```

**Próximos passos:**
1. Configurar domínio customizado (opcional)
2. Adicionar mais endpoints
3. Implementar mais funcionalidades
4. Monitorar uso e performance

---

**Deploy feito! Agora é só usar! 🚀**

