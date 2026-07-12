import { getFrontendVersion } from '../../lib/buildVersion';

export default function handler(_req, res) {
  res.status(200).json(getFrontendVersion());
}
