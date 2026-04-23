import { useMemo } from 'react';

const SESSION_STORAGE_KEY = 'ai_agent_session_id';

function createSessionId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useSessionId() {
  return useMemo(() => {
    const existingSessionId = localStorage.getItem(SESSION_STORAGE_KEY);

    if (existingSessionId) {
      return existingSessionId;
    }

    const sessionId = createSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    return sessionId;
  }, []);
}
