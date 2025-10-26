/**
 * Health Check Endpoint
 * GET /api/health
 */

export default function handler(req, res) {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'MCP Custom Server',
    version: '1.0.0'
  });
}

