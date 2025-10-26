/**
 * Trello Cards API
 * GET /api/trello/cards - Listar cards
 * POST /api/trello/cards - Criar card
 */

import https from 'https';

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const apiKey = process.env.TRELLO_API_KEY;
  const token = process.env.TRELLO_TOKEN;
  const boardId = process.env.TRELLO_BOARD_ID;

  if (!apiKey || !token || !boardId) {
    return res.status(500).json({
      error: 'Credenciais do Trello não configuradas'
    });
  }

  try {
    if (req.method === 'GET') {
      // Listar cards
      const cards = await getTrelloCards(apiKey, token, boardId);
      return res.status(200).json(cards);
    }

    if (req.method === 'POST') {
      // Criar card
      const { name, desc, listId } = req.body;
      
      if (!name || !listId) {
        return res.status(400).json({
          error: 'Nome e listId são obrigatórios'
        });
      }

      const card = await createTrelloCard(apiKey, token, {
        name,
        desc,
        idList: listId
      });

      return res.status(201).json(card);
    }

    return res.status(405).json({ error: 'Método não permitido' });

  } catch (error) {
    console.error('Erro:', error);
    return res.status(500).json({
      error: error.message
    });
  }
}

function getTrelloCards(apiKey, token, boardId) {
  return new Promise((resolve, reject) => {
    const path = `/1/boards/${boardId}/cards?key=${apiKey}&token=${token}`;
    
    const options = {
      hostname: 'api.trello.com',
      path: path,
      method: 'GET'
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

function createTrelloCard(apiKey, token, cardData) {
  return new Promise((resolve, reject) => {
    const params = new URLSearchParams({
      key: apiKey,
      token: token,
      name: cardData.name,
      idList: cardData.idList
    });

    if (cardData.desc) {
      params.append('desc', cardData.desc);
    }

    const options = {
      hostname: 'api.trello.com',
      path: `/1/cards?${params.toString()}`,
      method: 'POST'
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

