#!/usr/bin/env node
// G3: settings.local.json валідний і Bash-матчер включає
// request-brief-reminder-hook.py (ту саму функцію, не дублікат).
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SETTINGS = path.join(__dirname, "..", "..", "settings.local.json");

let data;
try {
  data = JSON.parse(fs.readFileSync(SETTINGS, "utf8"));
} catch (e) {
  console.error("FAIL: settings.local.json is not valid JSON:", e.message);
  process.exit(1);
}

const preToolUse = data?.hooks?.PreToolUse || [];
const bashEntries = preToolUse.filter((e) => e.matcher === "Bash");
if (bashEntries.length === 0) {
  console.error("FAIL: no PreToolUse entry with matcher 'Bash' found");
  process.exit(1);
}

const hasRequestBrief = bashEntries.some((entry) =>
  (entry.hooks || []).some((h) =>
    typeof h.command === "string" && h.command.includes("request-brief-reminder-hook.py")
  )
);

if (!hasRequestBrief) {
  console.error("FAIL: request-brief-reminder-hook.py is not wired into the Bash matcher");
  process.exit(1);
}

console.log("SETTINGS_WIRING_OK");
