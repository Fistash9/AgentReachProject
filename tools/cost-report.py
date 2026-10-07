#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cost-report.py -- підрахунок витрат на обох агентів (Claude Code і DSH) без
відомої пастки переобліку.

НАВІЩО
------
Транскрипти обох агентів стрімляться: те саме повідомлення моделі записується
у файл КІЛЬКА разів (окремі записи на кожен content-блок -- thinking / text /
tool_use). Об'єкт `usage` при цьому ПОВТОРЮЄТЬСЯ без змін у кожному записі.
Тому наївне сумування `usage` по всіх записах завищує результат у 2-4 рази.

ЯК САМЕ ДЕДУПЛІКУЄТЬСЯ (і чому саме так)
-----------------------------------------
Claude Code (`.jsonl` у ~/.claude/projects/...):
  1. Розглядаються лише записи `type == "assistant"`, у яких є `message.usage`.
  2. Записи з `isMeta == true` (наприклад agent-acompact-*, agent-aside_question-*)
     ВИКИДАЮТЬСЯ повністю -- це дублікати вже наявних повідомлень, службові
     копії, а не окремі API-виклики.
  3. Ключ дедуплікації -- `message.id` (id API-повідомлення, глобально унікальний
     для одного виклику моделі; саме він повторюється між записами стріму).
     Якщо `message.id` раптом порожній -- фолбек на `uuid` запису (тоді кожен
     запис вважається окремим -- консервативно, без ризику склеїти різне).
     Перевірено на даних: у межах одного message.id записи мають ІДЕНТИЧНИЙ
     usage і різняться лише `apiBlockIndex` + вмістом content-блоку. Тому
     «перший запис групи» і є повним описом витрат цього виклику.
  4. Наїзна сума (для показу величини похибки) рахується по ТИХ САМИХ записах,
     але без кроку 3 -- тобто кожен запис стріму додається окремо.

DSH (`session.v4.jsonl.zstd` у /root/.dsh/sessions/):
  1. usage лежить у `type == "assistant/message"` -> `data.usage`
     (`inputTokens`, `outputTokens`, `cacheReadTokens`, `cacheWriteTokens`).
     Записи `assistant/attempt` -- це невдалі спроби, usage вони не несуть.
  2. Ключ дедуплікації -- `data.message.id` (є у 100% записів), у межах сесії.
     На перевірених файлах дублікатів не знайдено (0 повторів `seq` і 0 повторів
     message.id), але крок лишається: він дешевий і захищає від регресій формату.
     ВАЖЛИВО: НЕ можна дедуплікувати за вмістом usage -- два різні короткі
     повідомлення можуть мати однакові числа і були б склеєні помилково.

ТРИ ДЖЕРЕЛА ГРОШЕЙ (звірка)
---------------------------
  1. `cost-state` у транскриптах Claude Code -- ГОТОВІ гроші від самого Claude
     Code (`totalCostUSD`, `modelUsage`). Записи кумулятивні в межах сесії
     (перевірено: монотонно не спадають), тому береться MAX на сесію, а не сума
     всіх записів (інакше -- ще одна пастка переобліку).
  2. `<корінь проєкту>/.claude/logs/session-cost.jsonl` -- статуслайн-оцінка; теж
     per-session MAX (це снапшоти одного й того самого лічильника).
     УВАГА: саме ПРОЄКТНИЙ шлях. `~/.claude/logs/session-cost.jsonl` на цьому
     хості не існує, а єдиний інший примірник лежить у /root/.trash і належить
     чужому trial-проєкту (15 сесій) -- брати його не можна.
  3. Перерахунок із дедупованих токенів за офіційним прайсом Anthropic.
     Cache-write рахується TTL-aware: 5m і 1h мають РІЗНІ ставки (1.25x і 2x
     input), а в цих транскриптах переважна більшість записів -- 1h.

ЗВІРКА -- ЛИШЕ НА ПЕРЕТИНІ session_id
-------------------------------------
Набори сесій у джерелах різні (cost-state ~146, журнал ~26), тому порівнювати
їхні підсумки «в лоб» безглуздо. Скрипт окремо рахує перетин session_id, який є
і в cost-state, і в журналі, і на ньому зводить усі три шляхи.

ЦІНИ
----
Anthropic (офіційно, https://platform.claude.com/docs/en/about-claude/pricing):
  claude-opus-5-5         in $4 / out $20 / cw-5m $5.00 / cw-1h $8   / cr $0.20
  claude-sonnet-5         in $2 / out $10 / cw-5m $2.50 / cw-1h $4   / cr $0.20
  claude-haiku-4-5-...    in $1 / out $5  / cw-5m $1.25 / cw-1h $2   / cr $0.10
DSH/DeepSeek (off-peak, /root/dsh-app/cost-waste.md):
  cache-hit $0.003/1M, cache-miss $0.15/1M, вихід $0.60/1M; пік = x2.

Жодних мережевих викликів: усе локальне, zstd -- через subprocess.

ВИКОРИСТАННЯ
------------
  python3 tools/cost-report.py --all             # обидва агенти
  python3 tools/cost-report.py --claude          # лише Claude Code
  python3 tools/cost-report.py --dsh             # лише DSH
  python3 tools/cost-report.py --all --json      # машинний вивід
  python3 tools/cost-report.py --all --claude-dir PATH --dsh-dir PATH \
                               --session-cost PATH
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Типові шляхи цього хоста (можна перекрити прапорцями)
# --------------------------------------------------------------------------
TERMUX_HOME = "/data/data/com.termux/files/home"
# Корінь проєкту -- тека над tools/; шляхи до ПРОЄКТНИХ даних прив'язані до нього,
# а не до ~/.claude (щоб скрипт не залежав від cwd і не «з'їжджав» на чужі копії).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CLAUDE_DIR = os.path.join(
    TERMUX_HOME, ".claude/projects/-data-data-com-termux-files-home-AgentReachProject"
)
# session-cost.jsonl -- це ПРОЄКТНИЙ журнал статуслайна: <корінь>/.claude/logs/.
# Саме він має повне покриття (4481 запис / 26 унікальних session_id станом на
# 2026-10-07). Решта шляхів -- фолбек для іншого хоста/архіву; вони НЕПОВНІ:
# `~/.claude/logs/session-cost.jsonl` на цьому хості не існує взагалі, а єдиний
# інший примірник (/root/.trash/2026-10-01/proj-trial/...) містить 2168 записів
# на 15 сесій чужого trial-проєкту. Брати його як «шлях 2» -- помилка.
SESSION_COST_CANDIDATES = [
    os.path.join(PROJECT_ROOT, ".claude", "logs", "session-cost.jsonl"),
    os.path.join(TERMUX_HOME, ".claude/logs/session-cost.jsonl"),
    "/root/.claude/logs/session-cost.jsonl",
    "/root/.trash/2026-10-01/proj-trial/.claude/logs/session-cost.jsonl",
]
DEFAULT_DSH_DIR = "/root/.dsh/sessions"

# --------------------------------------------------------------------------
# Прайс Anthropic: $ за 1M токенів
# (in, out, cache_write_5m, cache_write_1h, cache_read)
# 5m = 1.25x input, 1h = 2x input -- з офіційної таблиці
# https://platform.claude.com/docs/en/about-claude/pricing (перевірено 2026-10-07):
#   Claude Opus 5.5   $4 / $20 / $5   / $8    / $0.20
#   Claude Sonnet 5.5 $2 / $10 / $2.5 / $4    / $0.20
#   Claude Haiku 4.5  $1 / $5  / $1.25/ $2    / $0.10
# ВАЖЛИВО: у транскриптах майже вся cache-creation -- це 1h-записи
# (`usage.cache_creation.ephemeral_1h_input_tokens`), тому прайс 5m занижує
# перерахунок. Раніше тут був саме 5m -- це виправлено.
# --------------------------------------------------------------------------
ANTHROPIC_PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 5.0, 8.0, 0.20),
    "claude-sonnet-5": (2.0, 10.0, 2.50, 4.0, 0.20),
    "claude-haiku-4-5-20251001": (1.0, 5.0, 1.25, 2.0, 0.10),
    # аліаси, які може писати CLI
    "claude-haiku-4-5": (1.0, 5.0, 1.25, 2.0, 0.10),
    "claude-sonnet-5-5": (2.0, 10.0, 2.50, 4.0, 0.20),
}

# Прайс DSH (off-peak), $ за 1M токенів
DSH_CACHE_HIT = 0.003
DSH_CACHE_MISS = 0.15
DSH_OUTPUT = 0.60
DSH_PEAK_MULTIPLIER = 2.0


def log(msg: str) -> None:
    """Прогрес -- лише в stderr, щоб не псувати --json на stdout."""
    print(msg, file=sys.stderr)


def iter_jsonl(path: str):
    """Потоковий читач JSONL: по одному об'єкту, стійкий до битих рядків."""
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            # дешевий пре-фільтр: повний json.loads лише для потрібних типів
            if (
                '"cost-state"' not in line
                and '"assistant"' not in line
                and '"isMeta"' not in line
            ):
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


# ==========================================================================
# CLAUDE CODE
# ==========================================================================
def claude_files(claude_dir: str):
    """Усі транскрипти: топ-рівень + підтеки subagents/ (якщо є)."""
    files = sorted(glob.glob(os.path.join(claude_dir, "*.jsonl")))
    files += sorted(glob.glob(os.path.join(claude_dir, "*", "subagents", "*.jsonl")))
    files += sorted(glob.glob(os.path.join(claude_dir, "*", "*", "subagents", "*.jsonl")))
    return sorted(set(files))


def collect_claude(claude_dir: str) -> dict:
    """
    Читає всі транскрипти Claude Code і повертає:
      - dedup-токени (по message.id, isMeta виключено)
      - naive-токени (ті самі записи, але без дедупу) -- для оцінки похибки
      - cost-state: фінальний запис на сесію (MAX totalCostUSD)
    """
    files = claude_files(claude_dir)
    if not files:
        raise SystemExit(f"Немає транскриптів у {claude_dir}")

    seen_msg_ids = set()          # ключі дедупу (message.id)
    dedup = defaultdict(int)      # in/out/cc/cr
    naive = defaultdict(int)
    dedup_models = defaultdict(lambda: defaultdict(int))  # model -> tokens
    # те саме, але з розбивкою по сесіях -- для звірки НА ОДНОМУ наборі сесій
    sess_models = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    ts_min = ts_max = None
    n_assistant = 0
    n_assistant_meta = 0
    n_dedup_dropped = 0
    sessions_with_assistant = set()

    cost_state = {}               # sessionId -> фінальний запис
    cost_state_all_sum = 0.0      # наївна сума ВСІХ записів cost-state
    cost_state_records = 0
    n_isMeta_all = 0              # isMeta будь-якого типу (переважно type=user)
    n_isMeta_with_usage = 0

    for path in files:
        for rec in iter_jsonl(path):
            rtype = rec.get("type")

            if rec.get("isMeta"):
                n_isMeta_all += 1

            if rtype == "cost-state":
                cost_state_records += 1
                cost_state_all_sum += float(rec.get("totalCostUSD") or 0.0)
                sid = rec.get("sessionId") or os.path.basename(path)
                prev = cost_state.get(sid)
                if prev is None or float(rec.get("totalCostUSD") or 0.0) > float(
                    prev.get("totalCostUSD") or 0.0
                ):
                    cost_state[sid] = rec
                continue

            if rtype != "assistant":
                continue

            n_assistant += 1
            if rec.get("isMeta"):
                # службові копії (agent-acompact-*, agent-aside_question-*):
                # дублікати вже наявних повідомлень -> виключаємо повністю.
                n_assistant_meta += 1
                if (rec.get("message") or {}).get("usage"):
                    n_isMeta_with_usage += 1
                continue

            msg = rec.get("message") or {}
            usage = msg.get("usage") or {}
            if not usage:
                continue

            key = msg.get("id") or rec.get("uuid")
            model = msg.get("model") or "unknown"
            ts = rec.get("timestamp")
            if ts:
                ts_min = ts if ts_min is None or ts < ts_min else ts_min
                ts_max = ts if ts_max is None or ts > ts_max else ts_max
            sessions_with_assistant.add(rec.get("sessionId") or path)

            in_t = int(usage.get("input_tokens") or 0)
            out_t = int(usage.get("output_tokens") or 0)
            cc_t = int(usage.get("cache_creation_input_tokens") or 0)
            cr_t = int(usage.get("cache_read_input_tokens") or 0)
            # TTL cache-creation: 5m vs 1h -- у них РІЗНИЙ прайс (1.25x vs 2x input).
            cc_detail = usage.get("cache_creation") or {}
            cc5 = int(cc_detail.get("ephemeral_5m_input_tokens") or 0)
            cc1 = int(cc_detail.get("ephemeral_1h_input_tokens") or 0)
            if cc5 + cc1 == 0:
                # поля TTL немає -- консервативно вважаємо все 5m-записами
                cc5 = cc_t
                cc1 = 0
            sid = rec.get("sessionId") or path

            # ---- наївна сума: кожен запис стріму окремо ----
            naive["input"] += in_t
            naive["output"] += out_t
            naive["cache_creation"] += cc_t
            naive["cache_read"] += cr_t

            # ---- дедуп за message.id ----
            if key in seen_msg_ids:
                n_dedup_dropped += 1
                continue
            seen_msg_ids.add(key)

            dedup["input"] += in_t
            dedup["output"] += out_t
            dedup["cache_creation"] += cc_t
            dedup["cache_read"] += cr_t
            dedup_models[model]["input"] += in_t
            dedup_models[model]["output"] += out_t
            dedup_models[model]["cache_creation"] += cc_t
            dedup_models[model]["cache_creation_5m"] += cc5
            dedup_models[model]["cache_creation_1h"] += cc1
            dedup_models[model]["cache_read"] += cr_t
            sm = sess_models[sid][model]
            sm["input"] += in_t
            sm["output"] += out_t
            sm["cache_creation_5m"] += cc5
            sm["cache_creation_1h"] += cc1
            sm["cache_read"] += cr_t

    # ---- агрегація cost-state по моделях (з фінальних записів сесій) ----
    by_model = defaultdict(lambda: defaultdict(float))
    top_sessions = []
    total_cost = 0.0
    session_dates = {}
    n_unknown_flag = 0
    cost_unknown_flag = 0.0
    cost_anthropic_family = 0.0
    cost_other_family = 0.0
    # sessionId -> {total, claude_only} -- щоб мати змогу звіряти шляхи НА ОДНОМУ
    # Й ТОМУ САМОМУ наборі сесій (перетин), а не на різних підмножинах.
    cost_state_per_session = {}
    for sid, rec in cost_state.items():
        c = float(rec.get("totalCostUSD") or 0.0)
        total_cost += c
        top_sessions.append({"session": sid, "cost_usd": round(c, 6)})
        st = rec.get("startTime")
        session_dates[sid] = (
            datetime.fromtimestamp(st / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")
            if isinstance(st, (int, float))
            else "unknown"
        )
        if rec.get("hasUnknownModelCost"):
            # Claude Code сам каже: для якоїсь моделі він не мав прайсу і застосував
            # фолбек-тариф. На цих даних це РІВНО сесії з deepseek-моделями.
            n_unknown_flag += 1
            cost_unknown_flag += c
        claude_only = 0.0
        for model, mu in (rec.get("modelUsage") or {}).items():
            mc = float(mu.get("costUSD") or 0.0)
            if model.startswith("claude-"):
                cost_anthropic_family += mc
                claude_only += mc
            else:
                cost_other_family += mc
            m = by_model[model]
            m["input_tokens"] += int(mu.get("inputTokens") or 0)
            m["output_tokens"] += int(mu.get("outputTokens") or 0)
            m["thinking_tokens"] += int(mu.get("thinkingTokens") or 0)
            m["cache_read_input_tokens"] += int(mu.get("cacheReadInputTokens") or 0)
            m["cache_creation_input_tokens"] += int(
                mu.get("cacheCreationInputTokens") or 0
            )
            m["web_search_requests"] += int(mu.get("webSearchRequests") or 0)
            m["cost_usd"] += float(mu.get("costUSD") or 0.0)
        cost_state_per_session[sid] = {
            "total": round(c, 6),
            "claude_only": round(claude_only, 6),
        }
    top_sessions.sort(key=lambda x: -x["cost_usd"])

    # ---- середня вартість на день ----
    per_day = defaultdict(float)
    for sid, d in session_dates.items():
        per_day[d] += float(cost_state[sid].get("totalCostUSD") or 0.0)

    # ---- перерахунок із дедупованих токенів за прайсом Anthropic ----
    # Основне число -- TTL-aware: 5m- і 1h-записи кешу за РІЗНИМИ ставками.
    # Додатково рахуємо варіант «усе за ставкою 5m» -- щоб було видно, скільки
    # дає сама лише поправка на TTL (раніше в звіті було тільки це число).
    recompute_total = 0.0
    recompute_total_5m = 0.0
    recompute_priced = {}
    unpriced_models = []
    ttl_tokens = {"cache_creation_5m": 0, "cache_creation_1h": 0}
    for model, t in dedup_models.items():
        price = ANTHROPIC_PRICES.get(model)
        if price is None:
            unpriced_models.append(model)
            continue
        pin, pout, pcw5, pcw1, pcr = price
        cc5 = t["cache_creation_5m"]
        cc1 = t["cache_creation_1h"]
        ttl_tokens["cache_creation_5m"] += cc5
        ttl_tokens["cache_creation_1h"] += cc1
        base = t["input"] * pin + t["output"] * pout + t["cache_read"] * pcr
        c = (base + cc5 * pcw5 + cc1 * pcw1) / 1e6
        c5 = (base + (cc5 + cc1) * pcw5) / 1e6
        recompute_total += c
        recompute_total_5m += c5
        recompute_priced[model] = {
            "input_tokens": t["input"],
            "output_tokens": t["output"],
            "cache_creation_input_tokens": t["cache_creation"],
            "cache_creation_5m_tokens": cc5,
            "cache_creation_1h_tokens": cc1,
            "cache_read_input_tokens": t["cache_read"],
            "cost_usd": round(c, 6),
            "cost_usd_if_all_cache_writes_5m": round(c5, 6),
        }

    # ---- те саме, але окремо по кожній сесії (для звірки на перетині) ----
    def _price_session(models_tokens: dict) -> float:
        tot = 0.0
        for model, t in models_tokens.items():
            price = ANTHROPIC_PRICES.get(model)
            if price is None:
                continue
            pin, pout, pcw5, pcw1, pcr = price
            tot += (
                t["input"] * pin
                + t["output"] * pout
                + t["cache_creation_5m"] * pcw5
                + t["cache_creation_1h"] * pcw1
                + t["cache_read"] * pcr
            ) / 1e6
        return tot

    recompute_per_session = {
        sid: round(_price_session(models_tokens), 6)
        for sid, models_tokens in sess_models.items()
    }

    # ---- додатково: deepseek-моделі в тих самих транскриптах за прайсом DeepSeek ----
    # (це не «шлях 3» за Anthropic, а крос-перевірка: чи сходяться гроші cost-state
    #  з передруком токенів за тарифом DeepSeek).
    recompute_deepseek = 0.0
    for model, t in dedup_models.items():
        if not model.startswith("deepseek"):
            continue
        recompute_deepseek += (
            t["cache_read"] * DSH_CACHE_HIT
            + (t["input"] + t["cache_creation"]) * DSH_CACHE_MISS
            + t["output"] * DSH_OUTPUT
        ) / 1e6

    # ---- метрики ----
    denom = dedup["cache_read"] + dedup["input"] + dedup["cache_creation"]
    cache_hit_rate = dedup["cache_read"] / denom if denom else 0.0

    # частка output у вазі витрат (за прайсом, моделі з відомою ціною)
    out_cost = in_cost = cw_cost = cr_cost = 0.0
    for model, t in dedup_models.items():
        price = ANTHROPIC_PRICES.get(model)
        if price is None:
            continue
        pin, pout, pcw5, pcw1, pcr = price
        out_cost += t["output"] * pout / 1e6
        in_cost += t["input"] * pin / 1e6
        cw_cost += (t["cache_creation_5m"] * pcw5 + t["cache_creation_1h"] * pcw1) / 1e6
        cr_cost += t["cache_read"] * pcr / 1e6
    priced_total = out_cost + in_cost + cw_cost + cr_cost

    n_sessions = len(cost_state)
    return {
        "files": len(files),
        "records_assistant": n_assistant,
        "records_assistant_isMeta_excluded": n_assistant_meta,
        "is_meta_all": n_isMeta_all,
        "is_meta_with_usage": n_isMeta_with_usage,
        "records_dropped_as_duplicates": n_dedup_dropped,
        "unique_api_messages": len(seen_msg_ids),
        "sessions_with_cost_state": n_sessions,
        "sessions_with_assistant_records": len(sessions_with_assistant),
        "period": {"min": ts_min, "max": ts_max},
        "cost_state": {
            "total_usd_per_session_max": round(total_cost, 4),
            "naive_sum_all_records_usd": round(cost_state_all_sum, 4),
            "records": cost_state_records,
            "by_model": {
                k: {
                    kk: (round(vv, 6) if kk == "cost_usd" else int(vv))
                    for kk, vv in v.items()
                }
                for k, v in sorted(by_model.items(), key=lambda x: -x[1]["cost_usd"])
            },
            "top5_sessions": top_sessions[:5],
            "per_day": {k: round(v, 4) for k, v in sorted(per_day.items())},
            "avg_per_session_usd": round(total_cost / n_sessions, 4) if n_sessions else 0.0,
            "avg_per_day_usd": round(total_cost / len(per_day), 4) if per_day else 0.0,
            "n_days": len(per_day),
            "hasUnknownModelCost_sessions": n_unknown_flag,
            "hasUnknownModelCost_usd": round(cost_unknown_flag, 4),
            "family_split_usd": {
                "claude_*": round(cost_anthropic_family, 4),
                "other_deepseek": round(cost_other_family, 4),
            },
            "per_session": cost_state_per_session,
        },
        "tokens_dedup": {k: v for k, v in dedup.items()},
        "tokens_naive": {k: v for k, v in naive.items()},
        "dedup_overcount_factor": {
            k: round(naive[k] / dedup[k], 4) if dedup[k] else None for k in naive
        },
        "metrics": {
            "cache_hit_rate": round(cache_hit_rate, 6),
            "cost_split_priced_anthropic_usd": {
                "output": round(out_cost, 4),
                "input": round(in_cost, 4),
                "cache_creation": round(cw_cost, 4),
                "cache_read": round(cr_cost, 4),
                "total": round(priced_total, 4),
            },
            "output_share_of_priced_cost": round(out_cost / priced_total, 6)
            if priced_total
            else None,
        },
        "recompute_from_tokens": {
            "possible": not unpriced_models,
            "total_usd": round(recompute_total, 4),
            "total_usd_if_all_cache_writes_5m": round(recompute_total_5m, 4),
            "cache_creation_ttl_tokens": ttl_tokens,
            "per_model": recompute_priced,
            "per_session_usd": recompute_per_session,
            "unpriced_models": sorted(set(unpriced_models)),
            "deepseek_models_usd_at_deepseek_prices": round(recompute_deepseek, 4),
        },
    }


def collect_session_cost(path: str) -> dict:
    """Статуслайн-оцінка: per-session MAX cost (без пре-фільтра -- тут свій формат)."""
    per_session = {}
    models = defaultdict(int)
    n = 0
    min_ts = max_ts = None
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            c = rec.get("cost")
            sid = rec.get("session_id")
            if c is None or sid is None:
                continue
            n += 1
            per_session[sid] = max(per_session.get(sid, 0.0), float(c))
            models[rec.get("model") or "unknown"] += 1
            ts = rec.get("ts")
            if ts:
                min_ts = ts if min_ts is None or ts < min_ts else min_ts
                max_ts = ts if max_ts is None or ts > max_ts else max_ts
    top = sorted(per_session.items(), key=lambda x: -x[1])
    return {
        "path": path,
        "records": n,
        "sessions": len(per_session),
        "total_usd_per_session_max": round(sum(per_session.values()), 4),
        "top5_sessions": [{"session": s, "cost_usd": round(v, 4)} for s, v in top[:5]],
        "models_seen": dict(models),
        "per_session": {s: round(v, 6) for s, v in per_session.items()},
        "period": {"min": min_ts, "max": max_ts},
    }


# ==========================================================================
# DSH
# ==========================================================================
def dsh_session_files(dsh_dir: str):
    return sorted(glob.glob(os.path.join(dsh_dir, "*", "*", "session.v4.jsonl.zstd")))


def read_zstd(path: str):
    """Розпакування через subprocess (stdlib-only, без python-zstd)."""
    try:
        out = subprocess.run(
            ["zstd", "-dc", path], capture_output=True, timeout=120
        )
    except FileNotFoundError:
        raise SystemExit("Не знайдено `zstd` у PATH -- потрібен для сесій DSH")
    if out.returncode != 0:
        return
    for line in out.stdout.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue


def collect_dsh(dsh_dir: str) -> dict:
    files = dsh_session_files(dsh_dir)
    if not files:
        raise SystemExit(f"Немає сесій DSH у {dsh_dir}")

    sessions = []
    for path in files:
        sid = os.path.basename(os.path.dirname(path))
        origin = None
        parent = None
        cwd = None
        seen_ids = set()
        n_records = 0
        n_dup = 0
        tok = defaultdict(int)
        models = defaultdict(lambda: defaultdict(int))
        for rec in read_zstd(path):
            rtype = rec.get("type")
            if rtype == "session":
                sid = rec.get("id") or sid
                origin = rec.get("origin")
                parent = rec.get("parentSession")
                cwd = rec.get("cwd")
                continue
            if rtype != "assistant/message":
                continue
            data = rec.get("data") or {}
            usage = data.get("usage")
            if not usage:
                continue
            n_records += 1
            mid = (data.get("message") or {}).get("id") or f"{path}:{rec.get('seq')}"
            if mid in seen_ids:
                n_dup += 1
                continue
            seen_ids.add(mid)
            i = int(usage.get("inputTokens") or 0)
            o = int(usage.get("outputTokens") or 0)
            cr = int(usage.get("cacheReadTokens") or 0)
            cw = int(usage.get("cacheWriteTokens") or 0)
            tok["input"] += i
            tok["output"] += o
            tok["cache_read"] += cr
            tok["cache_write"] += cw
            model = ((data.get("message") or {}).get("source") or {}).get("model") or "unknown"
            models[model]["input"] += i
            models[model]["output"] += o
            models[model]["cache_read"] += cr
            models[model]["cache_write"] += cw

        off = (
            tok["cache_read"] * DSH_CACHE_HIT
            + (tok["input"] + tok["cache_write"]) * DSH_CACHE_MISS
            + tok["output"] * DSH_OUTPUT
        ) / 1e6
        sessions.append(
            {
                "session": sid,
                "origin": origin or "root",
                "parent": parent,
                "cwd": cwd,
                "records": n_records,
                "dup_dropped": n_dup,
                "tokens": dict(tok),
                "cost_off_peak_usd": round(off, 6),
                "cost_all_peak_usd": round(off * DSH_PEAK_MULTIPLIER, 6),
                "models": {k: dict(v) for k, v in models.items()},
            }
        )

    total = defaultdict(int)
    for s in sessions:
        for k, v in s["tokens"].items():
            total[k] += v

    subagents = [s for s in sessions if s["origin"] == "subagent"]
    roots = [s for s in sessions if s["origin"] != "subagent"]

    def _sum(lst, key):
        return round(sum(s[key] for s in lst), 6)

    def _tok(lst, key):
        return sum(s["tokens"].get(key, 0) for s in lst)

    return {
        "dir": dsh_dir,
        "files": len(files),
        "sessions_total": len(sessions),
        "sessions_root": len(roots),
        "sessions_subagent": len(subagents),
        "records_assistant_messages": sum(s["records"] for s in sessions),
        "duplicates_dropped": sum(s["dup_dropped"] for s in sessions),
        "tokens_total_dedup": dict(total),
        "cost_split_off_peak_usd": {
            "output": round(total.get("output", 0) * DSH_OUTPUT / 1e6, 6),
            "input": round(
                (total.get("input", 0) + total.get("cache_write", 0))
                * DSH_CACHE_MISS / 1e6, 6),
            "cache_read": round(total.get("cache_read", 0) * DSH_CACHE_HIT / 1e6, 6),
        },
        "total_cost_off_peak_usd": _sum(sessions, "cost_off_peak_usd"),
        "total_cost_all_peak_usd": _sum(sessions, "cost_all_peak_usd"),
        "root_cost_off_peak_usd": _sum(roots, "cost_off_peak_usd"),
        "root_cost_all_peak_usd": _sum(roots, "cost_all_peak_usd"),
        "subagent_cost_off_peak_usd": _sum(subagents, "cost_off_peak_usd"),
        "subagent_cost_all_peak_usd": _sum(subagents, "cost_all_peak_usd"),
        "root_tokens": {k: _tok(roots, k) for k in
                        ("input", "output", "cache_read", "cache_write")},
        "subagent_tokens": {k: _tok(subagents, k) for k in
                            ("input", "output", "cache_read", "cache_write")},
        "top5_sessions": sorted(
            sessions, key=lambda s: -s["cost_off_peak_usd"]
        )[:5],
        "prices": {
            "cache_hit_per_1m": DSH_CACHE_HIT,
            "cache_miss_per_1m": DSH_CACHE_MISS,
            "output_per_1m": DSH_OUTPUT,
            "peak_multiplier": DSH_PEAK_MULTIPLIER,
        },
    }


# ==========================================================================
# ВИВІД
# ==========================================================================
def fmt_int(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def print_claude(d: dict) -> None:
    cs = d["cost_state"]
    print("=" * 78)
    print("A) CLAUDE CODE -- гроші (джерело: cost-state у транскриптах)")
    print("=" * 78)
    print(f"  Транскриптів: {d['files']}  |  "
          f"сесій із cost-state: {d['sessions_with_cost_state']}  |  "
          f"сесій із записами assistant: {d['sessions_with_assistant_records']}")
    print(f"  СУМА totalCostUSD (MAX на сесію): ${cs['total_usd_per_session_max']:.2f}")
    print(f"  Наївна сума всіх {cs['records']} записів cost-state: "
          f"${cs['naive_sum_all_records_usd']:.2f}  (пастка кумулятивних снапшотів)")
    print(f"  Середня на сесію: ${cs['avg_per_session_usd']:.2f}"
          f"  |  Середня на день: ${cs['avg_per_day_usd']:.2f}  ({cs['n_days']} днів)")
    fam = cs["family_split_usd"]
    print(f"  Родина моделей: claude-* ${fam['claude_*']:.2f}  |  "
          f"deepseek/інші ${fam['other_deepseek']:.2f}  "
          f"(це {fam['other_deepseek']/cs['total_usd_per_session_max']*100:.1f}% суми)")
    print(f"  hasUnknownModelCost=True: {cs['hasUnknownModelCost_sessions']} сесій на "
          f"${cs['hasUnknownModelCost_usd']:.2f} -- Claude Code НЕ мав прайсу для цих "
          f"моделей і застосував фолбек-тариф (див. звірку)")
    p = d["period"]
    print(f"  Період: {p['min']} .. {p['max']}")

    print("\n  Розбивка по моделях:")
    print(f"  {'модель':<26}{'in':>13}{'out':>13}{'cacheR':>14}{'cacheC':>13}{'$':>10}")
    for m, v in cs["by_model"].items():
        print(f"  {m:<26}{fmt_int(v['input_tokens']):>13}"
              f"{fmt_int(v['output_tokens']):>13}"
              f"{fmt_int(v['cache_read_input_tokens']):>14}"
              f"{fmt_int(v['cache_creation_input_tokens']):>13}"
              f"{v['cost_usd']:>10.2f}")

    print("\n  Топ-5 сесій за грошима:")
    for s in cs["top5_sessions"]:
        print(f"    ${s['cost_usd']:>9.2f}  {s['session']}")

    print("\n  По днях:")
    for day, v in cs["per_day"].items():
        print(f"    {day}  ${v:>9.2f}")

    print()
    print("=" * 78)
    print("B) ТОКЕНИ: наївна сума vs дедуплікація")
    print("=" * 78)
    print(f"  Записів assistant: {fmt_int(d['records_assistant'])}  |  "
          f"isMeta усього: {d['is_meta_all']} "
          f"(з них з usage: {d['is_meta_with_usage']})  |  "
          f"дублікатів відкинуто: {fmt_int(d['records_dropped_as_duplicates'])}")
    print(f"  Унікальних API-повідомлень: {fmt_int(d['unique_api_messages'])}")
    print(f"  {'метрика':<18}{'наївна сума':>18}{'дедуп':>18}{'завищення':>12}")
    for k in ("input", "output", "cache_creation", "cache_read"):
        nv, dv = d["tokens_naive"][k], d["tokens_dedup"][k]
        f = d["dedup_overcount_factor"][k]
        print(f"  {k:<18}{fmt_int(nv):>18}{fmt_int(dv):>18}"
              f"{(str(round(f,2))+'x') if f else '-':>12}")
    tn = sum(d["tokens_naive"].values())
    td = sum(d["tokens_dedup"].values())
    print(f"  {'РАЗОМ':<18}{fmt_int(tn):>18}{fmt_int(td):>18}"
          f"{str(round(tn/td,2))+'x' if td else '-':>12}")

    print()
    print("=" * 78)
    print("C) МЕТРИКИ")
    print("=" * 78)
    print(f"  Cache hit rate = cr/(cr+in+cc): {d['metrics']['cache_hit_rate']*100:.2f}%")
    sp = d["metrics"]["cost_split_priced_anthropic_usd"]
    print(f"  Частка output у вазі витрат (прайс Anthropic, моделі з ціною): "
          f"{d['metrics']['output_share_of_priced_cost']*100:.2f}%")
    print(f"    output ${sp['output']:.2f} | input ${sp['input']:.2f} | "
          f"cache-write ${sp['cache_creation']:.2f} | cache-read ${sp['cache_read']:.2f}")


def print_dsh(d: dict) -> None:
    print()
    print("=" * 78)
    print("G) DSH -- токени й гроші")
    print("=" * 78)
    print(f"  Файлів сесій: {d['files']}  |  сесій: {d['sessions_total']}  "
          f"(root: {d['sessions_root']}, subagent: {d['sessions_subagent']})")
    print(f"  Записів assistant/message: {fmt_int(d['records_assistant_messages'])}  |  "
          f"дублікатів відкинуто: {d['duplicates_dropped']}")
    t = d["tokens_total_dedup"]
    print(f"  Токени (дедуп): in {fmt_int(t.get('input',0))}, "
          f"out {fmt_int(t.get('output',0))}, "
          f"cache-read {fmt_int(t.get('cache_read',0))}, "
          f"cache-write {fmt_int(t.get('cache_write',0))}")
    print(f"  ГРОШІ off-peak: ${d['total_cost_off_peak_usd']:.4f}"
          f"  |  усе в пік (x{d['prices']['peak_multiplier']}): "
          f"${d['total_cost_all_peak_usd']:.4f}")
    cw = d["cost_split_off_peak_usd"]
    print(f"    з них: output ${cw['output']:.4f} | input(+cache-write) "
          f"${cw['input']:.4f} | cache-read ${cw['cache_read']:.4f}")
    print(f"    root-сесії:     ${d['root_cost_off_peak_usd']:.2f} off-peak / "
          f"${d['root_cost_all_peak_usd']:.2f} peak")
    print(f"    subagent-сесії: ${d['subagent_cost_off_peak_usd']:.2f} off-peak / "
          f"${d['subagent_cost_all_peak_usd']:.2f} peak")
    print("\n  Топ-5 сесій DSH:")
    for s in d["top5_sessions"]:
        print(f"    ${s['cost_off_peak_usd']:>8.4f}  {s['session']}  "
              f"[{s['origin']}]  in={fmt_int(s['tokens'].get('input',0))} "
              f"out={fmt_int(s['tokens'].get('output',0))} "
              f"cr={fmt_int(s['tokens'].get('cache_read',0))}")


def implied_unit_prices(rows):
    """
    Розв'язує систему «токени x ціна = costUSD» (метод Гауса) для 3 моделей,
    щоб побачити, ЯКІ одиничні ціни реально зашиті в cost-state.
    rows: [(input_tokens, output_tokens, cache_read_tokens, cost_usd), ...]
    """
    n = len(rows)
    if n < 3:
        return None
    M = [
        [rows[i][0] / 1e6, rows[i][1] / 1e6, rows[i][2] / 1e6, rows[i][3]]
        for i in range(3)
    ]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(M[r][c]))
        if M[p][c] == 0:
            return None
        M[c], M[p] = M[p], M[c]
        for r in range(3):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, 4):
                    M[r][k] -= f * M[c][k]
    try:
        return {
            "input_per_1m": round(M[0][3] / M[0][0], 4),
            "output_per_1m": round(M[1][3] / M[1][1], 4),
            "cache_read_per_1m": round(M[2][3] / M[2][2], 4),
        }
    except ZeroDivisionError:
        return None


def print_reconciliation(claude: dict, sc: dict | None) -> dict:
    print()
    print("=" * 78)
    print("D) ЗВІРКА ТРЬОХ ШЛЯХІВ (Claude Code)")
    print("=" * 78)
    a = claude["cost_state"]["total_usd_per_session_max"]
    b = sc["total_usd_per_session_max"] if sc else None
    rec = claude["recompute_from_tokens"]
    c = rec["total_usd"]
    rows = [("1) cost-state (per-session max)", a, "усі сесії проєкту")]
    if b is not None:
        rows.append((f"2) session-cost.jsonl ({sc['sessions']} сесій)",
                     b, "лише ті сесії, що потрапили в статуслайн"))
    rows.append(("3) перерахунок із дедуп-токенів (прайс Anthropic)", c,
                 ("лише моделі з відомою ціною: " + ", ".join(rec["per_model"]))
                 if rec["possible"] else
                 "НЕПОВНИЙ: без ціни: " + ", ".join(rec["unpriced_models"])))
    print(f"  {'шлях':<52}{'$':>12}")
    for name, val, note in rows:
        print(f"  {name:<52}{val:>12.2f}")
        print(f"      ({note})")
    print()
    if b:
        print(f"  Розбіжність 1 vs 2 (РІЗНІ набори сесій!): {abs(a-b)/a*100:.1f}%  "
              f"(другий шлях бачить лише {sc['sessions']} сесій з ~"
              f"{claude['sessions_with_cost_state']})")
    print(f"  Розбіжність 1 vs 3 (РІЗНІ набори сесій!): {abs(a-c)/a*100:.1f}%  "
          f"(шлях 3 без моделей: {', '.join(rec['unpriced_models']) or 'немає'})")
    print("  ^ ці два числа не мають сенсу: порівнюються різні підмножини сесій.")
    print("    Коректне порівняння -- на ПЕРЕТИНІ session_id (нижче).")

    # ---- ЗВІРКА НА ПЕРЕТИНІ: ті самі сесії в усіх трьох джерелах ----
    inter = None
    if sc and claude["cost_state"].get("per_session"):
        cs_per = claude["cost_state"]["per_session"]
        sc_per = sc.get("per_session") or {}
        common = sorted(set(cs_per) & set(sc_per))
        a_i = sum(cs_per[s]["total"] for s in common)
        a_cl = sum(cs_per[s]["claude_only"] for s in common)
        b_i = sum(sc_per[s] for s in common)
        rps = rec.get("per_session_usd") or {}
        c_i = sum(rps.get(s, 0.0) for s in common)
        print()
        print(f"  ПЕРЕТИН session_id: {len(common)} сесій "
              f"(з {len(cs_per)} у cost-state і {len(sc_per)} у журналі)")
        print(f"  {'шлях (на перетині)':<46}{'$':>14}")
        print(f"  {'1) cost-state MAX, усі моделі':<46}{a_i:>14.2f}")
        print(f"  {'1c) cost-state MAX, лише claude-*':<46}{a_cl:>14.2f}")
        print(f"  {'2) session-cost.jsonl MAX':<46}{b_i:>14.2f}")
        print(f"  {'3) дедуп-токени x прайс Anthropic (TTL-aware)':<46}{c_i:>14.2f}")
        if a_i:
            print(f"     2 vs 1 : {(b_i-a_i)/a_i*100:+.2f}%  ({b_i-a_i:+.4f}$)")
        if a_cl:
            print(f"     2 vs 1c: {(b_i-a_cl)/a_cl*100:+.2f}%  ({b_i-a_cl:+.4f}$)")
            print(f"     3 vs 1c: {(c_i-a_cl)/a_cl*100:+.2f}%  ({c_i-a_cl:+.4f}$)")
        ttl = rec.get("cache_creation_ttl_tokens") or {}
        print(f"     TTL cache-write у дедуп-токах: 5m="
              f"{fmt_int(ttl.get('cache_creation_5m', 0))}, 1h="
              f"{fmt_int(ttl.get('cache_creation_1h', 0))} -> саме тому прайс 5m занижує")
        inter = {"n": len(common), "path1_all": round(a_i, 4),
                 "path1_claude_only": round(a_cl, 4),
                 "path2": round(b_i, 4), "path3": round(c_i, 4),
                 "pct_2_vs_1": round((b_i-a_i)/a_i*100, 2) if a_i else None,
                 "pct_3_vs_1c": round((c_i-a_cl)/a_cl*100, 2) if a_cl else None}
    ds_from_cs = sum(
        v["cost_usd"] for k, v in claude["cost_state"]["by_model"].items()
        if k.startswith("deepseek")
    )
    ds_tok = rec["deepseek_models_usd_at_deepseek_prices"]
    if ds_from_cs:
        print(f"  Крос-перевірка deepseek-частини: cost-state ${ds_from_cs:.2f} vs "
              f"передрук токенів за тарифом DeepSeek ${ds_tok:.2f} "
              f"(розбіжність {abs(ds_from_cs-ds_tok)/ds_from_cs*100:.1f}%)")
    else:
        print("  deepseek-моделей у cost-state немає")
    rows = [
        (v["input_tokens"], v["output_tokens"], v["cache_read_input_tokens"],
         v["cost_usd"])
        for k, v in claude["cost_state"]["by_model"].items() if k.startswith("deepseek")
    ]
    implied = implied_unit_prices(rows)
    if implied:
        print(f"  Які ціни реально зашиті в cost-state для deepseek (розв'язок системи): "
              f"in ${implied['input_per_1m']}/1M, out ${implied['output_per_1m']}/1M, "
              f"cache-read ${implied['cache_read_per_1m']}/1M")
        print("    -> це НЕ тариф DeepSeek з cost-waste.md; схоже на фолбек-прайс "
              "Claude Code для невідомої моделі."
              f" {claude['cost_state']['hasUnknownModelCost_sessions']} сесій мають "
              "hasUnknownModelCost=true.")
    print(f"  Разом 3 + deepseek(тариф DeepSeek): ${c + ds_tok:.2f} -- "
          f"проти cost-state ${a:.2f} "
          f"(розбіжність {abs(a-(c+ds_tok))/a*100:.1f}%)")
    return {"path1_cost_state": a, "path2_session_cost": b, "path3_recompute": c,
            "path3_recompute_if_all_cache_writes_5m":
                rec.get("total_usd_if_all_cache_writes_5m"),
            "path3_plus_deepseek": round(c + ds_tok, 4),
            "deepseek_cost_state": round(ds_from_cs, 4),
            "deepseek_recomputed": ds_tok,
            "deepseek_implied_unit_prices": implied,
            "intersection": inter,
            "pct_1_vs_2": round(abs(a - b) / a * 100, 2) if b else None,
            "pct_1_vs_3": round(abs(a - c) / a * 100, 2)}


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Витрати Claude Code і DSH без пастки переобліку стрімінгу."
    )
    ap.add_argument("--claude", action="store_true", help="лише Claude Code")
    ap.add_argument("--dsh", action="store_true", help="лише DSH")
    ap.add_argument("--all", action="store_true", help="обидва агенти")
    ap.add_argument("--json", action="store_true", help="машинний вивід (stdout)")
    ap.add_argument("--claude-dir", default=DEFAULT_CLAUDE_DIR)
    ap.add_argument("--dsh-dir", default=DEFAULT_DSH_DIR)
    ap.add_argument("--session-cost", default=None,
                    help="шлях до session-cost.jsonl (інакше -- автопошук)")
    args = ap.parse_args()

    if not (args.claude or args.dsh or args.all):
        args.all = True

    result = {}
    if args.claude or args.all:
        log("Читаю транскрипти Claude Code...")
        result["claude"] = collect_claude(args.claude_dir)
        sc_path = args.session_cost
        if sc_path is None:
            sc_path = next((p for p in SESSION_COST_CANDIDATES if os.path.exists(p)),
                           None)
        if sc_path and os.path.exists(sc_path):
            log(f"Читаю статуслайн {sc_path}...")
            result["session_cost"] = collect_session_cost(sc_path)
        else:
            result["session_cost"] = None
    if args.dsh or args.all:
        log("Читаю сесії DSH (zstd)...")
        result["dsh"] = collect_dsh(args.dsh_dir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    if "claude" in result:
        print_claude(result["claude"])
        print()
        print("=" * 78)
        print("ПЕРЕВІРКА: статуслайн .claude/logs/session-cost.jsonl")
        print("=" * 78)
        sc = result.get("session_cost")
        if sc:
            print(f"  {sc['path']}")
            print(f"  Записів: {fmt_int(sc['records'])}  |  сесій: {sc['sessions']}")
            print(f"  Сума per-session MAX: ${sc['total_usd_per_session_max']:.2f}")
            for s in sc["top5_sessions"]:
                print(f"    ${s['cost_usd']:>9.2f}  {s['session']}")
        else:
            print("  Файл не знайдено -- шлях 2 у звірці недоступний.")
        print_reconciliation(result["claude"], sc)
    if "dsh" in result:
        print_dsh(result["dsh"])


if __name__ == "__main__":
    main()
