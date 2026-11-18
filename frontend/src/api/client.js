/**
 * REST API Client for Estate Intelligence AI Backend
 * Never exposes or hardcodes any OpenRouter API key in frontend source code.
 */

const API_BASE = import.meta.env?.VITE_API_BASE_URL || '';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchSources(sourceFilter = null, searchQuery = '') {
  const params = new URLSearchParams();
  if (sourceFilter && sourceFilter !== 'ALL') params.set('source', sourceFilter);
  if (searchQuery) params.set('search', searchQuery);
  const res = await fetch(`${API_BASE}/api/sources?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch sources: ${res.status}`);
  return res.json();
}

export async function sendChatMessage({ message, history = [], sourceFilter = null, customOpenRouterKey = '' }) {
  const headers = { 'Content-Type': 'application/json' };
  if (customOpenRouterKey && customOpenRouterKey.trim()) {
    headers['X-OpenRouter-Key'] = customOpenRouterKey.trim();
  }
  const payload = {
    message,
    history,
    source_filter: sourceFilter === 'ALL' ? null : sourceFilter,
    top_k: 8,
  };
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Chat API Error (${res.status}): ${errText}`);
  }
  return res.json();
}
