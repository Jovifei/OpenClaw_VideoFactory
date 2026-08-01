import { timingSafeEqual } from "node:crypto";

import { validateLocalBridgeRequest } from "./bridge_contract.mjs";
import { runOfficialDeviceConnection } from "./official_client.mjs";

function sameSession(expected, received) {
  if (typeof expected !== "string" || typeof received !== "string") return false;
  const expectedBytes = Buffer.from(expected, "utf8");
  const receivedBytes = Buffer.from(received, "utf8");
  return expectedBytes.length === receivedBytes.length && timingSafeEqual(expectedBytes, receivedBytes);
}

async function readRequest() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString("utf8").trim();
  if (text.length === 0 || text.length > 16_384) throw new Error("bridge_request_invalid");
  return JSON.parse(text);
}

function safeFailure(status) {
  return { status, token_present: false, private_key_present: false };
}

async function main() {
  const request = await readRequest();
  const expectedSession = process.env.VIDEO_FACTORY_BRIDGE_SESSION;
  if (!sameSession(expectedSession, request?.session)) return safeFailure("bridge_session_unauthorized");
  const { method } = validateLocalBridgeRequest(request);
  if (method !== "health") return safeFailure("bridge_method_not_active");
  const result = await runOfficialDeviceConnection({ operation: "health" });
  return { ...result, token_present: false, private_key_present: false };
}

try {
  console.log(JSON.stringify(await main()));
} catch {
  console.log(JSON.stringify(safeFailure("bridge_request_failed")));
  process.exitCode = 2;
}
