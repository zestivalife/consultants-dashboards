const BASE = "/api/gateway/api/v1/public/consultants";
async function publicRequest(path = "", options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const problem = new Error(
      body?.error?.safe_message || "Marketplace request failed",
    );
    problem.code = body?.error?.code;
    throw problem;
  }
  return body?.data;
}
export function listPublicConsultants(filters = {}) {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.filter(Boolean).forEach((item) => query.append(key, String(item)));
    } else if (value !== "" && value != null) query.set(key, String(value));
  });
  return publicRequest(`?${query}`);
}
export function listFeaturedConsultants(limit = 6) {
  return publicRequest(`/featured?limit=${encodeURIComponent(limit)}`);
}
export function trackHomepageMarketplaceEvent(payload) {
  return publicRequest("/homepage-events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function comparePublicConsultants(slugs = []) {
  const query = new URLSearchParams();
  slugs.forEach((slug) => query.append("c", slug));
  return publicRequest(`/compare?${query}`);
}
export function trackComparisonEvent(payload) {
  return publicRequest("/comparison-events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function getFinderConfig() {
  return publicRequest("/finder/config");
}
export function findConsultants(payload) {
  return publicRequest("/finder/matches", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function trackFinderEvent(payload) {
  return publicRequest("/finder/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export function getPublicConsultant(slug) {
  return publicRequest(`/${encodeURIComponent(slug)}`);
}
export function getPublicAvailability(slug) {
  return publicRequest(`/${encodeURIComponent(slug)}/availability`);
}
export function createPublicEnrolment(slug, payload) {
  const source =
    typeof window !== "undefined"
      ? new URLSearchParams(window.location.search).get("source")
      : null;
  return publicRequest(`/${encodeURIComponent(slug)}/enrolments`, {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      source: source || payload.source || "PUBLIC_CONSULTANT_DIRECTORY",
    }),
  });
}
