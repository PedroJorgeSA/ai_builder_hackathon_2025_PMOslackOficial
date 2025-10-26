# ⚡ Vercel - Início Rápido (2 minutos!)

## 🚀 3 Comandos para Deploy

```bash
# 1. Instalar Vercel CLI
npm install -g vercel

# 2. Login
vercel login

# 3. Deploy!
vercel
```

**Pronto!** ✅ Sua aplicação está online!

---

## 🔧 Configuração Rápida

### 1. Adicionar Variáveis de Ambiente

No dashboard da Vercel (após deploy):

```
Settings → Environment Variables → Add

TRELLO_API_KEY → sua-api-key
TRELLO_TOKEN → seu-token
TRELLO_BOARD_ID → id-do-quadro
SLACK_BOT_TOKEN → xoxb-seu-token
SLACK_SIGNING_SECRET → seu-secret
OPENAI_API_KEY → sk-sua-key
```

### 2. Configurar Webhook do Slack

1. Pegue sua URL da Vercel:
   ```
   https://seu-projeto.vercel.app
   ```

2. No Slack (https://api.slack.com/apps):
   ```
   Event Subscriptions → Request URL:
   https://seu-projeto.vercel.app/api/slack/events
   ```

3. Subscribe to events:
   - `app_mention`
   - `message.channels`

---

## ✅ Testar

### Health Check
```bash
curl https://seu-projeto.vercel.app/api/health
```

### No Slack
```
@bot olá
```

---

## 📊 Ver Logs

```bash
vercel logs
```

Ou no dashboard: **Deployments → Functions → Logs**

---

## 🔄 Atualizar

```bash
git push  # Se conectado ao GitHub
# ou
vercel --prod
```

---

## 💡 Dica Pro

Conecte ao GitHub para deploy automático:

```bash
# Push = Deploy automático! 🎉
git add .
git commit -m "Update"
git push
```

---

## 📚 Guia Completo

Veja [VERCEL_DEPLOY.md](./VERCEL_DEPLOY.md) para mais detalhes.

---

**Deploy feito! 🎉**

