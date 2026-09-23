#!/usr/bin/env node
// G2: request-brief-reminder-hook.py МАЄ МОВЧАТИ на звичайних, повсякденних
// Bash-командах — негативна перевірка. Per unlazy: негативний тест без
// позитивного контролю поруч нічого не доводить (може бути, що скрипт
// просто зламаний і завжди мовчить) — тому наприкінці є один позитивний
// контроль (той самий патерн, що й check-bash-positive.mjs), який МАЄ
// спрацювати, інакше цей файл теж провалюється.
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

const negativeCases = [
  ["ls -la", "простий ls"],
  ["git status --short", "git status"],
  ['export FOO="bar"\necho $FOO', "лише один export, без claude"],
  ["cat TROUBLES.md | head -20", "cat+head, без export/claude"],
  [
    'git commit -m "$(cat <<\'EOF\'\nfix: щось\nEOF\n)"',
    "звичайний коміт (heredoc), без export/claude",
  ],
  [
    'export A=1\nexport B=2\necho "два export, але без claude"',
    "два export, немає виклику claude",
  ],
];

let failed = false;

for (const [command, label] of negativeCases) {
  const { status, out, err } = runHook(command);
  if (status !== 0) {
    console.error(`FAIL [${label}]: hook exited non-zero (${status}): ${err}`);
    failed = true;
    continue;
  }
  if (out) {
    console.error(`FAIL [${label}]: hook produced output on a benign command: ${out}`);
    failed = true;
  }
}

// Позитивний контроль — має спрацювати, інакше "мовчання" вище нічого не доводить.
const controlCommand = [
  'export DEEPSEEK_API_KEY=$(grep -oE "sk-[a-zA-Z0-9]+" ~/AgentReachProject/agent.py | head -1)',
  'export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"',
  'claude -p "тест"',
].join("\n");
const control = runHook(controlCommand);
if (control.status !== 0 || !control.out) {
  console.error("FAIL: positive control did not fire — negative results above are not trustworthy");
  failed = true;
}

if (failed) {
  process.exit(1);
}

console.log("BASH_NEGATIVE_OK");
