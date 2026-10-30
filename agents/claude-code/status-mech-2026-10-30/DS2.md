deepseek-search: перший шматок 0.5 с, усе 97.5 с
УВАГА: пошуків 6 при --uses 4 — сервер ліміт не тримає.
# Контроль, який агент не може вимкнути сам: Claude Code та суміжні інструменти

> Тип питання: **огляд + рішення** (не швидкий факт). Тому нижче — кілька шарів доказів і окремо рекомендація.
> Обмеження: я бачу лише сніпети результатів пошуку, сторінок не відкривав. Частина джерел — дзеркала/перекази офіційної документації; це позначено.
> Ліміт кроків пошуку вичерпано на 4-му запиті, тому **Codex CLI / Gemini CLI / Cursor я не встиг перевірити** — про них див. «Чого не знайшов».

---

## Коротка відповідь

1. **У Claude Code є вбудований шар «protected paths»**, і `.claude/` входить до нього: `permissions.allow` **не може** пре-апрувити запис у ці шляхи, а `deny`-правило перемагає `allow` і спрацьовує навіть у `bypassPermissions` [першоджерело + третя сторона, тест].
2. **Але `deny` на `Edit`/`Write` не зупиняє запис через Bash** (`python3 -c`, `sed -i`, редірект). Це підтверджено незалежним тестом: модель сама сказала «I could write directly via Bash, but that would bypass the prohibition rule» [третя сторона]. Тобто `deny` — це UI-політика для інструментів, не пісочниця.
3. **Справжня межа — managed settings + OS-sandbox**: `managed-settings.json` (root-owned, `/etc/claude-code/`) не перекривається користувацькими файлами; є ключі `allowManagedPermissionRulesOnly`, `allowManagedHooksOnly`; sandbox на Seatbelt/bubblewrap з `filesystem.denyWrite` і `allowUnsandboxedCommands: false` [першоджерело + дзеркало документації].
4. **Хуки — не «поза теками»**, вони реєструються в `settings.json`; тому захист хука = захист файлу налаштувань. Робоча схема: хук у managed settings + `allowManagedHooksOnly: true` + скрипт хука root-owned поза репо [висновок на основі першоджерел].
5. **Хуки fail-open**: на таймауті/помилці інструмент виконується далі — тому хук не можна вважати єдиним бар'єром [третя сторона, з посиланням на docs].
6. **Готового «agent ledger» від Anthropic я не знайшов.** Є примітиви (`SubagentStop` + `agent_transcript_path`, `PostToolUse`, `ConfigChange`, `PermissionDenied`) і сторонні інструменти: `cc-audit` (PyPI, самозахист від видалення), RavenClaude (`hook-events.jsonl`), `cc-safe-setup`, MintMCP Agent Monitor [третя сторона].

---

## Докази

### A. Protected paths і `permissions.deny` у Claude Code

| Твердження | Мітка | URL | Цитата |
|---|---|---|---|
| `allow`-правила не пре-апрувлять запис у protected paths; перевірка йде **раніше** за allow | [першоджерело] | https://code.claude.com/docs/en/permission-modes | «permissions.allow rules in settings files do not pre-approve protected-path writes. The safety check runs before Claude Code evaluates allow rules from settings, so an entry such as `Edit(.claude/**)` in `~/.claude/settings.json` or `.claude/settings.json` does not change the per-mode outcome» |
| `.claude` — protected directory (виняток `.claude/worktrees` і md-файли auto-memory у сесії без `--restricted`) | [першоджерело] | там же | «.claude, except for .claude/worktrees where Claude stores its own git worktrees, and except for the markdown files in Claude's own auto memory directory in a session started without --restricted» |
| `allow`-правило або хук з `allow` **не** можуть апрувити `rm` по critical path | [першоджерело] | там же | «Claude Code never lets a permissions.allow rule or a PreToolUse hook that returns "allow" approve an rm or rmdir command that targets a critical path» |
| У `bypassPermissions` запис у protected path **дозволений** → protected paths не є безпековою межею в цьому режимі | [третя сторона, тест v2.1.248] | https://dev.classmethod.jp/en/articles/claude-code-protect-settings-json-deny-rule-protected-paths/ | «bypassPermissions \| Allowed \| Allowed» (таблиця «Edit / Write to protected paths») |
| `deny` на `.claude/settings.json` блокує `Edit`/`Write` навіть у `bypassPermissions` | [третя сторона, тест] | там же | «As long as this rule is in effect, I cannot rewrite .claude/settings.json.» + «a rule prohibiting editing is included in this settings.json itself, and Edit has been blocked» |
| **Але** `deny` не блокує обхід через Bash | [третя сторона, тест] | там же (JP-версія: https://dev.classmethod.jp/articles/claude-code-protect-settings-json-deny-rule-protected-paths/) | «I could write directly via Bash, but that would bypass the prohibition rule you set, so I won't do it without your permission»; заголовок розділу: «deny するだけでは Bash 経由の操作はブロックできない» |
| `deny`/`allow` для Bash матчаться по **рядку команди** (glob, не regex), тому складені команди ламають правила | [третя сторона, референс-витяг] | https://cdn.jsdelivr.net/npm/cc-safe-setup@29.8.0/SETTINGS_REFERENCE.md | «Compound commands don't match: `Bash(git:*)` won't match `cd /path && git log`» […] «Deny rules have the same compound-command limitation as allow rules. Hooks are more reliable for blocking.» |
| `allowManagedPermissionRulesOnly: true` → правила з user/project/local ігноруються | [третя сторона / дзеркало] | https://mintlify.wiki/anthropics/claude-code/reference/config/settings-json | «allowManagedPermissionRulesOnly \| boolean \| Only permission rules from managed settings are respected» |

### B. Managed settings / policy (шар, який агент не редагує)

| Твердження | Мітка | URL | Цитата |
|---|---|---|---|
| Ніщо у власних файлах чи `--settings` не перекриває managed-ключі | [першоджерело, локалізована версія docs] | https://code.claude.com/docs/zh-CN/settings | «您自己的设置文件或 --settings 中的任何内容都不会覆盖托管键» (= ніщо у ваших файлах налаштувань або `--settings` не перекриває managed-ключі) |
| Managed = `managed-settings.json`, MDM-політика або server-managed з консолі claude.ai | [першоджерело] | https://code.claude.com/docs/it/settings | «Impostazioni gestite, che si tratti di un file managed-settings.json, di una politica MDM o di impostazioni gestite dal server» |
| Файлові шляхи політики: macOS `/Library/Application Support/ClaudeCode/`, Linux/WSL `/etc/claude-code/`, Windows `C:\Program Files\ClaudeCode\`; можна як symlink, політика все одно діє | [дзеркало офіційної документації] | https://github.com/ericbuess/claude-code-docs/blob/main/docs/managed-settings.md | «File-based: managed-settings.json, an optional managed-settings.d/ directory, and managed-mcp.json in the system directory: /Library/Application Support/ClaudeCode/ on macOS, /etc/claude-code/ on Linux and WSL» |
| `managed-settings.d/*.json` мерджаться поверх базового файлу (алфавітно), списки додаються | [дзеркало офіційної документації] | там же | «Claude Code merges managed-settings.json first, then every *.json file in the directory in alphabetical order» |
| Для кількох security-ключів **суворіше** значення з нижчого рівня поважається навіть проти managed (напр. `permissions.blockReadsOutsideWorkingDirectories: true`) | [першоджерело, локалізована версія] | https://code.claude.com/docs/zh-CN/settings | «permissions.blockReadsOutsideWorkingDirectories \| 来自任何作用域的 true \| 即使托管来源设置 false 也被尊重» |
| `allowManagedHooksOnly` / `allowManagedPermissionRulesOnly` / `strictPluginOnlyCustomization` — enterprise-ключі | [третя сторона / дзеркало] | https://mintlify.wiki/VineeTagarwal-code/claude-code/configuration/settings | «allowManagedHooksOnly — only run hooks defined in managed settings; allowManagedPermissionRulesOnly — only use permission rules from managed settings» |
| `disableBypassPermissionsMode: "disable"` існує як ключ | [третя сторона] | https://github.com/affaan-m/ECC/blob/e56c2c1ccd2909c45d0d7d39ae7895d78783fc6c/docs/claude-code-guide/02-permissions.md | «disableBypassPermissionsMode \| Prevent bypass mode activation» |

### C. Sandbox / read-only на рівні ОС (єдине, що реально спиняє Bash)

| Твердження | Мітка | URL | Цитата |
|---|---|---|---|
| Sandbox = Seatbelt (macOS) / bubblewrap (Linux, WSL2) | [першоджерело] | https://code.claude.com/docs/en/sandboxing | «uses Seatbelt for sandbox enforcement» / «Linux: uses bubblewrap for isolation» |
| Permission rules і sandbox — різні шари; sandbox діє лише на Bash/PowerShell/Monitor і дочірні процеси | [першоджерело] | там же | «Permission rules control which tools Claude Code can use and are evaluated before any tool runs.» / «Sandboxing provides OS-level enforcement that restricts what shell commands can access at the filesystem and network level. It applies to Bash, PowerShell, and Monitor tool commands and their child processes.» |
| `sandbox.filesystem.denyWrite`/`denyRead`/`allowWrite`; `failIfUnavailable`; `allowUnsandboxedCommands: false` | [першоджерело] | там же | «failIfUnavailable: a missing dependency such as bubblewrap on Linux blocks Claude Code from starting rather than falling back to unsandboxed execution» / «allowUnsandboxedCommands: false: Claude Code ignores the dangerouslyDisableSandbox escape hatch» |
| `--dangerously-skip-permissions` пропускає і перевірки protected paths | [першоджерело] | там же | «Nothing. Protected path checks are also skipped; the actions no mode auto-approves still apply.» (рядок про `--dangerously-skip-permissions`) |
| Вбудовані `Read/Edit/Write` **не** йдуть через sandbox — тільки через permission system | [третя сторона, цитує docs] | https://raw.githubusercontent.com/cdubiel08/ralph-hero/refs/heads/main/thoughts/shared/research/2026-08-16-claude-code-sandbox-spike.md | «Built-in file tools: Read, Edit, and Write use the permission system directly rather than running through the sandbox.» (з посиланням на code.claude.com/docs/en/sandboxing) |
| Тому sandbox **сам по собі** не робить теку read-only для агента | [третя сторона, експеримент] | там же | «a filesystem sandbox ALONE cannot enforce ralph's read-only investigator invariant. Containment must be sandbox (Bash + subprocesses) PLUS permission deny rules (Edit/Write/NotebookEdit)» |
| За замовчуванням sandbox уже тримає write-denied на `settings.json`, `.claude/skills`, git-метаданих | [третя сторона, аналіз коду] | https://deepwiki.com/cablate/claude-code-research/6.2-filesystem-permissions-sandbox-and-tool-permission-hooks | «denyWrite: Enforces read-only status on settings.json files, the .claude/skills directory, and internal git metadata (HEAD, objects, refs, hooks, config) to prevent RCE via git hooks» |
| Під admin-мандатом sandbox гранти з project/local settings **відкидаються** | [третя сторона, changelog v2.1.285] | https://changelogs.core-directive.com/v/2.1.285/e/sandbox-read-block-withholds-risky-repo-grants | «Under an admin sandbox mandate (managed settings require the sandbox), sandbox.filesystem.allowWrite, Edit allow-rule paths and allowRead paths from project and local settings are dropped» |
| Побитий JSON sandbox деградує **мовчки** (агент необмежений, без попереджень) | [третя сторона, експеримент] | https://raw.githubusercontent.com/cdubiel08/ralph-hero/refs/heads/main/thoughts/shared/research/2026-08-16-claude-code-sandbox-spike.md | «With denyWrite given as a string instead of an array […] touch .../m1.txt → exit 0, file created, no warning on either stream» |
| Хуки, локальні MCP-сервери, status line виконуються з повним доступом користувача (поза sandbox) | [третя сторона, огляд docs] | https://easyspawn.com/blog/claude-code-sandbox | «Hooks, local MCP servers, your status line command run with your full access.» / «A denyRead doesn't stop the Read tool — add a permission deny rule too.» |

### D. Хуки: де живуть і як їх захистити

| Твердження | Мітка | URL | Цитата |
|---|---|---|---|
| Хуки реєструються в `.claude/settings.json` (ключ `hooks`), є `disableAllHooks` | [третя сторона, навчальний огляд] | https://mintlify.wiki/shanraisshan/claude-code-best-practice/concepts/hooks | «Hooks are configured in .claude/settings.json under the hooks key, or in agent/skill frontmatter.» |
| Типи хендлерів: `command`, `http`, `mcp_tool`, `prompt`, `agent` | [третя сторона, «звірено з docs» 2026-06-08] | https://raw.githubusercontent.com/mcorbett51090/RavenClaude/refs/heads/main/plugins/ravenclaude-core/knowledge/claude-code-permissions.md | «A hook entry declares a handler type. The full set is five: command | http | mcp_tool | prompt | agent» |
| Хук `allow` **не** перемагає `deny` у settings | [третя сторона, цитує hooks-guide] | там же | «Returning "allow" skips the interactive prompt but does not override permission rules. If a deny rule matches the tool call, the call is blocked even when your hook returns "allow".» |
| Хуки fail-open на таймауті/помилці | [третя сторона, «звірено з docs»] | там же | «On timeout or connection failure, Claude Code treats the hook as a non-blocking error and the tool proceeds — i.e. fail-open.» |
| Є подія `ConfigChange` (зміна конфігурації) — можна логувати спробу зміни налаштувань | [першоджерело] | https://code.claude.com/docs/en/agent-sdk/hooks.md | «ConfigChange \| No \| Yes \| Configuration file changes \| Reload settings dynamically» |
| Є `InstructionsLoaded` — аудит того, які інструкції завантажились | [першоджерело] | там же | «InstructionsLoaded \| No \| Yes \| A CLAUDE.md or rules file is loaded into context \| Audit which instruction files load» |
| Централізоване обмеження джерел хуків: `allowManagedHooksOnly: true` | [вендор, блог] | https://docs.mintmcp.com/blog/claude-code-hooks | «Managed settings enforcement: Using allowManagedHooksOnly: true to block user-, project-, and non-approved plugin hooks while retaining centrally managed hooks» |
| Історичний клас ризику: project-controlled config виконував код **до** trust-рішення (CVE-2025-59536, виправлено v1.0.111) | [вендор, блог] | там же | «CVE-2025-59536 affected Claude Code versions before 1.0.111 and allowed project-controlled configuration to execute code before the startup trust decision.» |
| Project `allow`-правила застосовуються лише після workspace trust | [першоджерело] | https://code.claude.com/docs/en/permissions | «permissions.allow rules and permissions.additionalDirectories entries in a project's .claude/settings.json grant capability, so Claude Code applies them only after you accept the workspace trust dialog for that folder.» |

### E. Журнал дій агента і збереження результатів під-агентів

| Твердження | Мітка | URL | Цитата |
|---|---|---|---|
| Офіційний примітив для результатів субагентів: `SubagentStop` | [першоджерело] | https://code.claude.com/docs/en/agent-sdk/hooks.md | «SubagentStop \| Yes \| Yes \| Subagent completion \| Aggregate results from parallel tasks» |
| `PostToolUse` прямо призначений для audit trail | [першоджерело] | там же | «PostToolUse \| Yes \| Yes \| Tool execution result \| Log file changes to an audit trail» |
| `SubagentStop` віддає `agent_transcript_path` — можна скопіювати транскрипт субагента | [третя сторона, цитує docs] | https://github.com/johnzfitch/claude-wiki/blob/master/05-Agent-SDK/agent-sdk-hooks.md | «print(f"  Transcript: {input_data['agent_transcript_path']}")» |
| `PermissionDenied` (auto-mode деніали) — окрема подія для логу | [першоджерело] | https://code.claude.com/docs/en/agent-sdk/hooks.md | «PermissionDenied \| No \| Yes \| Auto mode denies a tool call […] \| Log denials» |
| **cc-audit** (PyPI): хук-аудитор з політикою YAML, самозахист файлів аудиту, заборона `cc-audit uninstall` агенту | [третя сторона, open source] | https://pypi.org/project/cc-audit/ | «Self-protection. The defaults treat the auditor's own files as protected: the agent can read audit-policy.yaml and the logs, but a Write/Edit to them, a shell redirect into them, rm -rf .cc-audit, sed -i on the policy, or cc-audit uninstall / pip uninstall cc-audit from inside the session are blocked.» |
| cc-audit за замовчуванням блокує запис у `.claude/settings.json` і власний лог | [третя сторона] | там же | «**/.cc-audit/** # the audit log […] **/.claude/settings.json # where the hook is registered» |
| **RavenClaude** (GitHub-плагін): журнал `hook-events.jsonl`, логує `PermissionDenied` | [третя сторона] | https://raw.githubusercontent.com/mcorbett51090/RavenClaude/refs/heads/main/plugins/ravenclaude-core/knowledge/claude-code-permissions.md | «RavenClaude wires hooks/emit-permission-denied.sh → hook-events.jsonl.» |
| **cc-safe-setup** (npm): інсталятор хуків + `--audit`/`--doctor` | [третя сторона] | https://cdn.jsdelivr.net/npm/cc-safe-setup@29.8.0/SETTINGS_REFERENCE.md | «npx cc-safe-setup --audit  # Check your score» |
| **MintMCP Agent Monitor**: MDM-розповсюдження хуків у Claude Code і Cursor, стрім у SIEM | [вендор] | https://docs.mintmcp.com/blog/claude-code-hooks | «Its documented MDM deployment supports pushing Agent Monitor hooks for Claude Code and Cursor to developer machines» |

---

## Суперечності та розбіжності

1. **«Protected paths захищають `.claude`» vs `bypassPermissions` дозволяє запис.** Обидва з першоджерел/тесту: у `default`/`acceptEdits`/`auto` — питає або йде в класифікатор, у `bypassPermissions` — «Allowed». Отже protected paths — це анти-випадковість, не анти-агент.
2. **«`deny` блокує назавжди» vs обхід через Bash.** Тест показує: `deny` на `Edit` не заважає `python3 -c "...write_text(...)"`. Офіційна документація цього не приховує (правила матчаться по інструменту/рядку команди), але межу часто трактують неправильно.
3. **`cc-safe-setup` стверджує, що `bypassPermissions` «Skip everything including hooks»** — це суперечить іншим джерелам, де хук з `permissionDecision: deny` блокує навіть під bypass, а `deny` спрацьовує в bypass-режимі. Вважаю цей рядок ненадійним.
4. **Managed settings «не перекриваються» vs таблиця винятків**, де суворіше значення з lower-scope поважається проти managed (`blockReadsOutsideWorkingDirectories`, `isolatePeerMachines` тощо). Це не баг, а свідомий «fail-safe» дизайн, але формулювання в маркетингу і в довідці різняться.
5. **Хуки «блокують» vs fail-open.** Блокування гарантоване лише при явному `deny`/exit 2 **у межах таймауту**; інакше — неблокуюча помилка і дія виконується.
6. **Версії/дати різняться**: згадки v2.1.81, v2.1.248, v2.1.257, v2.1.282, v2.1.285 у різних джерелах; дати публікації в сніпетах переважно відсутні → числа не усереднюю і не подаю як «поточні».

---

## Висновок (висновок)

- **Жоден один механізм у Claude Code не є межею безпеки проти самого агента.** Реальна гарантія будується з трьох незалежних шарів, і кожен закриває дірку іншого:
  1. **Permission deny** — закриває інструменти `Edit`/`Write`/`NotebookEdit` (працює навіть у bypass, якщо правило є в файлі);
  2. **Sandbox `filesystem.denyWrite`** — закриває Bash (`python`, `sed`, редіректи);
  3. **OS/контейнер + managed settings** — закриває саме себе: агент не може ні змінити файл політики, ні зняти хук, ні змінити `deny`, бо файли root-owned/read-only, а `allowManagedHooksOnly` + `allowManagedPermissionRulesOnly` відкидають усе, що агент міг би дописати.
- **Хуки — це детектор і аудит, а не бар'єр.** Їхня цінність у тому, що вони дають журнал і миттєву реакцію; їхня слабкість — fail-open і залежність від файлу реєстрації.
- **«Ledger» готового рівня** (як бухгалтерська книга незмінних дій) у екосистемі поки що немає; є набір хуків + сторонні обгортки. Найближче до «ledger» — `cc-audit` (локально) і схема «http-хук → зовнішній колектор» (агент не має доступу до сховища).

---

## Рекомендація (рішення)

Мінімальний робочий стек, у порядку важливості:

1. **Контейнер/VM + непривілейований користувач.** Репо — rw, `~/.claude` і `/etc/claude-code` — **ro-mount або root-owned 0444/0555**. `chmod 444` від самого агента не захищає: як власник файлу він поверне права; захищає лише root-owner або read-only mount. *(висновок)*
2. **`/etc/claude-code/managed-settings.json`** (root-owned) з:
   - `permissions.deny`: `Edit(./.claude/**)`, `Write(./.claude/**)`, `Edit(~/.claude/**)`, `Write(~/.claude/**)`;
   - `permissions.disableBypassPermissionsMode: "disable"`;
   - `allowManagedPermissionRulesOnly: true`, `allowManagedHooksOnly: true`;
   - `sandbox.enabled: true`, `sandbox.failIfUnavailable: true`, `sandbox.allowUnsandboxedCommands: false`, `sandbox.filesystem.denyWrite: [".claude", "~/.claude", "/opt/agent-audit"]`.
   *Позначення: це**рекомендація**, а не цитата; точне розташування ключів (`allowManaged*` — top-level чи в `permissions`) у сніпетах не видно → **звірити зі схемою `settings-reference` перед деплоєм** [не перевірено].*
3. **Хук поза репо**: скрипт `/opt/agent-audit/hook.sh`, root-owned `0755`, зареєстрований **лише** в managed settings; краще — `type: "http"` на зовнішній колектор, щоб навіть читання логів агентом не давало змоги їх підробити [висновок; тип `http` — зі стороннього джерела].
4. **Самоперевірка при старті**: скрипт, що намагається записати в `.claude/settings.json` і **вимагає** помилки; інакше — не запускати сесію. Причина: побитий sandbox-конфіг деградує мовчки (задокументований hazard) [третя сторона].
5. **Аудит**: `cc-audit` як швидкий локальний журнал + власний `PostToolUse`/`SubagentStop` хук, що копіює `agent_transcript_path` у теку поза репо (або `http`-хук у SIEM). Додатково `ConfigChange`-хук як сигнал «хтось чіпав налаштування».
6. **Не покладатися на хуки як єдиний контроль** — через fail-open і через те, що хук-`allow` не скасовує `deny`, але й `deny` не скасовує Bash.

---

## Чого не знайшов

- **OpenAI Codex CLI**: sandbox-режими (`read-only` / `workspace-write` / `danger-full-access`), `[sandbox_workspace_write] writable_roots`, політика approvals, захист `~/.codex/config.toml` — **пошук не встиг виконати** (ліміт кроків). Нічого не стверджую.
- **Gemini CLI**: policy engine / deny-правила, trusted folders, docker/podman sandbox — **не перевірено**.
- **Cursor / Amp / Aider**: механізми «агент не редагує власні правила» — **не перевірено**.
- **Офіційний OpenTelemetry-експорт** Claude Code (`CLAUDE_CODE_ENABLE_TELEMETRY` тощо) — у результатах не з'явився; за моїми попередніми знаннями він існує, але **без URL не наводжу** → [не перевірено].
- **Точне розташування транскриптів сесій/субагентів на диску** — не знайшов першоджерела в сніпетах.
- **Чи є `allowManagedPermissionRulesOnly` top-level ключем** — у сніпетах видно лише назву, не рівень вкладеності.
- **Офіційна назва/наявність «agent ledger»** — не знайшов; схоже, такого продукту в екосистемі Anthropic немає.

## Червоні прапорці

- `deny` на `Edit`/`Write` ≠ заборона запису. Bash-обхід тривіальний (`python3 -c`, `sed -i`, `tee`).
- `bypassPermissions`/`--dangerously-skip-permissions` знімає і protected paths — «захист» стає нульовим.
- Хуки **fail-open**; крім того, вони запускаються з повним доступом користувача (тобто хук — це теж код, який агент теоретично може зламати, якщо має write до його файлу).
- Реєстрація хука живе в `settings.json` → незахищений settings = агент може «вимкнути» аудит, просто відредагувавши/видаливши секцію.
- Побитий/невалідний sandbox-конфіг **не падає з помилкою**, а тихо вимикає обмеження.
- Project-level settings можуть виконувати код до trust-рішення (історичний CVE-2025-59536, виправлено у v1.0.111) — перевіряйте версію.
- Частина «документації» в результатах — дзеркала, wiki та AI-згенеровані огляди (`mintlify.wiki`, `deepwiki`, `core-directive`); вони можуть відставати або перебріхувати. Першоджерелом вважав лише `code.claude.com/docs/*` і GitHub-репо Anthropic.
- Версії в сніпетах (v2.1.2xx) і зміст (Sonnet/Opus-нейми) не збігаються з тим, що я знаю про публічну документацію → **URL у результатах не доказ, що сторінка існує сьогодні**; перед деплоєм звірте живі сторінки.

## [не перевірено]

- Будь-які твердження про Codex CLI, Gemini CLI, Cursor, Aider.
- OpenTelemetry-експорт Claude Code.
- Точний рівень вкладеності `allowManaged*` ключів і повний перелік полів `sandbox.*` (бачив лише фрагменти).
- Твердження RavenClaude про п'ять типів хендлерів і «fail-open» — джерело стороннє, хоч і посилається на docs.
- Твердження `cc-safe-setup` про те, що `bypassPermissions` пропускає хуки — вважаю сумнівним, не підтверджено.
- Дати публікації більшості джерел (у сніпетах `page_age: null`).

> Це питання, схоже, буде повторюватися (політика безпеки для агентів) — варто один раз зафіксувати цей стек у внутрішньому runbook і далі оновлювати лише розділ «інші агенти» та версії.

== Джерела (38):
- Choose a permission mode - Claude Code Docs - defaultMode: "bypassPermissions" or "dontAsk" from your settings files, so a repository’s checked-in settings can’t start a clou... — https://code.claude.com/docs/en/permission-modes?hubs_content=blog.hubspot.com%2Fwebsite%2Ffree-web-design-tools&hubs_content-cta=development-phase&__hstc=129072723.b2d5a836355d1e4385182decf6a7e201.1679308395642.1679308395642.1679308395642.1&__hssc=129072723.1.1679308395642&__hsfp=32358173#what-the-classifier-blocks-by-default#4
- File di impostazioni e precedenza - Claude Code Docs - Documentation Index — https://code.claude.com/docs/it/settings#1
- settings.json を Claude Code 自身に書き換えさせない方法を検証した～deny ルールと保護されたパス（protected paths）について | DevelopersIO — https://dev.classmethod.jp/articles/claude-code-protect-settings-json-deny-rule-protected-paths/#2
- How to Prevent Claude Code from Overwriting settings.json Itself: Verifying Deny Rules and Protected Paths | DevelopersIO - How to Prevent Claude Code from Overwriting settings.json Itself: Verifying Deny Rules and Protected Paths — https://dev.classmethod.jp/en/articles/claude-code-protect-settings-json-deny-rule-protected-paths/#1
- Einstellungsdateien und Priorität - Claude Code Docs — https://code.claude.com/docs/de/settings#1
- Permissions API - Claude Code — https://mintlify.wiki/VineeTagarwaL-code/claude-code/reference/sdk/permissions-api
- ECC/docs/claude-code-guide/02-permissions.md at e56c2c1ccd2909c45d0d7d39ae7895d78783fc6c · affaan-m/ECC - Skip to content — https://github.com/affaan-m/ECC/blob/e56c2c1ccd2909c45d0d7d39ae7895d78783fc6c/docs/claude-code-guide/02-permissions.md#1
- settings.json - Claude Code — https://mintlify.wiki/anthropics/claude-code/reference/config/settings-json
- Settings - Claude Code — https://mintlify.wiki/sanbuphy/claude-code-source-code/configuration/settings#content-area
-  — https://cdn.jsdelivr.net/npm/cc-safe-setup@29.8.0/SETTINGS_REFERENCE.md#1
- All settings - Claude Code Docs - "forceRemoteSettingsRefresh": true — https://code.claude.com/docs/en/settings-reference?m=1&d7430fcd_page=1#18
- 设置文件和优先级 - Claude Code Docs - -p 运行显示无对话框 — https://code.claude.com/docs/zh-CN/settings#2
- All settings - Claude Code Docs - - policyHelper: Claude Code honors it only when the highest source that carries a policy key is an MDM policy or a managed setti... — https://code.claude.com/docs/en/settings-reference?utm_source=bensbites&utm_medium=newsletter&utm_campaign=bb-digest-find-your-files-faster&_bhlid=d1030884e5dca825bb1cc18c29840268bf468af6#managed-settings#18
- Enterprise Features - Claude Code — https://mintlify.wiki/jackdog668/claude-code/advanced/enterprise
- Defense in Depth for Claude Code in the Enterprise — https://www.zenodo.org/records/19464158/files/Claude_Code_Defense_in_Depth.pdf?download=1#1#3#1
- claude-code-docs/docs/managed-settings.md at main · ericbuess/claude-code-docs - Skip to content — https://github.com/ericbuess/claude-code-docs/blob/main/docs/managed-settings.md#1
- Precedence with other managed sources — https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/docs/claude-apps-gateway-config.md#5
- Settings - Claude Code — https://mintlify.wiki/VineeTagarwal-code/claude-code/configuration/settings
- tags:: [[Claude/Code]], [[Diataxis/Explanation]] — https://raw.githubusercontent.com/codekiln/logseq-encode-garden/refs/heads/main/pages/Claude___Code___Settings___Override.md#1
- * **[`policyHelper`](#policyhelper)**: Claude Code honors it only when the highest source that carries a policy key is an MDM po... — https://raw.githubusercontent.com/ericbuess/claude-code-docs/refs/heads/main/docs/settings-reference.md#24
- All settings - Claude Code Docs - - allowWrite and denyWrite: on macOS, wildcards work — https://code.claude.com/docs/en/settings-reference?m=1&trk=article-ssr-frontend-pulse_little-text-block#managed-settings#6
- Configure the sandboxed Bash tool - Claude Code Docs - - In~/ — https://code.claude.com/docs/en/sandboxing#3
- Configure permissions - Claude Code Docs - - Allow rules: apply only when both the requested path and the file it resolves to match — https://code.claude.com/docs/en/permissions?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_recent_activity_details_shares%3BC54KKP8bThyw1I6wtbjoog%3D%3D#3
- Filesystem sandbox as a read-only containment mechanism — spike findings — https://raw.githubusercontent.com/cdubiel08/ralph-hero/refs/heads/main/thoughts/shared/research/2026-08-16-claude-code-sandbox-spike.md#1
- * **Scope**: [`User or managed`](#scopes) — https://raw.githubusercontent.com/ericbuess/claude-code-docs/refs/heads/main/docs/settings-reference.md#9
- The Claude Code Sandbox: Limit What Shell Commands Can Touch — https://easyspawn.com/blog/claude-code-sandbox
- Filesystem Permissions, Sandbox & Tool Permission Hooks | cablate/claude-code-research | DeepWiki - Menu — https://deepwiki.com/cablate/claude-code-research/6.2-filesystem-permissions-sandbox-and-tool-permission-hooks#1
- Repository sandbox file grants are dropped or withheld in more… — https://changelogs.core-directive.com/v/2.1.285/e/sandbox-read-block-withholds-risky-repo-grants
- Intercept dan kontrol perilaku agent dengan hooks - Claude Code Docs — https://code.claude.com/docs/id/agent-sdk/hooks#available-hooks#1
-  — https://code.claude.com/docs/en/agent-sdk/hooks.md
- > ## Documentation Index - > ## Documentation Index — https://code.claude.com/docs/en/agent-sdk/hooks.md#1
- claude-code-docs/docs/agent-sdk__hooks.md at main · ericbuess/claude-code-docs - Skip to content — https://github.com/ericbuess/claude-code-docs/blob/main/docs/agent-sdk__hooks.md#1
- > ## Documentation Index — https://raw.githubusercontent.com/ArcReel/ArcReel/489e21357a87d21f12928addd27acc836b318093/docs/claude-agent-sdk-docs/hooks.md#1
- claude-wiki/05-Agent-SDK/agent-sdk-hooks.md at master · johnzfitch/claude-wiki - Skip to content — https://github.com/johnzfitch/claude-wiki/blob/master/05-Agent-SDK/agent-sdk-hooks.md#1
- Hooks - Claude Code Best Practice — https://mintlify.wiki/shanraisshan/claude-code-best-practice/concepts/hooks
- Claude Code Hooks: Automation Guide | MintMCP Blog — https://docs.mintmcp.com/blog/claude-code-hooks
- cc-audit — https://pypi.org/project/cc-audit/#1
- 2. **A hook `allow` does NOT beat a settings `deny` — https://raw.githubusercontent.com/mcorbett51090/RavenClaude/refs/heads/main/plugins/ravenclaude-core/knowledge/claude-code-permissions.md#3

== Розмова: 20261030-090246 | вх 40128 (з кешу 62976) | вих 16555 | пошуків 6
== Ціна ≈$0.0323 (пік; без вартості пошуків)
