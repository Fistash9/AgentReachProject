<!-- Пошук DeepSeek (tools/deepseek-search.py --uses 4), 2026-10-16, ≈$0.0123, рішення користувача «Так, у фоні + бектест». Звірено claude-code: code.claude.com/docs/en/memory.md:24 «context, not enforced configuration… use a PreToolUse hook» і :46 «Claude makes the same mistake a second time» — ТАК (curl). ETH 2602.11988 — уже в TROUBLES:3538. Решта — як позначив пошук. -->
deepseek-search: перший шматок 0.6 с, усе 59.8 с
УВАГА: пошуків 5 при --uses 4 — сервер ліміт не тримає.
Почну з розбиття на підпитання й паралельних пошуків: (A) реальна практика — CLAUDE.md/AGENTS.md журнали помилок з числами; (B) arXiv — Reflexion/пам'ять про помилки й перенесення між сесіями; (C) автоматичні механізми — хуки, лінтери транскриптів, LLM-суддя; (D) критика й негативний досвід.# Журнали помилок поведінки AI-агентів: чи зменшують повтори?

## Коротка відповідь

**Практика поширена і добре задокументована; доказів, що саме вона зменшує повтори саме помилок ПОВЕДІНКИ (а не виконання завдань), у числах "до/після" я майже не знайшов.** Що є:
- Офіційна документація Anthropic прямо рекомендує дописувати в CLAUDE.md після **другої** такої самої помилки агента — але застерігає, що CLAUDE.md це «контекст, а не примусова конфігурація».
- Найсильніші числа, які я знайшов (38,1% → 69% успіху PR), стосуються **команд збірки/тестів**, а не повторів поведінкових помилок — і це зміна + доступ до мережі одночасно.
- Академічні дані (Reflexion) — реальні, але вони про **замикання в межах одного класу завдань** з обмеженим вікном пам'яті (1–3 рефлексії), а не про перенесення «уроків» між довільними сесіями.
- Незалежне дослідження (ETH, цитоване у двох місцях) показує, що **написані руками контекст-файли дають лише ~+4%**, машинно-згенеровані — **погіршують** результат, і обидва **+20% до вартості**. Тобто ефект малий і може бути негативним.
- Найпереконливіший механізм — **автоматичні хуки/гейти**, а не текст у пам'яті: прикладів інструментів багато (self-critic, capt-hook, proof-of-done, crucible), і саме вони ловлять повтор без участі людини.

Далі — доказова база, розбита на 4 підпитання. Позначки: **[першоджерело]** (репо/офіц. дока/arXiv), **[третя сторона]** (блог/стаття), **[не перевірено]**.

---

## Докази

### 1) Практика та репозиторії/пости

**1.1. Anthropic Claude Code Docs — офіційна рекомендація вести журнал помилок у CLAUDE.md** · [першоджерело] · https://code.claude.com/docs/zh-CN/memory
> «将 CLAUDE.md 视为您写下本来需要重新解释的内容的地方... 在以下情况下添加到它：**Claude 第二次犯同样的错误** ... 您在聊天中输入的相同更正或澄清是您上一个会话中输入的»
І важливе застереження:
> «两者都在每次对话开始时加载。Claude 将它们视为**上下文，而不是强制配置**。要阻止某个操作，无论 Claude 决定什么，请改用 **PreToolUse hook**。»
(У підрахунку: Claude Code має два шари — CLAUDE.md, який пише людина, і «авто-пам'ять», яку пише сам Claude; авто-пам'ять лімітована «першими 200 рядками або 25KB» на сесію.)

**1.2. ctoth/claude-failures — публічний журнал провалів агента** · [першоджерело] · дата у файлі 2026-04-05 · https://raw.githubusercontent.com/ctoth/claude-failures/refs/heads/master/2026-04-05-ignored-every-instruction.md
Заголовок: «Failure: Ignored Every Instruction in CLAUDE.md». Це **негативний досвід** у чистому вигляді — журнал фіксує, що агент проігнорував CLAUDE.md цілком:
> «The agent treated CLAUDE.md as something it read once and then forgot. Instructions were acknowledged in principle but never applied in practice.»
> «Zero uses of DOING/EXPECT/IF YES/IF NO across the entire session»
Тобто наявність файлу ≠ виконання. Це прямий контрприклад до тези «запис у журнал вирішує повтори».

**1.3. xda-developers — MISTAKES.md (12 рядків)** · [третя сторона] · https://www.xda-developers.com/coding-agent-kept-making-mistake-12-line-file-taught-it-not-to/
Опис практики з поясненням механізму:
> «The agent would follow it for that session. The next time I gave it a similar task, it would make the same mistake again.»
> «Correcting a coding agent doesn't modify the underlying model... your correction becomes additional context... a new session starts without that context unless the information has been saved and retrieved.»
> «AGENTS.md makes instructions persistent, though it still cannot enforce them... **adding every correction to AGENTS.md eventually creates the same problem. The file becomes another long collection of instructions** that the model has to process.»
Тут немає числа повторів до/після — лише опис, що «це працює» суб'єктивно. Мітка: досвід автора, без метрик.

**1.4. Steve Kinney — «Patterns: Keeping Context Useful» (найсильніше число, з застереженнями)** · [третя сторона] · https://stevekinney.com/courses/ai-development-setup/patterns-for-keeping-context-useful
> «Stephen Toub's report on ten months of running GitHub's coding agent against dotnet/runtime measured **pull request success at 38.1% before their setup changes and 69% after**. The main change wasn't a better model. It was **writing down which commands to run, in what order, and what to expect**.»
> «Two caveats on the number. The team made two changes at once—the instructions file and network access to package feeds—and it's one repository with an unusually complicated build.»
**Важливо:** це про тести/збірку, а не про журнал поведінкових помилок. Первинний звіт (Toub) я не відкривав — **[не перевірено]** як першоджерело.

**1.5. SIOS Tech Lab — «перетворити помилки Claude Code на баг-тікети»** · [третя сторона] · https://tech-lab.sios.jp/archives/52066
> «教訓ファイルはバグチケット... 永続的なナレッジとして積み上げるのではなく、改修したら消す。» («Урок-файл = баг-тікет... не накопичувати як вічне знання, а видаляти після виправлення»). Мотив — дежавю «знову ця сама помилка». Числа не наводяться.

**1.6. Steve Kinney про progress-файли (фіксація «що не спрацювало»)** · [третя сторона] · той самий URL
> «The failures are the most valuable part... The useful version records the dead ends with the reason: "tried moving the query into the parent component; it broke the suspense boundary, reverted." Without that, every fresh session rediscovers the same dead end, **which is the most common way long runs waste money**.»

**1.7. langwatch — скіл `/learn`, що оновлює AGENTS.md** · [першоджерело] · https://raw.githubusercontent.com/langwatch/langwatch/.../.claude/skills/learn/SKILL.md
> «Learn from mistakes by updating AGENTS.md. Use when a mistake was made that should be prevented in future sessions.»
Процес: проаналізувати помилку → «Common Mistake» vs «Correct Behavior» → оновити AGENTS.md.

**1.8. swift-code-reviewer-skill — порогова евристика «≥2 = патерн»** · [першоджерело] · https://cdn.jsdelivr.net/npm/swift-code-reviewer-skill@1.4.0/references/agent-loop-feedback.md
> «A single instance of a mistake is a slip. Two is a pattern. Three or more means the agent's instructions are silent on the topic and need an explicit rule.» Таблиця: «2 → Recurring pattern. Suggest a rule. 3+ → Strong signal.»

**1.9. shenxingy/Clade — PROGRESS.md з розділом Lessons по кожній фазі** · [першоджерело] · https://github.com/shenxingy/Clade/blob/.../PROGRESS.md
Приклад: «Code review after implementation caught 4 real bugs including an infinite loop — do it every time»; «Stuck-retry guard: [STUCK-RETRY] prefixed tasks must NOT be re-queued on second stuck — prevents infinite loops». Це саме «lessons learned» лог, але доказів зменшення повторів немає.

**1.10. yologdev/yoyo-evolve — memory/learnings.jsonl** · [першоджерело] · https://raw.githubusercontent.com/yologdev/yoyo-evolve/.../memory/learnings.jsonl
Машинозчитуваний журнал уроків (`{"type": "lesson", "day": 38, ...}`): «Documenting a footgun in CLAUDE...». Цікава деталь — уроки посилаються один на одного («There's a stronger version of the Day 30 facade rule»).

**1.11. HN-коментар (практика «змусити Codex підсумувати помилки сесії»)** · [третя сторона] · https://althacker.news/item?id=47113137
> «It will often do the same mistakes over and over (e.g. trying to SSH without opening a bastion...). Once you have a sense for all the repeated failure points... add them to future plan files.»
> «An approach that's worked fairly well is asking Codex to summarize mistakes made in a session [and] use the lessons learned to modify the AGENTS.md file for future agents»

**1.12. harness-starter-kit (docs/failures як «постійна пам'ять»)** · [не перевірено] (через GeekNews) · https://tr.news.hada.io/topic?id=30190
> «docs/decisions, docs/failures tabanlı kalıcı hafıza... drift / structure / failure memory check script'leri... Gerçek dogfood repo ve effectiveness report örnekleri»

---

### 2) Дослідження (arXiv): чи переносяться уроки/рефлексія між сесіями

**2.1. Reflexion (Shinn et al., 2023) — arXiv:2303.11366** · [першоджерело] · https://arxiv.org/abs/2303.11366 (текст: browse.arxiv.org/pdf/2303.11366)
> «we show that several of these concepts can be enhanced with **self-reflection to build a persisting memory of self-reflective experiences** which allows an agent to identify its own errors and self-suggest lessons to learn from its mistakes over time.»
Архітектура: Actor + Evaluator + Self-Reflection; короткострокова (trajectory) + довгострокова (episodic buffer) пам'ять.
> «In this study, we limit long-term memory to a **sliding window with maximum capacity** [typically Ω = 1–3 experiences]... we encourage future work to extend the memory component... with more advanced structures such as vector embedding databases»
Результати ALFWorld (через аналіз ksmooi/agentic_ai_lab) · [першоджерело репо-конспекту] · https://github.com/ksmooi/agentic_ai_lab/blob/.../papers/agent/reflexion.md
> «After 10 trials, Reflexion achieves a success rate of approximately 90%, compared to around 70% for ReAct alone.»
> «hallucination errors... ~20% of failures... By the 10th trial, hallucination errors drop to ~5%, and inefficient planning errors drop to ~3%.»
**Ключове обмеження:** це ітерації в межах ОДНОГО завдання/класу завдань (той самий середовище, той самий task), а не перенесення між різними сесіями розробки.

**2.2. Self-Refine (Madaan et al., 2023) — arXiv:2303.17651** · [першоджерело, згадане в конспекті] — контрольна межа: **немає** епізодичної пам'яті, «❌ 不保留» між сесіями. https://cdn.jsdelivr.net/npm/aiwg@2026.8.27/docs/references/REF-021-reflexion-verbal-reinforcement.md (таблиця порівняння)

**2.3. Multi-Agent Reflexion (MAR) — arXiv:2512.20845** · [першоджерело] · https://ar5iv.labs.arxiv.org/html/2512.20845
Спроба покращити Reflexion через багатоагентність у reasoning; цитує Shinn та Self-Refine. (Я не витягнув конкретних чисел з фрагмента.)

**2.4. Де це НЕ працює — «superstition» і memory rot** · [першоджерело, PDF-збірка] · https://release-assets.githubusercontent.com/...aiefs-vol5-agents.pdf
> «The agent already succeeds on the first try. The failure is external (network down, tool broken) - **reflection on "the network was down" does not help future runs. The reflection turns into superstition** - storing a narrative about a one-off flaky run.»
> «2026 pitfall: **memory rot. Reflections accumulate; some are obsolete or wrong; re-runs get slower as the episodic buffer grows.** Mitigation: periodic compaction, TTL on reflections, or a separate sleep-time cleanup agent.»
Також у тому ж джерелі пряма відповідь на ваше питання про «LLM-суддю як єдине джерело»:
> «Self-evaluator ("LLM-as-judge on own trace") — **Lower-signal fallback when no ground truth** — pair with tool-grounded verification.»
І теза, що Claude Code `/memory`, а LangGraph/Letta «externalize the episodic buffer as a markdown file».

---

### 3) Автоматичні механізми, що ловлять повтор класу помилки раніше за людину

**3.1. nadimtuhin/claude-code-self-critic — «deterministic-first + LLM veto»** · [першоджерело] · https://github.com/nadimtuhin/claude-code-self-critic
> «**Stop Hook (Self-Critic)** — Extracts evidence from the transcript... If claims are unbacked by evidence, it blocks the turn... Escalates to a Haiku veto only to suppress false positives — Haiku never writes the critique.»
> «**PreToolUse Stuck-Detector** — Detects when the same flag-normalized command or file target is **repeated 3+ times**.»
> «The key insight: don't let the LLM write the critique... The LLM is a tiebreaker, not the author.» (40 тестів, нуль залежностей)

**3.2. proof-of-done (PyPI) — Stop-хук, що ловить непідтверджені заяви** · [першоджерело] · https://pypi.org/project/proof-of-done/
Приклади заяв: `tests_passed`, `build_passed`, `lint_clean`, `typecheck_clean`, `deployed`, `fixed`. Механізм «anchor → candidates → verdict», закритий набір причин: `supported / no_command / stale / failed_exit / failed_output / empty_run / masked_inconclusive / background_only`. Приклад блокування:
> «the last test run `uv run pytest -q` at step 2 was **before your edit** to `src/app/parser.py` at step 4.»

**3.3. capt-hook (PyPI) — мінінг транскриптів → PR з хуком** · [першоджерело] · https://pypi.org/project/capt-hook/8.10.0/
> «captain-hook mines your transcripts for **the corrections you keep giving** and opens PRs that turn each one into a typed, tested Python hook.»
> «You've typed "use uv, not pip" in a dozen sessions, and session thirteen makes the same mistake... once a **pattern proves itself across sessions** — opens a PR that codifies it as a hook.» (Умова, сесійний reviewer, lifecycle.)

**3.4. crucible-ci (npm) — регресійний CI для конфігурації `.claude/`** · [першоджерело] · https://socket.dev/npm/package/crucible-ci
> «Treat your .claude/ (skills, subagents, hooks, CLAUDE.md) as code under test -- **deterministic + LLM-judge assertions, baselines, transcript diffs**...»
> «Record a run once, replay it forever: --record ... --replay ... no claude calls at all.» + `crucible bisect` для пошуку коміту, що зламав сценарій. (Статус: «v0.1 -- alpha», LLM-judge на roadmap.)

**3.5. netresearch/retro-skill — 3-шарова детекція, включно з крос-сесійною** · [першоджерело] · https://raw.githubusercontent.com/netresearch/retro-skill/main/README.md
> «Mechanical pre-pass (layer A)... parses the transcript for exactly **18 deterministic signals**...»
> «LLM enrichment (layer B) — adds **14 inferential signals** (wrong skill choice, skill capability gap, hallucination, convention violation... **repeated mistake**...)
> «Cross-session enrichment (layer C, optional) — scans ~/.claude/projects/... across projects... **5 signals: same-friction-again, cross-project pattern, memory drift, ineffective skill update, follow-up-fix session**»
Ключова думка про призначення: «before asking where to *store* a learning, retro asks **who should own the truth**» — тобто механічні перевірки → у `checkpoints.yaml`/хуки, а не в текст.

**3.6. Claude Code Docs — повний набір хуків як «примус»** · [першоджерело] · https://code.claude.com/docs/en/hooks-guide
> «Use as type: "agent" hooks... spawn a subagent that can read files, search code... verify conditions before returning a decision.» (приклад: «Verify that all unit tests pass. Run the test suite and check the results.»)
Важливі обмеження: «**PostToolUse hooks can't undo actions** since the tool has already executed»; «Stop hooks fire whenever Claude finishes responding, not only at task completion»; «Text returned via additionalContext is injected as a system reminder that Claude reads as plain text.» — тобто навіть хук-контекст не є жорстким кодом.

**3.7. @houtini/metacog (npm) — «7 senses» + motor learning** · [першоджерело] · https://www.npmjs.com/package/@houtini/metacog
> «Nociception | Error friction | **Repeated similar errors, the agent is stuck**»; «Vestibular | Action diversity | Repeated identical actions, going in circles»
> «Layer 3: Motor Learning (cross-session) When a nociceptive event resolves, the system extracts what changed... persisted as a **behavioural lesson** and injected into future sessions.»
Та чесне про пастку decay-системи: «Standard time-decay actively punishes success. If the agent learns "don't retry the same error three times" and stops doing it, the decay system **sees the rule going stale and prunes it**» (вони інвертують це через «suppressions»).

**3.8. AI Agent Discipline Linter (GitHub Marketplace) — «Mulahazah» інстинкти з порогами** · [першоджерело] · https://github.com/marketplace/actions/ai-agent-discipline-linter
> «Hooks capture every tool call. After ~20 observations Claude analyzes patterns and creates instincts with confidence scores: silent below 0.5, suggested at 0.5–0.69, auto-applied at 0.7+. Corrections drop confidence by 0.1; unused instincts decay.»
Та прив'язка до 5 modes failure, де «Forgotten lessons» = «Next session starts from zero — prior corrections, decisions, instincts are lost; **the same mistake repeats next week**» → Law 5 (Reflect), Law 7 (Learn).

**3.9. Everything Claude Code — огляд життєвого циклу хуків** · [першоджерело] · https://mintlify.wiki/affaan-m/everything-claude-code/concepts/hooks
Перелік подій: PreToolUse / PostToolUse / Stop / SessionStart / SessionEnd / PreCompact, з прикладами (secret detection, type-check після Edit, аудит змінених файлів у Stop, «Extract patterns for continuous learning» у SessionEnd).

---

### 4) Критика й негативний досвід

**4.1. ETH Zurich (через Andela) — рукописний контекст дає ~+4%, машинний — гірше** · [третя сторона, цитує дослідження — первинне джерело не перевірено] · https://www.andela.com/publication/context-rot-the-silent-cause-of-ai-agent-failure
> «A study published by ETH Zurich evaluated the utility of developer-written context files using a benchmark of 138 tasks across 12 repositories. **Developer-written context files improved task completion by roughly 4%. Machine-generated context degraded performance by 0.5% to 2% compared to providing no context at all. Both approaches increased inference costs by over 20%.**»
> «while agents reliably follow explicit instructions in context files, **repository overviews... do not improve performance even when completely accurate**.»
Плюс власний скан автора:
> «The final scan across 15 repositories and 23 context files yielded... **110 falsifiable claims checked, 18 false claims identified, 58 unverifiable claims, 83.6% accuracy rate**... All 18 false claims resided in a single repository... Documentation decay is not a slow, uniform process. **It is event-driven.**»
Первинна ETH-стаття — **[не перевірено]** (я не відкривав Pdf; цифри подані однаково в Andela і Bruin, що підвищує довіру, але це переказ).

**4.2. Bruin Academy — той самий висновок, стисло** · [третя сторона] · https://getbruin.com/learn/sql-ai-beginner/fix-the-context/
> «Research on agent-context files found that **careful, human-written notes improve task success by only a few percent**, and that machine-generated context can **make results worse while adding around 20 percent to cost**. So context is not automatically good... **A long, generic AGENTS.md is worse than a short, sharp one.**»

**4.3. «Кожен доданий урок = додатковий шум ⇒ та сама проблема знову»** · [третя сторона] · xda (див. 1.3)
Ключова критика: «Adding every correction to AGENTS.md eventually creates the same problem.» Модель слабше використовує інформацію в середині довгого контексту (lost-in-the-middle) — і саме журнал помилок розростається в такий контекст.

**4.4. Context rot: документація гниє, і агент цього не повідомляє** · [третя сторона] · Andela
> «Agents do not get confused. That is a feature, but it also removes the **historical feedback loop that kept documentation accurate**. Engineers... observing OpenAPI specifications rotting quietly because routing agents never complain about discrepancies.»

**4.5. Cole Medin (через конспект ai-wiki) — «кожен новий урок = баласт»** · [третя сторона] · https://github.com/tim-kaa-py/ai-wiki/commit/e6627e8...
> «**Less context is more, and increasingly so.** As models get more capable, generic instruction hurts... Keep global rules under ~200 lines... Restrict them to project-specific constraints...»
> «Never escalate the model mid-task... Swapping Sonnet → Opus inside a struggling conversation does not rescue it; **the accumulated bias and errors carry over regardless of model**.»
> «Never let the writer approve the work... self-review returns "looks great" for work that isn't.»

**4.6. Уроки ≠ примусові правила (повторний акцент)** — див. 1.1 (дока) і 1.2 (реальний провал ctoth): файл прочитаний, але проігнорований.

---

## Суперечності (не усереднюю)

| Твердження A | Твердження B | Джерела |
|---|---|---|
| Контекст/журнал помилок дає великий приріст: PR success 38,1% → 69% | Journal/контекст дає лише ~+4%, а машинний — **мінус** 0,5–2% | A: [третя сторона] Steve Kinney (цитує Toub, dotnet/runtime) · B: [третя сторона] Andela/Bruin (цитує ETH Zurich) |
| AGENTS.md/CLAUDE.md достатньо, щоб агент «навчився» | Офіц. дока каже «Claude 将它们视为**上下文，而不是强制配置**»; [першоджерело] со3сяться на PreToolUse hook | A: xda, HN · B: [першоджерело] code.claude.com/docs |
| Reflexion різко покращує (75%→90%, hallucination 20%→5%) | Reflexion чутливий до «superstition» та memory rot; LLM-self-judge — «lower-signal fallback» | A: [першоджерело] arXiv:2303.11366 / конспект · B: [першоджерело] aiefs-vol5 pdf |
| Файл журналу сам «попереджає» повтори | Модель слабшає на середині довгого контексту; кожен новий урок додає шум | A: багато блогів · B: [третя сторона] xda, Andela, ai-wiki |
Метрики з статті Kinney (PR success) не порівнюванні напряму з ETH-метрикою (task completion) — це різні метрики й різні репозиторії, тому зводити в одну не можна.

---

## Висновок (висновок)

1. **Практика журналів помилок — реальна й поширена** (CLAUDE.md «додай, коли Claude схибив двічі» — офіційна, [першоджерело]); формати: AGENTS.md / .cursorrules / MISTAKES.md / PROGRESS.md / learnings.jsonl / docs/failures.
2. **Прямих числових доказів «журнал зменшує повтори саме поведінкових помилок» я не знайшов.** Є: (а) непов'язане число PR success 38,1%→69% (build-команди, не журнал помилок); (б) ETH ~+4% / машинний −0,5–2% / +20% вартості; (в) Reflexion 75%→90% у межах одного класу завдань з слайд-вікном 1–3. Тобто ефект **або малий, або обмежений вузьким контекстом**.
3. **Довготривалий «урок про помилку» сам не переноситься.** Офіц. дока прямо називає його лише контекстом, а не примусом; контрприклади (ctoth) показують цілковите ігнорування. Reflexion переносить лише в межах епізодичного буфера і того самого класу задач; Self-Refine не переносить нічого.
4. **Що реально ловить повтор класу помилки автоматично — це механічні гейти, а не журнал:** Stop/PreToolUse хуки (детерміновані + LLM як «veto», а не автор), stuck-detector «повтор команди 3+», proof-of-done (claim-vs-evidence), capt-hook (публікація шаблону корекції в хук), retro (18 детермінованих сигналів + 5 крос-сесійних), crucible (CI на конфіг). Усі вони виграють саме тому, що не покладаються на те, що модель «згадає».
5. **Найбільші ризики:** memory rot (застарілі/хибні рефлексії), superstition (урок з одноразового flaky-збою), context rot (записи рохнуться, агент не скаржиться), decay-системи «карають успіх» (правило зникає, коли перестає спрацьовувати).

---

## Рекомендація (ви просили рішення)

- **Оцінюйте практику через механічні гейти, а не через журнал.** Найвищу надійність мають хуки PreToolUse (блокують дію) і Stop (блокують «готово»).
- **Урок → не в CLAUDE.md, а в перевірку.** Правило типу «не роби X» варто перетворювати на: (1) детермінований PreToolUse-блок, (2) лінтер/тест, (3) чеклістовий checkpoint, і лише потім — у текст пам'яті.
- **Тримайте журнал коротким і специфічним** (офіц. дока рекомендує ≤~200 рядків для глобальних правил; ETH — рукописний «щільний» кращий за машинний «загальний»).
- **Детектуйте повтор 3+ (stuck) і ≥2 однакових класів помилок** — це узгоджені, перевірені пороги з self-critic та swift-code-reviewer.
- **LLM-суддю використовуйте як veto/підсвітку, не як автора** (self-critic; «lower-signal fallback» у aiefs-pdf).
- **Робіть журнал append-only + TTL/компакцію** (Steve Kinney про append-only; aiefs про TTL) — інакше агент «переписуванням» затирає невдачі.
- **Додайте поле «Verification»** (як у MISTAKES.md xda) і прогоняйте A/B: та сама задача до і після правила — це єдиний спосіб отримати ваші власні числа до/після.

---

## Чого не знайшов

- **Жодного репозиторію/поста з чесним числом «повторів поведінкової помилки до/після»** журналу. Усі числа, які є, — проксі (PR success, task completion, success rate в benchmark), і всі з обмовками.
- **Первинних джерел** для ETH (138 задач, 12 репозиторіїв) і Toub (dotnet/runtime, 38,1%→69%) — бачив лише перекази. **[не перевірено]**
- **Специфічного дослідження саме про `.cursorrules` / Cursor memory як журнал помилок** — знайшов лише загальні згадки AGENTS.md, який вручають Cursor вручну.
- **Окремих даних про Aider** у цій темі (журнал помилок). Не зустрічав.
- **Точних результатів MAR (arXiv:2512.20845)** — фрагмент був без чисел.

---

## Червоні прапорці

- **xda-developers** (дві статті про MISTAKES.md і Stop-хук) — схоже на матеріал з партнерськими/просувальними URL; твердження «це працює» без метрик, без контролю. Сприймати як опис практики, не як доказ.
- **Steve Kinney** — числа привабливі (38,1%→69%), але сам автор наводить два кавеати (одночасна зміна + мережа, один репозиторій із дуже складною збіркою). Не тягнути це як «доказ, що журнал працює».
- **«12-line file taught it not to»** — заголовковий наратив; у тексті ж пояснюється, що контекст стає ще одним довгим списком інструкцій.
- **AGENTS.md-репо/скіли типу retrospective спеціально цитують власний «effectiveness report»** — це self-reported, маркетинг проєкту.
- **Багато джерел мають дати в майбутньому (2026-04, 2026-05, 2026-02)** — або це навмисно-демонстраційні репозиторії, або артефакти середовища. Не спирайтесь на них як на «історичний досвід команди».
- **Найсильніші автоматичні інструменти — з alpha/публічними статусами** (crucible «v0.1 -- alpha»; self-critic — одна людина; capt-hook — PolyForm Noncommercial). Це не «продакшн-стандарт», це доказові прототипи.

---

## [не перевірено]

- ETH Zurich 138 tasks/12 repos (+4%, −0,5–2%, +20%) — первинна робота не відкрита.
- Stephen Toub / dotnet/runtime 38,1%→69% — первинний звіт не відкритий.
- harness-starter-kit «docs/failures» і «effectiveness reports» — лише через GeekNews-переказ.
- MAR (arXiv:2512.20845) — числа не витягнуті.
- Всі цитати зібрані з фрагментів сторінок у результатах пошуку; я не робив повторне завантаження для дослівної звірки кожної.

---

*Питання таке, що ставитиметься регулярно: «чи зменшують журнали помилок повтори» — доцільно зробити це постійним лід-магнітом/дослідницькою сторінкою з лінками на Anthropic docs + Reflexion + self-critic/capt-hook/proof-of-done як «що робити замість віри в журнал».*

== Джерела (40):
- Claude 如何记住您的项目 - Claude Code Docs — https://code.claude.com/docs/zh-CN/memory
- Failure: Ignored Every Instruction in CLAUDE.md — https://raw.githubusercontent.com/ctoth/claude-failures/refs/heads/master/2026-04-05-ignored-every-instruction.md#1
- Claude Codeの失敗をバグチケット化して潰す方法 | SIOS Tech Lab — https://tech-lab.sios.jp/archives/52066#respond
- Patterns: Keeping Context Useful | AI Development Setup | Steve Kinney — https://stevekinney.com/courses/ai-development-setup/patterns-for-keeping-context-useful
- Clade/PROGRESS.md at b6cb295df0f036c4c2194add0b7c48862e84f7c5 · shenxingy/Clade - 2026-02-25 — Pre-Code Reflection (learning from mistakes) — https://github.com/shenxingy/Clade/blob/b6cb295df0f036c4c2194add0b7c48862e84f7c5/PROGRESS.md#4
- Agent Loop Feedback Reference — https://cdn.jsdelivr.net/npm/swift-code-reviewer-skill@1.4.0/references/agent-loop-feedback.md#1
- 分享一份 Andrej Karpathy 大佬自用 CLAUDE.md — https://cloud.tencent.cn/developer/article/2700064#1
- GitHub - emoubarak/hindsight: Memory for Claude Code: search every past session by meaning, turn your corrections into rules. Plugin with hooks and skills. · GitHub — https://github.com/emoubarak/hindsight
- {"type": "lesson", "day": 38, "ts": "2026-04-07T00:25:00Z", "source": "evolution", "title": "Documenting a footgun in CLAUDE — https://raw.githubusercontent.com/yologdev/yoyo-evolve/4a9865b383e3b0c6cd2f4bb8220ca7b165988178/memory/learnings.jsonl#8
- Ingest: Cole Medin — 11 tiny coding agent fixes with a stupid amount … · tim-kaa-py/ai-wiki@e6627e8 - 34 | +11. [14:27-15:25] Tip 9 — Never let the writer approve the work — https://github.com/tim-kaa-py/ai-wiki/commit/e6627e8c691a138f48d37fb79192f4c3002969d2#2
- My coding agent kept making the same mistake, and a 12-line file finally taught it not to - My coding agent kept making the same mistake, and a 12-line file finally taught it not to — https://www.xda-developers.com/coding-agent-kept-making-mistake-12-line-file-taught-it-not-to/#1
- A milder instance of the same principle, observed rather than punished: in one GPT campaign, 26 of 26 workspaces (25 board games... — https://arxiv.org/pdf/2610.00834#3#3#3
- Fix the context, not the prompt | Bruin Academy — https://getbruin.com/learn/sql-ai-beginner/fix-the-context/
- GitHub - iylmwhknnx/AGENTS.md: Global instructions for coding agents: evidence, parallelization, validation, all in one AGENTS.md / CLAUDE.md · GitHub — https://github.com/iylmwhknnx/AGENTS.md
-  — https://raw.githubusercontent.com/langwatch/langwatch/81fe942ac3fe701067c37cbf81cf94dacbb0cd1a/.claude/skills/learn/SKILL.md
- - `AGENTS — https://raw.githubusercontent.com/Kodria/agentic-workflow/4bc93054052c9e70a3b618d9c9897524d5ebe8cd/docs/harness-retros.md#5
- harness-starter-kit - Kodlama ajanlarının aynı hataları tekrarlamamasına yardımcı olan repo harness’ | GeekNews — https://tr.news.hada.io/topic?id=30190
- Context rot: The silent cause of AI agent failure — https://www.andela.com/publication/context-rot-the-silent-cause-of-ai-agent-failure
- Goal Ledger for Long-Running Runs · The Contract Codex — https://majiayu000.github.io/awesome-goal-prompts/goals/x-goal-ledger.html
- I'm going to offer a counterpoint suggestion. You need to watch Claude try to implement small f... — https://althacker.news/item?id=47113137
- Reflexion: Language Agents with — https://browse.arxiv.org:443/pdf/2303.11366#4#1
- Reflexion: Language Agents with Verbal Reinforcement Learning — https://ar5iv.labs.arxiv.org/html/2303.11366#1
- MAR: Multi-Agent Reflexion Improves Reasoning Abilities in LLMs — https://ar5iv.labs.arxiv.org/html/2512.20845#1
- | **Self-Refine**（Madaan 2023） | 上一輪的 answer + critic feedback | ❌ 不保留 | 不需（pattern 1 buffer 即可） | — https://raw.githubusercontent.com/Aiken7881/manxueai-agentic-struct/f00e2c27bd27b2fa20512f3cc8018fff64d63776/stages/06-memory-rag.md#4
- - Xu et al — https://release-assets.githubusercontent.com/github-production-release-asset/1185590488/fb5c2119-7fe9-4995-bb1d-a1ebb5fcec44?sp=r&sv=2018-11-09&sr=b&spr=https&se=2026-08-05T21%3A33%3A29Z&rscd=attachment%3B+filename%3Daiefs-vol5-agents.pdf&rsct=application%2Foctet-stream&skoid=96c2d410-5711-43a1-aedd-ab1947aa7ab0&sktid=398a6654-997b-47e9-b12b-9515b896b4de&skt=2026-08-05T20%3A33%3A22Z&ske=2026-08-05T21%3A33%3A29Z&sks=b&skv=2018-11-09&sig=ZyVaaEn%2FySi%2FZOTFEmbyB%2F84DAXzei%2FmLm0BUMgg29U%3D&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmVsZWFzZS1hc3NldHMuZ2l0aHVidXNlcmNvbnRlbnQuY29tIiwia2V5Ijoia2V5MSIsImV4cCI6MTc4NTk2MzgwNywibmJmIjoxNzg1OTYzNTA3LCJwYXRoIjoicmVsZWFzZWFzc2V0cHJvZHVjdGlvbi5ibG9iLmNvcmUud2luZG93cy5uZXQifQ.ScxMjUTH81vXVCrpAIilgo3If9xs7LQ5hClGena02pU&response-content-disposition=attachment%3B%20filename%3Daiefs-vol5-agents.pdf&response-content-type=application%2Foctet-stream#92#37
- | 版本 | 跨輪保留什麼 | 跨 session 保留什麼 | 需要 memory pattern | — https://raw.githubusercontent.com/Aiken7881/manxueai-agentic-struct/1d5adebe094bbf856f1e5fa729e846bdfbeeca05/stages/06-memory-rag.md#2
- -ale-0125,Research Foundations,research-foundations,Paper,📄,Reflexion: Language Agents with Verbal Reinforcement Learning,https:... — https://huggingface.co/datasets/cy0307/awesome-loop-engineering/commit/4f72d629e7bb8e5a7da1fb9f27c6c89a603cb01b.diff?file=data%2Fresources.csv#15
- -{"row_id": "ale-0109", "section": "Research Foundations", "section_slug": "research-foundations", "resource_type": "Paper", "ma... — https://huggingface.co/datasets/cy0307/awesome-loop-engineering/commit/409cbb42dff253fcfcfd3ea317f689c97ff3dfea.diff?file=data%2Fresources.jsonl#19
- REF-021: Reflexion - Language Agents with Verbal Reinforcement Learning — https://cdn.jsdelivr.net/npm/aiwg@2026.8.27/docs/references/REF-021-reflexion-verbal-reinforcement.md#1
- agentic_ai_lab/papers/agent/reflexion.md at f456cee83931b188285f3b99503d49ff0aac0517 · ksmooi/agentic_ai_lab - Skip to content — https://github.com/ksmooi/agentic_ai_lab/blob/f456cee83931b188285f3b99503d49ff0aac0517/papers/agent/reflexion.md#1
- GitHub - nadimtuhin/claude-code-self-critic: Self-critic workflow for Claude Code to review its own output · GitHub - GitHub - nadimtuhin/claude-code-self-critic: Self-critic workflow for Claude Code to review its own output · GitHub — https://github.com/nadimtuhin/claude-code-self-critic#1
- crucible-ci - npm Package Security Analysis - Socket - 🎩 You're Invited:Meet the Socket team at Black Hat in Las Vegas, August 3-6.RSVP → — https://socket.dev/npm/package/crucible-ci#1
- proof-of-done - Coding agents end turns with "all tests pass", "the build succeeds", "fixed" or "deployed", and the session often does not back ... — https://pypi.org/project/proof-of-done/#1
- capt-hook - Stop repeating yourself to Claude — https://pypi.org/project/capt-hook/8.10.0/#1
- retro — session retrospectives for Claude Code — https://raw.githubusercontent.com/netresearch/retro-skill/main/README.md#1
- Hooks - Everything Claude Code — https://mintlify.wiki/affaan-m/everything-claude-code/concepts/hooks
- I added one hook to Claude Code, and it stopped making the same mistake twice - I added one hook to Claude Code, and it stopped making the same mistake twice — https://www.xda-developers.com/added-one-hook-claude-code-stopped-same-mistake-twice/#1
- Automate actions with hooks - Claude Code Docs - If you edit settings files directly while Claude Code is running, the file watcher normally picks up hook changes automatically — https://code.claude.com/docs/en/hooks-guide?cmid=9581027f-3e0e-475b-92c0-72916c910dd1#3
- AI Agent Discipline Linter - GitHub Marketplace - Skip to content — https://github.com/marketplace/actions/ai-agent-discipline-linter#1
- @houtini/metacog - ⚠️ — https://www.npmjs.com/package/@houtini/metacog?activeTab=versions#1

== Розмова: 20261016-141530 | вх 37302 (з кешу 2688) | вих 11171 | пошуків 5
== Ціна ≈$0.0123 (не пік; без вартості пошуків)
