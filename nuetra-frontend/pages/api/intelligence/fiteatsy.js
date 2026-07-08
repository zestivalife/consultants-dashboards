import { getFiteatsyIntelligence } from '../../../lib/fiteatsyIntelligence';

export default function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { range = 'month', start, end } = req.query;

  try {
    const payload = getFiteatsyIntelligence({
      range: Array.isArray(range) ? range[0] : range,
      startDate: Array.isArray(start) ? start[0] : start,
      endDate: Array.isArray(end) ? end[0] : end,
    });

    return res.status(200).json(payload);
  } catch (error) {
    return res.status(500).json({
      error: 'Unable to build Fiteatsy intelligence payload',
      detail: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
