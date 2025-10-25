#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const https = require('https');

// Configurações do Trello
const TRELLO_API_KEY = process.env.TRELLO_API_KEY;
const TRELLO_TOKEN = process.env.TRELLO_TOKEN;
const TRELLO_BOARD_ID = process.env.TRELLO_BOARD_ID;

// Configurações do Slack
const SLACK_BOT_TOKEN = process.env.SLACK_BOT_TOKEN;
const SLACK_TEAM_ID = process.env.SLACK_TEAM_ID;

// Configurações do GitHub
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_OWNER = process.env.GITHUB_OWNER;
const GITHUB_REPO = process.env.GITHUB_REPO;

class CustomMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'custom-trello-slack-github-mcp',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // Listar ferramentas disponíveis
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'trello_get_boards',
            description: 'Lista todos os quadros do Trello',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
          {
            name: 'trello_get_cards',
            description: 'Lista todos os cards de um quadro específico',
            inputSchema: {
              type: 'object',
              properties: {
                boardId: {
                  type: 'string',
                  description: 'ID do quadro (opcional, usa o padrão se não fornecido)',
                },
              },
            },
          },
          {
            name: 'trello_create_card',
            description: 'Cria um novo card no Trello',
            inputSchema: {
              type: 'object',
              properties: {
                name: {
                  type: 'string',
                  description: 'Nome do card',
                },
                description: {
                  type: 'string',
                  description: 'Descrição do card',
                },
                listId: {
                  type: 'string',
                  description: 'ID da lista onde criar o card',
                },
              },
              required: ['name'],
            },
          },
          {
            name: 'trello_move_card',
            description: 'Move um card para outra lista',
            inputSchema: {
              type: 'object',
              properties: {
                cardId: {
                  type: 'string',
                  description: 'ID do card',
                },
                listId: {
                  type: 'string',
                  description: 'ID da lista de destino',
                },
              },
              required: ['cardId', 'listId'],
            },
          },
          {
            name: 'trello_delete_card',
            description: 'Deleta um card do Trello',
            inputSchema: {
              type: 'object',
              properties: {
                cardId: {
                  type: 'string',
                  description: 'ID do card a ser deletado',
                },
                cardName: {
                  type: 'string',
                  description: 'Nome do card (alternativa ao cardId)',
                },
              },
              required: [],
            },
          },
          {
            name: 'slack_list_channels',
            description: 'Lista canais do Slack',
            inputSchema: {
              type: 'object',
              properties: {
                limit: {
                  type: 'number',
                  description: 'Número máximo de canais a retornar',
                  default: 50,
                },
              },
            },
          },
          {
            name: 'slack_get_channel_history',
            description: 'Obtém histórico de um canal do Slack',
            inputSchema: {
              type: 'object',
              properties: {
                channelId: {
                  type: 'string',
                  description: 'ID do canal',
                },
                limit: {
                  type: 'number',
                  description: 'Número máximo de mensagens',
                  default: 20,
                },
              },
              required: ['channelId'],
            },
          },
          {
            name: 'slack_post_message',
            description: 'Posta uma mensagem no Slack',
            inputSchema: {
              type: 'object',
              properties: {
                channelId: {
                  type: 'string',
                  description: 'ID do canal',
                },
                text: {
                  type: 'string',
                  description: 'Texto da mensagem',
                },
              },
              required: ['channelId', 'text'],
            },
          },
          {
            name: 'trello_slack_integration',
            description: 'Integração: Cria card no Trello e notifica no Slack',
            inputSchema: {
              type: 'object',
              properties: {
                cardName: {
                  type: 'string',
                  description: 'Nome do card',
                },
                cardDescription: {
                  type: 'string',
                  description: 'Descrição do card',
                },
                listId: {
                  type: 'string',
                  description: 'ID da lista do Trello',
                },
                slackChannelId: {
                  type: 'string',
                  description: 'ID do canal do Slack',
                },
                slackMessage: {
                  type: 'string',
                  description: 'Mensagem para o Slack',
                },
              },
              required: ['cardName', 'slackChannelId'],
            },
          },
          {
            name: 'github_get_repo_info',
            description: 'Obtém informações do repositório GitHub',
            inputSchema: {
              type: 'object',
              properties: {
                owner: {
                  type: 'string',
                  description: 'Proprietário do repositório (opcional, usa o padrão)',
                },
                repo: {
                  type: 'string',
                  description: 'Nome do repositório (opcional, usa o padrão)',
                },
              },
            },
          },
          {
            name: 'github_list_issues',
            description: 'Lista issues do repositório GitHub',
            inputSchema: {
              type: 'object',
              properties: {
                state: {
                  type: 'string',
                  description: 'Estado das issues (open, closed, all)',
                  default: 'open',
                },
                limit: {
                  type: 'number',
                  description: 'Número máximo de issues',
                  default: 20,
                },
              },
            },
          },
          {
            name: 'github_create_issue',
            description: 'Cria uma nova issue no GitHub',
            inputSchema: {
              type: 'object',
              properties: {
                title: {
                  type: 'string',
                  description: 'Título da issue',
                },
                body: {
                  type: 'string',
                  description: 'Descrição da issue',
                },
                labels: {
                  type: 'array',
                  description: 'Labels da issue',
                  items: { type: 'string' },
                },
              },
              required: ['title'],
            },
          },
          {
            name: 'github_list_commits',
            description: 'Lista commits do repositório GitHub',
            inputSchema: {
              type: 'object',
              properties: {
                branch: {
                  type: 'string',
                  description: 'Branch (opcional, usa main)',
                  default: 'main',
                },
                limit: {
                  type: 'number',
                  description: 'Número máximo de commits',
                  default: 20,
                },
              },
            },
          },
          {
            name: 'github_trello_slack_integration',
            description: 'Integração completa: Cria issue no GitHub, card no Trello e notifica no Slack',
            inputSchema: {
              type: 'object',
              properties: {
                issueTitle: {
                  type: 'string',
                  description: 'Título da issue',
                },
                issueBody: {
                  type: 'string',
                  description: 'Descrição da issue',
                },
                cardName: {
                  type: 'string',
                  description: 'Nome do card no Trello',
                },
                cardDescription: {
                  type: 'string',
                  description: 'Descrição do card',
                },
                slackChannelId: {
                  type: 'string',
                  description: 'ID do canal do Slack',
                },
                slackMessage: {
                  type: 'string',
                  description: 'Mensagem para o Slack',
                },
              },
              required: ['issueTitle', 'cardName', 'slackChannelId'],
            },
          },
        ],
      };
    });

    // Handler para chamadas de ferramentas
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'trello_get_boards':
            return await this.getTrelloBoards();
          
          case 'trello_get_cards':
            return await this.getTrelloCards(args.boardId);
          
          case 'trello_create_card':
            return await this.createTrelloCard(args);
          
          case 'trello_move_card':
            return await this.moveTrelloCard(args);
          
          case 'trello_delete_card':
            return await this.deleteTrelloCard(args);
          
          case 'slack_list_channels':
            return await this.listSlackChannels(args.limit);
          
          case 'slack_get_channel_history':
            return await this.getSlackChannelHistory(args);
          
          case 'slack_post_message':
            return await this.postSlackMessage(args);
          
          case 'trello_slack_integration':
            return await this.trelloSlackIntegration(args);
          
          case 'github_get_repo_info':
            return await this.getGitHubRepoInfo(args);
          
          case 'github_list_issues':
            return await this.listGitHubIssues(args);
          
          case 'github_create_issue':
            return await this.createGitHubIssue(args);
          
          case 'github_list_commits':
            return await this.listGitHubCommits(args);
          
          case 'github_trello_slack_integration':
            return await this.githubTrelloSlackIntegration(args);
          
          default:
            throw new Error(`Ferramenta desconhecida: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Erro: ${error.message}`,
            },
          ],
        };
      }
    });
  }

  // Métodos do Trello
  async trelloRequest(endpoint) {
    return new Promise((resolve, reject) => {
      const url = `https://api.trello.com/1${endpoint}?key=${TRELLO_API_KEY}&token=${TRELLO_TOKEN}`;
      
      https.get(url, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        });
      }).on('error', reject);
    });
  }

  async getTrelloBoards() {
    const boards = await this.trelloRequest('/members/me/boards');
    return {
      content: [
        {
          type: 'text',
          text: `📋 Quadros encontrados (${boards.length}):\n\n${boards.map(board => 
            `• ${board.name} (ID: ${board.id})\n  URL: ${board.url}\n  Fechado: ${board.closed ? 'Sim' : 'Não'}\n`
          ).join('\n')}`,
        },
      ],
    };
  }

  async getTrelloCards(boardId = TRELLO_BOARD_ID) {
    const [board, cards, lists] = await Promise.all([
      this.trelloRequest(`/boards/${boardId}`),
      this.trelloRequest(`/boards/${boardId}/cards`),
      this.trelloRequest(`/boards/${boardId}/lists`),
    ]);

    const listMap = {};
    lists.forEach(list => {
      listMap[list.id] = list.name;
    });

    const cardsByList = {};
    cards.forEach(card => {
      const listName = listMap[card.idList] || 'Lista Desconhecida';
      if (!cardsByList[listName]) {
        cardsByList[listName] = [];
      }
      cardsByList[listName].push(card);
    });

    let result = `📋 Quadro: ${board.name}\n📊 Total de cards: ${cards.length}\n\n`;
    
    Object.entries(cardsByList).forEach(([listName, listCards]) => {
      result += `📌 ${listName} (${listCards.length} cards):\n`;
      listCards.forEach(card => {
        result += `  • ${card.name}\n`;
        if (card.desc) {
          result += `    Descrição: ${card.desc.substring(0, 100)}${card.desc.length > 100 ? '...' : ''}\n`;
        }
        if (card.due) {
          result += `    Vencimento: ${new Date(card.due).toLocaleDateString('pt-BR')}\n`;
        }
      });
      result += '\n';
    });

    return {
      content: [
        {
          type: 'text',
          text: result,
        },
      ],
    };
  }

  async createTrelloCard(args) {
    const { name, description = '', listId } = args;
    
    // Se não forneceu listId, pega a primeira lista do quadro padrão
    let targetListId = listId;
    if (!targetListId) {
      const lists = await this.trelloRequest(`/boards/${TRELLO_BOARD_ID}/lists`);
      targetListId = lists[0].id;
    }

    const card = await this.trelloRequest(`/cards`, {
      method: 'POST',
      body: JSON.stringify({
        name,
        desc: description,
        idList: targetListId,
        key: TRELLO_API_KEY,
        token: TRELLO_TOKEN,
      }),
    });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Card criado com sucesso!\n📄 Nome: ${card.name}\n📋 Lista: ${targetListId}\n🔗 URL: ${card.url}`,
        },
      ],
    };
  }

  async moveTrelloCard(args) {
    const { cardId, listId } = args;
    
    const card = await this.trelloRequest(`/cards/${cardId}`, {
      method: 'PUT',
      body: JSON.stringify({
        idList: listId,
        key: TRELLO_API_KEY,
        token: TRELLO_TOKEN,
      }),
    });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Card movido com sucesso!\n📄 Card: ${card.name}\n📋 Nova lista: ${listId}`,
        },
      ],
    };
  }

  async deleteTrelloCard(args) {
    let cardId = args.cardId;
    
    // Se não forneceu cardId, buscar pelo nome
    if (!cardId && args.cardName) {
      const cards = await this.trelloRequest(`/boards/${TRELLO_BOARD_ID}/cards`);
      const card = cards.find(c => c.name.toLowerCase() === args.cardName.toLowerCase());
      
      if (!card) {
        return {
          content: [
            {
              type: 'text',
              text: `❌ Card '${args.cardName}' não encontrado`,
            },
          ],
        };
      }
      
      cardId = card.id;
    }
    
    if (!cardId) {
      return {
        content: [
          {
            type: 'text',
            text: '❌ É necessário fornecer cardId ou cardName',
          },
        ],
      };
    }
    
    // Deletar o card
    const result = await new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.trello.com',
        path: `/1/cards/${cardId}?key=${TRELLO_API_KEY}&token=${TRELLO_TOKEN}`,
        method: 'DELETE',
      };
      
      https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          resolve({ status: res.statusCode, data });
        });
      }).on('error', reject).end();
    });
    
    if (result.status === 200) {
      return {
        content: [
          {
            type: 'text',
            text: '✅ Card deletado com sucesso!',
          },
        ],
      };
    } else {
      return {
        content: [
          {
            type: 'text',
            text: `❌ Erro ao deletar card: ${result.data}`,
          },
        ],
      };
    }
  }

  // Métodos do Slack
  async slackRequest(endpoint, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'slack.com',
        path: `/api${endpoint}`,
        method,
        headers: {
          'Authorization': `Bearer ${SLACK_BOT_TOKEN}`,
          'Content-Type': 'application/json',
        },
      };

      const req = https.request(options, (res) => {
        let responseData = '';
        res.on('data', (chunk) => responseData += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(responseData));
          } catch (e) {
            reject(e);
          }
        });
      });

      if (data) {
        req.write(JSON.stringify(data));
      }
      req.end();
    });
  }

  async listSlackChannels(limit = 50) {
    const response = await this.slackRequest('/conversations.list', 'GET');
    
    if (!response.ok) {
      throw new Error(`Erro do Slack: ${response.error}`);
    }

    const channels = response.channels.slice(0, limit);
    let result = `📋 Canais do Slack (${channels.length}):\n\n`;
    
    channels.forEach(channel => {
      result += `📌 ${channel.name} (ID: ${channel.id})\n`;
      result += `  Membros: ${channel.num_members || 'N/A'}\n`;
      result += `  Privado: ${channel.is_private ? 'Sim' : 'Não'}\n`;
      result += `  Arquivado: ${channel.is_archived ? 'Sim' : 'Não'}\n\n`;
    });

    return {
      content: [
        {
          type: 'text',
          text: result,
        },
      ],
    };
  }

  async getSlackChannelHistory(args) {
    const { channelId, limit = 20 } = args;
    
    const response = await this.slackRequest(`/conversations.history?channel=${channelId}&limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`Erro do Slack: ${response.error}`);
    }

    let result = `📝 Histórico do canal (${response.messages.length} mensagens):\n\n`;
    
    response.messages.forEach(msg => {
      result += `👤 ${msg.user || 'Bot'}: ${msg.text}\n`;
      result += `⏰ ${new Date(parseFloat(msg.ts) * 1000).toLocaleString('pt-BR')}\n\n`;
    });

    return {
      content: [
        {
          type: 'text',
          text: result,
        },
      ],
    };
  }

  async postSlackMessage(args) {
    const { channelId, text } = args;
    
    const response = await this.slackRequest('/chat.postMessage', 'POST', {
      channel: channelId,
      text,
    });
    
    if (!response.ok) {
      throw new Error(`Erro do Slack: ${response.error}`);
    }

    return {
      content: [
        {
          type: 'text',
          text: `✅ Mensagem enviada com sucesso!\n📝 Mensagem: ${text}\n📋 Canal: ${channelId}`,
        },
      ],
    };
  }

  // Integração Trello + Slack
  async trelloSlackIntegration(args) {
    const { cardName, cardDescription = '', listId, slackChannelId, slackMessage } = args;
    
    // Criar card no Trello
    const cardResult = await this.createTrelloCard({
      name: cardName,
      description: cardDescription,
      listId,
    });

    // Enviar notificação no Slack
    const defaultMessage = `🎯 Novo card criado no Trello: **${cardName}**`;
    const slackResult = await this.postSlackMessage({
      channelId: slackChannelId,
      text: slackMessage || defaultMessage,
    });

    return {
      content: [
        {
          type: 'text',
          text: `🚀 Integração Trello + Slack executada com sucesso!\n\n${cardResult.content[0].text}\n\n${slackResult.content[0].text}`,
        },
      ],
    };
  }

  // Métodos do GitHub
  async githubRequest(endpoint, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.github.com',
        path: endpoint,
        method,
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'User-Agent': 'Custom-MCP-Server',
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
      };

      const req = https.request(options, (res) => {
        let responseData = '';
        res.on('data', (chunk) => responseData += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(responseData));
          } catch (e) {
            reject(e);
          }
        });
      });

      if (data) {
        req.write(JSON.stringify(data));
      }
      req.end();
    });
  }

  async getGitHubRepoInfo(args) {
    const owner = args.owner || GITHUB_OWNER;
    const repo = args.repo || GITHUB_REPO;
    
    try {
      const repoInfo = await this.githubRequest(`/repos/${owner}/${repo}`);
      
      let result = `📋 Repositório: ${repoInfo.full_name}\n`;
      result += `🔗 URL: ${repoInfo.html_url}\n`;
      result += `📝 Descrição: ${repoInfo.description || 'Sem descrição'}\n`;
      result += `⭐ Stars: ${repoInfo.stargazers_count}\n`;
      result += `🍴 Forks: ${repoInfo.forks_count}\n`;
      result += `🐛 Issues: ${repoInfo.open_issues_count}\n`;
      result += `📅 Criado: ${new Date(repoInfo.created_at).toLocaleDateString('pt-BR')}\n`;
      result += `🔄 Última atualização: ${new Date(repoInfo.updated_at).toLocaleDateString('pt-BR')}\n`;
      result += `🌿 Linguagem principal: ${repoInfo.language || 'N/A'}\n`;
      result += `🔒 Privado: ${repoInfo.private ? 'Sim' : 'Não'}\n`;

      return {
        content: [
          {
            type: 'text',
            text: result,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Erro ao obter informações do repositório: ${error.message}`);
    }
  }

  async listGitHubIssues(args) {
    const owner = GITHUB_OWNER;
    const repo = GITHUB_REPO;
    const state = args.state || 'open';
    const limit = args.limit || 20;
    
    try {
      const issues = await this.githubRequest(`/repos/${owner}/${repo}/issues?state=${state}&per_page=${limit}`);
      
      let result = `📋 Issues do repositório (${issues.length} encontradas):\n\n`;
      
      if (issues.length === 0) {
        result += '📭 Nenhuma issue encontrada.';
      } else {
        issues.forEach((issue, index) => {
          result += `${index + 1}. 🐛 **${issue.title}**\n`;
          result += `   📝 ${issue.body ? issue.body.substring(0, 100) + '...' : 'Sem descrição'}\n`;
          result += `   👤 Autor: ${issue.user.login}\n`;
          result += `   🏷️ Labels: ${issue.labels.map(l => l.name).join(', ') || 'Nenhuma'}\n`;
          result += `   📅 Criada: ${new Date(issue.created_at).toLocaleDateString('pt-BR')}\n`;
          result += `   🔗 URL: ${issue.html_url}\n\n`;
        });
      }

      return {
        content: [
          {
            type: 'text',
            text: result,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Erro ao listar issues: ${error.message}`);
    }
  }

  async createGitHubIssue(args) {
    const owner = GITHUB_OWNER;
    const repo = GITHUB_REPO;
    const { title, body = '', labels = [] } = args;
    
    try {
      const issue = await this.githubRequest(`/repos/${owner}/${repo}/issues`, 'POST', {
        title,
        body,
        labels,
      });
      
      let result = `✅ Issue criada com sucesso!\n`;
      result += `📝 Título: ${issue.title}\n`;
      result += `🔢 Número: #${issue.number}\n`;
      result += `🔗 URL: ${issue.html_url}\n`;
      result += `👤 Autor: ${issue.user.login}\n`;
      result += `🏷️ Labels: ${issue.labels.map(l => l.name).join(', ') || 'Nenhuma'}\n`;

      return {
        content: [
          {
            type: 'text',
            text: result,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Erro ao criar issue: ${error.message}`);
    }
  }

  async listGitHubCommits(args) {
    const owner = GITHUB_OWNER;
    const repo = GITHUB_REPO;
    const branch = args.branch || 'main';
    const limit = args.limit || 20;
    
    try {
      const commits = await this.githubRequest(`/repos/${owner}/${repo}/commits?sha=${branch}&per_page=${limit}`);
      
      let result = `📋 Commits do repositório (${commits.length} encontrados):\n\n`;
      
      if (commits.length === 0) {
        result += '📭 Nenhum commit encontrado.';
      } else {
        commits.forEach((commit, index) => {
          result += `${index + 1}. 📝 **${commit.commit.message.split('\n')[0]}**\n`;
          result += `   👤 Autor: ${commit.commit.author.name}\n`;
          result += `   📅 Data: ${new Date(commit.commit.author.date).toLocaleString('pt-BR')}\n`;
          result += `   🔗 SHA: ${commit.sha.substring(0, 7)}\n`;
          result += `   🔗 URL: ${commit.html_url}\n\n`;
        });
      }

      return {
        content: [
          {
            type: 'text',
            text: result,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Erro ao listar commits: ${error.message}`);
    }
  }

  // Integração completa GitHub + Trello + Slack
  async githubTrelloSlackIntegration(args) {
    const { issueTitle, issueBody = '', cardName, cardDescription = '', slackChannelId, slackMessage } = args;
    
    try {
      // 1. Criar issue no GitHub
      const issueResult = await this.createGitHubIssue({
        title: issueTitle,
        body: issueBody,
      });

      // 2. Criar card no Trello
      const cardResult = await this.createTrelloCard({
        name: cardName,
        description: cardDescription,
      });

      // 3. Enviar notificação no Slack
      const defaultMessage = `🚀 Nova issue criada: **${issueTitle}**\n📋 Card criado: **${cardName}**`;
      const slackResult = await this.postSlackMessage({
        channelId: slackChannelId,
        text: slackMessage || defaultMessage,
      });

      return {
        content: [
          {
            type: 'text',
            text: `🎉 Integração completa executada com sucesso!\n\n${issueResult.content[0].text}\n\n${cardResult.content[0].text}\n\n${slackResult.content[0].text}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Erro na integração completa: ${error.message}`);
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('MCP Customizado Trello + Slack + GitHub iniciado!');
  }
}

// Iniciar servidor
const server = new CustomMCPServer();
server.run().catch(console.error);
