#!/usr/bin/env node
// G1: request-brief-reminder-hook.py МАЄ спрацювати (додати additionalContext)
// на Bash-команді, що відтворює реальну помилку сесії 2026-09-23:
// кілька export + виклик claude без звірки з реальним скриптом.
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const HOOK = path.join(__dirname, "..", "request-brief-reminder-hook.py");

const command = [
  'export DEEPSEEK_API_KEY=$(grep -oE "sk-[a-zA-Z0-9]+" ~/AgentReachProject/agent.py | head -1)',
  'export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"',
  'export ANTHROPIC_MODEL="deepseek-v4-flash"',
  'timeout 60 claude -p "тест" --model deepseek-v4-flash',
].join("\n");

const payload = JSON.stringify({ tool_name: "Bash", tool_input: { command } });
const result = spawnSync("python3", [HOOK], { input: payload, encoding: "utf8" });

if (result.status !== 0) {
  console.error("FAIL: hook exited non-zero", result.status, result.stderr);
  process.exit(1);
}

const out = (result.stdout || "").trim();
if (!out) {
  console.error("FAIL: hook produced no output for a positive (export+claude) command");
  process.exit(1);
}

let parsed;
try {
  parsed = JSON.parse(out);
} catch (e) {
  console.error("FAIL: hook output is not valid JSON:", out);
  process.exit(1);
}

const ctx = parsed?.hookSpecificOutput?.additionalContext || "";
if (!ctx.includes("Ручне відтворення") || !ctx.includes("методологію")) {
  console.error("FAIL: additionalContext missing expected reminder text:", ctx);
  process.exit(1);
}

console.log("BASH_POSITIVE_OK");
