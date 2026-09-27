#!/data/data/com.termux/files/usr/bin/bash
# agent-probe — пробний запуск перед затвердженням плану агента/налаштувань
# (trees/pidrozdil-deepseek.md, 2026-09-27): показує, що РЕАЛЬНО отримує
# сесія, запущена з теки: інструменти, MCP, пам'ять, файли інструкцій,
# хуки, токени на вході. Модель отримує прохання не викликати інструментів.
#
# Використання: tools/agent-probe.sh <тека> [модель]   (типово haiku)
# Коштує один короткий запит (з ліміту підписки Anthropic).
set -u
DIR=$(cd "${1:?вкажи теку}" && pwd) || exit 1
MODEL=${2:-haiku}
OUT=$(mktemp -d "${TMPDIR:-/data/data/com.termux/files/usr/tmp}/agent-probe.XXXXXX")
cd "$DIR" && timeout 180 claude -p "Не використовуй інструментів. Відповідай одним словом: ок." \
  --model "$MODEL" --output-format stream-json --verbose \
  --debug-file "$OUT/debug.log" > "$OUT/stream.jsonl" 2> "$OUT/stderr.txt"
echo "rc=$? · тека: $DIR · модель: $MODEL · сирі дані: $OUT"

python3 - "$OUT" <<'EOF'
import json, os, re, sys, glob, collections
out = sys.argv[1]
init, usage, cost, sid = {}, {}, None, None
for l in open(f"{out}/stream.jsonl"):
    d = json.loads(l)
    sid = sid or d.get("session_id")
    if d.get("subtype") == "init": init = d
    if d.get("type") == "result": usage, cost = d.get("usage", {}), d.get("total_cost_usd")
print("інструменти :", init.get("tools"))
print("MCP-сервери :", [m.get("name") for m in init.get("mcp_servers", [])])
print("пам'ять     :", init.get("memory_paths"))
print("скіли       :", len(init.get("skills", [])), "(зареєстровано; чи в контексті — див. токени)")
files, hooks, mcp_instr = [], collections.Counter(), []
j = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))
for l in open(j[0]) if j else []:
    a = json.loads(l).get("attachment") or {}
    t = a.get("type")
    if t == "instructions": files += [(f.get("type"), f.get("path")) for f in a.get("files", [])]
    elif t and t.startswith("hook_"): hooks[f"{a.get('hookEvent')} ({t})"] += 1
    elif t == "mcp_instructions_delta": mcp_instr += a.get("addedNames", [])
print("файли інструкцій:", len(files), "" if j else "(журнал сесії не знайдено)")
for typ, n in collections.Counter(t for t, _ in files).items(): print(f"   {typ}: {n}")
for typ, p in files:
    if "CLAUDE" in p or "AGENTS" in p or "RULES" in p: print(f"   → {typ}: {p}")
print("інструкції MCP у контексті:", mcp_instr or "немає")
dbg = open(f"{out}/debug.log").read() if os.path.exists(f"{out}/debug.log") else ""
ran = collections.Counter(re.findall(r'Hook (\w+) \([^)]*\) success', dbg))
for l in open(f"{out}/stream.jsonl"):
    d = json.loads(l)
    if d.get("subtype") == "hook_response": ran[d.get("hook_event")] += 1
print("хуки спрацювали:", dict(ran) or "жодного", "| у контекст/користувачу:", dict(hooks) or "нічого")
tok = sum(usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
print(f"вхід: {tok} токенів · ціна за тарифом Claude: ${cost}")
EOF
