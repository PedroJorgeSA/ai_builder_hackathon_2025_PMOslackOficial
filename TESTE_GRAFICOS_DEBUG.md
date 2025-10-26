# 🔍 Debug de Gráficos - Guia Completo

## 🚀 Deploy Primeiro

```bash
git add .
git commit -m "fix: corrigir formato multipart do upload de gráficos"
git push
vercel --prod
```

Aguarde o deploy terminar completamente!

---

## 🧪 Teste 1: Verificar Permissões do Slack

### Passo a passo:

1. **Acesse**: https://api.slack.com/apps
2. **Selecione seu app**
3. **OAuth & Permissions** (menu lateral)
4. **Bot Token Scopes** - Verifique se tem:
   - ✅ `chat:write`
   - ✅ `files:write` ⭐ **IMPORTANTE**
   - ✅ `app_mentions:read`

5. **SE ADICIONOU `files:write` AGORA:**
   - Role até o topo da página
   - Você verá: **"Reinstall your app"** (banner amarelo)
   - Clique em **"Reinstall to Workspace"** ⚠️ **OBRIGATÓRIO**
   - Autorize as novas permissões

---

## 🧪 Teste 2: Verificar Token

### No painel do Slack (OAuth & Permissions):

1. Copie o **Bot User OAuth Token** (começa com `xoxb-`)
2. **IMPORTANTE**: Copie o token COMPLETO

### Na Vercel:

1. Vá em: https://vercel.com
2. Selecione seu projeto
3. **Settings** → **Environment Variables**
4. Verifique se `SLACK_BOT_TOKEN` está configurado
5. Se tiver dúvida, **delete e crie novamente**:
   ```
   Nome: SLACK_BOT_TOKEN
   Valor: xoxb-seu-token-completo-aqui
   ```
6. **Redeploy**: `vercel --prod`

---

## 🧪 Teste 3: Testar no Slack

No canal do Slack, digite:

```
@PMO bot estatística de commits
```

### Aguarde e observe:

1. **Relatório textual** aparece ✅
2. Mensagem: "📊 Gerando gráficos..." ✅
3. **Aguarde 5-10 segundos** ⏳
4. **Imagens devem aparecer** 🖼️

---

## 🔍 Teste 4: Ver Logs Detalhados

### No terminal (Git Bash):

```bash
cd "/c/Users/Inteli/Documents/teste de integração"
vercel logs --output raw | grep -A 5 -B 5 "UPLOAD"
```

### Procure por estas mensagens:

#### ✅ **SE FUNCIONOU:**

```
[UPLOAD] Iniciando upload de commits_ranking_...png
[UPLOAD] Tamanho da imagem: 145234 bytes
[UPLOAD] Enviando requisição para https://slack.com/api/files.upload
[UPLOAD] ✅ Upload bem-sucedido!
[UPLOAD] URL do arquivo: https://files.slack.com/...
```

#### ❌ **SE DEU ERRO: "missing_scope"**

```
[UPLOAD] ❌ Erro do Slack: missing_scope
[UPLOAD] 🔑 SOLUÇÃO: Vá em https://api.slack.com/apps
[UPLOAD]    1. OAuth & Permissions
[UPLOAD]    2. Adicione 'files:write' em Bot Token Scopes
[UPLOAD]    3. REINSTALE o app (botão no topo)
```

**SOLUÇÃO**: Você esqueceu de **reinstalar o app** após adicionar `files:write`!

#### ❌ **SE DEU ERRO: "invalid_auth"**

```
[UPLOAD] ❌ Erro do Slack: invalid_auth
[UPLOAD] 🔐 SOLUÇÃO: Token inválido
```

**SOLUÇÃO**: 
1. Copie o token novamente do Slack (OAuth & Permissions)
2. Atualize na Vercel (delete e crie novamente)
3. Redeploy: `vercel --prod`

#### ❌ **SE DEU ERRO: "not_in_channel"**

```
[UPLOAD] ❌ Erro do Slack: not_in_channel
[UPLOAD] 🚪 SOLUÇÃO: Bot não está no canal
```

**SOLUÇÃO**: No canal do Slack, digite:
```
/invite @PMO bot
```

#### ❌ **SE DEU ERRO: "channel_not_found"**

```
[UPLOAD] ❌ Erro do Slack: channel_not_found
```

**SOLUÇÃO**: O ID do canal está errado (isso é raro, geralmente funciona automaticamente)

---

## 🧪 Teste 5: Debug Avançado

### Ver TODOS os logs em tempo real:

No Git Bash:

```bash
cd "/c/Users/Inteli/Documents/teste de integração"
vercel logs --follow
```

Deixe isso rodando e **em outra janela**, teste no Slack:

```
@PMO bot estatística de commits
```

Você verá em tempo real o que está acontecendo!

---

## 📋 Checklist de Verificação

Antes de testar, certifique-se:

- [ ] ✅ Deploy feito com `vercel --prod`
- [ ] ✅ Deploy terminou completamente (sem erros)
- [ ] ✅ Permissão `files:write` adicionada no Slack App
- [ ] ✅ App **REINSTALADO** no workspace (banner amarelo desapareceu)
- [ ] ✅ `SLACK_BOT_TOKEN` configurado na Vercel
- [ ] ✅ Token copiado COMPLETO do Slack (começa com `xoxb-`)
- [ ] ✅ Bot adicionado ao canal (`/invite @PMO bot`)
- [ ] ✅ Testou no Slack e aguardou 5-10 segundos

---

## 💡 Dicas Importantes

### 1. **SEMPRE Reinstale o App**
Sempre que adicionar uma nova permissão (scope) no Slack, você PRECISA reinstalar o app. As permissões só terão efeito após a reinstalação!

### 2. **Aguarde o Deploy**
O deploy na Vercel pode levar 30-60 segundos. Aguarde terminar completamente antes de testar.

### 3. **Token Completo**
O token do Slack é longo (geralmente 50+ caracteres). Certifique-se de copiar TODO o token, incluindo o final.

### 4. **Cache do Slack**
Às vezes o Slack faz cache. Se não funcionar, aguarde 1 minuto e tente novamente.

---

## 🎯 Teste Rápido - 3 Minutos

```bash
# 1. Deploy (1 min)
git add . && git commit -m "fix: upload gráficos" && git push && vercel --prod

# 2. Enquanto o deploy roda:
# - Vá em https://api.slack.com/apps
# - OAuth & Permissions
# - Verifique files:write
# - Se adicionou agora, REINSTALE o app

# 3. Teste no Slack (30 seg)
# Digite: @PMO bot estatística de commits
# Aguarde 10 segundos

# 4. Ver logs (se não funcionou)
vercel logs --output raw | tail -n 100 | grep "UPLOAD"
```

---

## ✅ O que Você Deve Ver (Sucesso)

No Slack, após digitar `@PMO bot estatística de commits`:

```
📊 Análise de Commits - seu-repo

🏆 Top 10 Contribuidores:

1. João Silva
   • Commits: 47 (38.2%)
   • Status: 🔥 Acima da média

...

📊 Gerando gráficos...
```

**Aguarde 5-10 segundos...**

```
[IMAGEM 1 APARECE] 
📊 Ranking de Commits - seu-repo
```

```
[IMAGEM 2 APARECE]
📈 Evolução de Commits (últimos 30 dias)
• Total: 47 commits
• Média/dia: 1.57
• Máximo em 1 dia: 8
```

```
✅ Gráficos enviados com sucesso!
```

---

## 🆘 Ainda Não Funciona?

Se seguiu TODOS os passos acima e ainda não funciona:

1. **Copie a saída dos logs**:
   ```bash
   vercel logs --output raw | tail -n 200 > logs.txt
   ```

2. **Abra `logs.txt` e procure por**:
   - Linhas com `[UPLOAD]`
   - Linhas com `ERROR` ou `Exception`
   - A resposta do Slack (JSON)

3. **Me envie essas linhas** para eu analisar o problema específico.

---

## 🎨 Resultado Esperado

Os gráficos são gerados com Matplotlib e devem aparecer como **imagens PNG** no Slack com:

- **Gráfico 1**: Barras coloridas (verde = acima da média, vermelho = abaixo)
- **Gráfico 2**: Linha azul com área preenchida mostrando evolução

Se você vê isso = **SUCESSO!** 🎉

