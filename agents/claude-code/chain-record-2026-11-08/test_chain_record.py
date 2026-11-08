"""Тести chain-record.py на копіях живих файлів (fixtures/, cp 2026-11-08).

Кожен тест працює в тимчасовій теці з копіями fixtures — самі fixtures
не змінюються. Запуск: python3 -m unittest -v test_chain_record
"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {"chain": "CHAIN.md", "prompt": "PROMPT-v3.md",
         "backlog": "BACKLOG.md", "gaps": "GAPS.md"}


def load_module():
    # 2026-11-08: ім'я файлу з дефісом — імпорт через importlib.
    spec = importlib.util.spec_from_file_location(
        "chain_record", os.path.join(HERE, "chain-record.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class ChainRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cr = load_module()

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="chain-record-test-")
        for name in NAMES.values():
            shutil.copy(os.path.join(HERE, "fixtures", name), self.tmp)
        self.before = {k: read(self.path(k)) for k in NAMES}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def path(self, key):
        return os.path.join(self.tmp, NAMES[key])

    def run_cli(self, *extra):
        argv = ["--root", self.tmp, "--date", "2026-11-08"]
        for key, name in NAMES.items():
            argv += [f"--{key}", name]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.cr.main(argv + list(extra))
        return code, out.getvalue(), err.getvalue()

    def changed_lines(self, key):
        old = self.before[key].splitlines()
        new = read(self.path(key)).splitlines()
        return old, new

    def row(self, text, link):
        lines = text.splitlines(keepends=True)
        return lines[self.cr.table_row_index(lines, link)]

    # --- запис ланки 5 з --passed ---
    def test_link5_passed_changes_only_its_row(self):
        code, out, _ = self.run_cli("--link", "5", "--decision", "сценарій Z обрано",
                                    "--passed", "--evidence", "5-scenariy-v3-full.md:1")
        self.assertEqual(code, 0, out)
        old, new = self.changed_lines("prompt")
        self.assertEqual(len(old), len(new))
        diff = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
        self.assertEqual(len(diff), 1, "у каркасі змінився не один рядок")
        self.assertEqual(new[diff[0]].rstrip("\n"),
                         self.row(read(self.path("prompt")), "5").rstrip("\n"))
        self.assertIn("08.11: C:48, 5-scenariy-v3-full.md:1 |", new[diff[0]])

    def test_link5_chain_and_backlog_plus_one(self):
        self.run_cli("--link", "5", "--decision", "сценарій Z обрано",
                     "--passed", "--evidence", "x.md:1")
        for key in ("chain", "backlog"):
            old, new = self.changed_lines(key)
            old_ne = [l for l in old if l.strip()]
            new_ne = [l for l in new if l.strip()]
            self.assertEqual(len(new_ne), len(old_ne) + 1, key)
        chain_new = read(self.path("chain"))
        self.assertTrue(chain_new.startswith(self.before["chain"]), "CHAIN — не лише дописування")
        self.assertTrue(chain_new.rstrip("\n").endswith(
            "Ланка 5 (08.11, сценарій Z обрано): x.md:1 — [claude-code, 2026-11-08]"))
        backlog = read(self.path("backlog")).splitlines()
        old_bl = self.before["backlog"].splitlines()
        anchor = next(i for i, l in enumerate(old_bl) if "ПЕРШИМ У НАСТУПНІЙ СЕСІЇ" in l)
        # після наявних підпунктів якоря (рядки з відступом), а не одразу під ним
        pos = next(i for i in range(anchor + 1, len(old_bl)) if not old_bl[i].startswith(" "))
        self.assertEqual(backlog[:pos], old_bl[:pos])
        self.assertEqual(backlog[pos + 1:], old_bl[pos:])
        self.assertEqual(backlog[pos],
                         "  - Статус змінився (08.11): ланка 5 — сценарій Z обрано")
        self.assertEqual(read(self.path("gaps")), self.before["gaps"], "GAPS змінено")

    def test_passed_replaces_mark_only_in_row(self):
        code, _, _ = self.run_cli("--link", "5б", "--decision", "розмітка зроблена",
                                  "--passed", "--evidence", "r.md:3")
        self.assertEqual(code, 0)
        new_row = self.row(read(self.path("prompt")), "5б")
        self.assertIn("[пройдено 08.11]", new_row)
        self.assertNotIn("не перевірено]", new_row)
        # інші рядки з позначкою (6, 8, …) не зачеплено
        self.assertEqual(self.row(read(self.path("prompt")), "6"),
                         self.row(self.before["prompt"], "6"))

    # --- помилки й dry-run ---
    def test_unknown_link_fails_and_writes_nothing(self):
        code, _, err = self.run_cli("--link", "99", "--decision", "x",
                                    "--evidence", "y")
        self.assertNotEqual(code, 0)
        self.assertIn("нема в таблиці", err)
        for key in NAMES:
            self.assertEqual(read(self.path(key)), self.before[key], key)

    def test_dry_run_writes_nothing(self):
        code, out, _ = self.run_cli("--link", "7", "--decision", "голос af_bella",
                                    "--passed", "--evidence", "golos/KEY.md:1",
                                    "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("+Ланка 7 (08.11, голос af_bella)", out)
        for key in NAMES:
            self.assertEqual(read(self.path(key)), self.before[key], key)

    def test_gaps_matching(self):
        text = ("- [ ] 2026-11-08 | ланка 5 не закрита | a\n"
                "- [ ] 2026-11-08 | ланка 5б окремо | b\n"
                "- [x] 2026-11-08 | ланка 5 закрита | c\n"
                "- [ ] 2026-11-08 | сценарій повної довжини | d\n")
        hits = [n for n, _ in self.cr.open_gaps(text, "5", "сценарій повної довжини")]
        self.assertEqual(hits, [1, 4])  # 5б і закритий [x] — не збіг

    # --- червоний на старому, зелений на новому ---
    def test_old_state_row_still_unverified(self):
        """Старий стан: ланку 5б пройшли б, але рядок каркаса досі «не перевірено»."""
        self.assertIn("не перевірено]", self.row(self.before["prompt"], "5б"))

    def test_lag_check_red_on_manual_append_green_via_script(self):
        lag_before = {n for n, _, _ in self.cr.lagging_entries(
            self.before["chain"], self.before["prompt"])}
        # старий спосіб: запис у CHAIN руками, каркас забули
        manual = self.before["chain"] + "\nЛанка 5 (08.11, руками): z — [claude-code, 2026-11-08]\n"
        lag_manual = {n for n, _, _ in self.cr.lagging_entries(manual, self.before["prompt"])}
        self.assertEqual(lag_manual - lag_before, {48}, "перевірка не впіймала відставання")
        # новий спосіб: скрипт
        self.run_cli("--link", "5", "--decision", "скриптом", "--evidence", "z")
        lag_script = {n for n, _, _ in self.cr.lagging_entries(
            read(self.path("chain")), read(self.path("prompt")))}
        self.assertEqual(lag_script, lag_before, "скрипт лишив нове відставання")

    def test_check_mode_exit_code(self):
        code, out, _ = self.run_cli("--check")
        self.assertEqual(code, 1 if "ВІДСТАЄ" in out else 0)

    def test_passed_without_evidence_rejected(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.run_cli("--link", "5", "--decision", "x", "--passed")
        for key in NAMES:
            self.assertEqual(read(self.path(key)), self.before[key], key)


if __name__ == "__main__":
    unittest.main()
