export const MINIMUM_SCOPES = Object.freeze(["operator.read"]);
export const LOCAL_METHODS = Object.freeze(["health", "session.resolve", "agent.request", "request.status"]);

export function validateLocalBridgeRequest(request) {
  if (!request || typeof request !== "object" || Array.isArray(request)) throw new Error("bridge_request_invalid");
  if (!LOCAL_METHODS.includes(request.method)) throw new Error("bridge_method_forbidden");
  const params = request.params && typeof request.params === "object" && !Array.isArray(request.params) ? request.params : {};
  for (const prohibited of ["tool", "model", "config", "channel", "device", "admin"]) {
    if (Object.hasOwn(params, prohibited)) throw new Error("bridge_privileged_field_forbidden");
  }
  if (request.method === "agent.request" && params.agentId !== "video-factory") {
    throw new Error("bridge_agent_forbidden");
  }
  return { method: request.method, params };
}
