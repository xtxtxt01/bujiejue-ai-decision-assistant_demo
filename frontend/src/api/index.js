const API_BASE = '/api';

async function handleResp(resp) {
  if (!resp.ok) {
    let msg = `请求失败 (${resp.status})`;
    try { const err = await resp.json(); msg = err.detail || msg; } catch {}
    throw new Error(msg);
  }
  return resp.json();
}

export async function register(data) {
  const resp = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResp(resp);
}

export async function login(username, password) {
  const resp = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  return handleResp(resp);
}

export async function registerUser(data) {
  const resp = await fetch(`${API_BASE}/user/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResp(resp);
}

export async function getUserProfile(uid) {
  const resp = await fetch(`${API_BASE}/user/${uid}/profile`);
  return handleResp(resp);
}

export async function createCard(uid, dilemmaType, initialInput, triggerEvent = '', fearedOutcome = '') {
  const resp = await fetch(`${API_BASE}/cards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      uid,
      dilemma_type: dilemmaType,
      initial_input: initialInput,
      trigger_event: triggerEvent,
      feared_outcome: fearedOutcome,
    }),
  });
  return handleResp(resp);
}

export async function getCards(uid) {
  const resp = await fetch(`${API_BASE}/cards?uid=${uid}`);
  return handleResp(resp);
}

export async function getInsights(uid) {
  const resp = await fetch(`${API_BASE}/cards/insights?uid=${uid}`);
  return handleResp(resp);
}

export async function getCardDetail(cardId) {
  const resp = await fetch(`${API_BASE}/cards/${cardId}`);
  return handleResp(resp);
}

export async function sendMessage(cardId, uid, message) {
  const resp = await fetch(`${API_BASE}/cards/${cardId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uid, message }),
  });
  return handleResp(resp);
}

export async function closeCard(cardId, uid, status, decisionResult = '', decisionReason = '') {
  const resp = await fetch(`${API_BASE}/cards/${cardId}/close`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uid, status, decision_result: decisionResult, decision_reason: decisionReason }),
  });
  return handleResp(resp);
}

export async function reopenCard(cardId) {
  const resp = await fetch(`${API_BASE}/cards/${cardId}/reopen`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
  });
  return handleResp(resp);
}

export async function getMemories(uid, type = 'episode', limit = 20) {
  const resp = await fetch(`${API_BASE}/memories?uid=${uid}&type=${type}&limit=${limit}`);
  return handleResp(resp);
}

export async function deleteMemory(uid, type, memoryIds) {
  const resp = await fetch(`${API_BASE}/memories`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uid, type, memory_ids: memoryIds }),
  });
  return handleResp(resp);
}

export async function updateCoreMemory(uid, items) {
  const resp = await fetch(`${API_BASE}/memories/core`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uid, items }),
  });
  return handleResp(resp);
}

// ============ 社区案例 ============

export async function getCommunityCases(type = 'all', limit = 50, offset = 0) {
  const resp = await fetch(`${API_BASE}/cases?type=${type}&limit=${limit}&offset=${offset}`);
  return handleResp(resp);
}

export async function addCaseEmpathy(caseId) {
  const resp = await fetch(`${API_BASE}/cases/${caseId}/empathy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return handleResp(resp);
}

export async function getCardRecommendations(cardId, limit = 3) {
  const resp = await fetch(`${API_BASE}/cases/recommendations?card_id=${cardId}&limit=${limit}`);
  return handleResp(resp);
}

export async function shareCardPreview(cardId, retrospectScore, retrospectText) {
  const resp = await fetch(`${API_BASE}/cards/${cardId}/share/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ retrospect_score: retrospectScore, retrospect_text: retrospectText }),
  });
  return handleResp(resp);
}

export async function shareCardConfirm(cardId, caseData) {
  const resp = await fetch(`${API_BASE}/cards/${cardId}/share/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_data: caseData }),
  });
  return handleResp(resp);
}

