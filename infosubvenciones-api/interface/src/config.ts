const requiredEnv = ["VITE_AGENT_ENDPOINT", "VITE_AGENT_BASIC_AUTH_USER", "VITE_AGENT_BASIC_AUTH_PASS"];

requiredEnv.forEach((key) => {
  if (import.meta.env.DEV && !import.meta.env[key]) {
    console.warn(`[env] Missing ${key}. Set it in .env.local for local dev.`);
  }
});

export const config = {
  agentEndpoint: import.meta.env.VITE_AGENT_ENDPOINT as string,
  basicAuthUser: import.meta.env.VITE_AGENT_BASIC_AUTH_USER as string,
  basicAuthPass: import.meta.env.VITE_AGENT_BASIC_AUTH_PASS as string,
  requestTimeoutMs: Number(import.meta.env.VITE_AGENT_TIMEOUT_MS ?? 20000),
  lastUpdated: import.meta.env.VITE_APP_LAST_UPDATED as string | undefined,
};
