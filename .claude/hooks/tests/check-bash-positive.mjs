#!/usr/bin/env node
// G1: request-brief-reminder-hook.py МАЄ спрацювати (додати additionalContext)
// на Bash-командах, що відтворюють реальну помилку сесії 2026-09-23:
// кілька export + виклик claude без звірки з реальним скриптом.
// Друга команда (через &&) — регресія, знайдена незалежним ревʼю
// (delegate, 2026-09-23): стара regex-версія не бачила export після &&.
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const HOOK = path.join(__dirname, "..", "request-brief-reminder-hook.py");

function runHook(command) {
  const payload = JSON.stringify({ tool_name: "Bash", tool_input: { command } });
  const result = spawnSync("python3", [HOOK], { input: payload, encoding: "utf8" });
  return { status: result.status, out: (result.stdout || "").trim(), err: result.stderr };
}

const positiveCases = [
  [
    [
      'export DEEPSEEK_API_KEY=$(grep -oE "sk-[a-zA-Z0-9]+" ~/AgentReachProject/agent.py | head -1)',
      'export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"',
      'export ANTHROPIC_MODEL="deepseek-v4-flash"',
      'timeout 60 claude -p "тест" --model deepseek-v4-flash',
    ].join("\n"),
    "переноси рядків між export",
  ],
  [
    'export A="1" && export B="2" && claude -p "тест"',
    "export через && (регресія з ревʼю)",
  ],
];

let failed = false;

for (const [command, label] of positiveCases) {
  const { status, out, err } = runHook(command);
  if (status !== 0) {
    console.error(`FAIL [${label}]: hook exited non-zero (${status}): ${err}`);
    failed = true;
    continue;
  }
  if (!out) {
    console.error(`FAIL [${label}]: hook produced no output for a positive (export+claude) command`);
    failed = true;
    continue;
  }
  let parsed;
  try {
    parsed = JSON.parse(out);
  } catch (e) {
    console.error(`FAIL [${label}]: hook output is not valid JSON:`, out);
    failed = true;
    continue;
  }
  const ctx = parsed?.hookSpecificOutput?.additionalContext || "";
  if (!ctx.includes("Ручне відтворення") || !ctx.includes("методологію")) {
    console.error(`FAIL [${label}]: additionalContext missing expected reminder text:`, ctx);
    failed = true;
  }
}

if (failed) {
  process.exit(1);
}

console.log("BASH_POSITIVE_OK");
