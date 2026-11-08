"""Deviation 20: a more realistic coding task.

Each deliverable is a small Python module that must satisfy a written spec and a
test file. Agents get a real `run_tests` tool that executes the tests against the
current module in a subprocess. A deliverable counts as complete only when its
tests actually pass. Constants vary per seed so the code differs across seeds.
"""

from __future__ import annotations

import hashlib
import os
import random
import subprocess
import sys
import tempfile
from functools import lru_cache

MODULES = {"D1": "pricing", "D2": "shipping", "D3": "inventory", "D4": "billing"}
FUNCS = {"D1": ["bulk_discount", "line_total", "parse_sku"],
         "D2": ["shipping_zone", "shipping_cost", "is_oversize"]}


def module_path(tid: str) -> str:
    return f"deliverables/{tid.lower()}_{MODULES[tid]}.py"


def _d1(rng):
    t_hi, t_lo = rng.choice([(100, 20), (50, 10), (200, 25), (120, 30)])
    r_hi, r_lo = rng.choice([(0.15, 0.05), (0.2, 0.1), (0.12, 0.04), (0.25, 0.08)])
    sep = rng.choice(["-", "/", ":"])
    spec = f"""# Task D1: pricing module

Write `{module_path('D1')}` defining exactly these three functions.

1. `bulk_discount(qty)` returns the discount rate for an integer quantity:
   {r_hi} if qty >= {t_hi}; {r_lo} if qty >= {t_lo}; otherwise 0.0.
2. `line_total(unit_price, qty)` returns unit_price * qty * (1 - bulk_discount(qty)),
   rounded to 2 decimal places.
3. `parse_sku(s)` parses a SKU of the form `CAT{sep}1234{sep}X`: an upper-case category
   of 2-4 letters, a 4-digit number and a one-letter variant, separated by `{sep}`.
   Return a dict {{"category": str, "number": int, "variant": str}}.
   Raise ValueError for anything else.

Run the tests with the run_tests tool (task_id "D1"). The task is complete when all pass.
"""
    tests = f"""from d1_pricing import bulk_discount, line_total, parse_sku

def test_discount():
    assert bulk_discount({t_hi}) == {r_hi}
    assert bulk_discount({t_hi - 1}) == {r_lo}
    assert bulk_discount({t_lo}) == {r_lo}
    assert bulk_discount({t_lo - 1}) == 0.0

def test_line_total():
    assert line_total(2.5, {t_lo - 1}) == round(2.5 * {t_lo - 1}, 2)
    assert line_total(3.0, {t_hi}) == round(3.0 * {t_hi} * (1 - {r_hi}), 2)

def test_parse_sku():
    assert parse_sku("AB{sep}0042{sep}Z") == {{"category": "AB", "number": 42, "variant": "Z"}}
    assert parse_sku("WXYZ{sep}9999{sep}A")["number"] == 9999
    for bad in ["ab{sep}0042{sep}Z", "AB{sep}42{sep}Z", "AB{sep}0042", "ABCDE{sep}0042{sep}Z", "AB{sep}0042{sep}ZZ"]:
        try:
            parse_sku(bad)
        except ValueError:
            continue
        raise AssertionError("accepted " + bad)
"""
    return spec, tests


def _d2(rng):
    zones = rng.choice([("US", "CA", "MX"), ("DE", "FR", "NL"), ("JP", "KR", "SG")])
    base = rng.choice([(5.0, 12.0, 25.0), (4.5, 9.0, 20.0), (6.0, 15.0, 30.0)])
    per_kg = rng.choice([1.2, 0.8, 1.5, 2.0])
    lim, tot = rng.choice([(120, 300), (100, 250), (150, 360)])
    spec = f"""# Task D2: shipping module

Write `{module_path('D2')}` defining exactly these three functions.

1. `shipping_zone(country_code)` returns 1 for {zones[0]}, 2 for {zones[1]} or {zones[2]},
   and 3 for any other code.
2. `shipping_cost(weight_kg, zone)` returns base + {per_kg} * weight_kg rounded to 2 decimals,
   where base is {base[0]} for zone 1, {base[1]} for zone 2 and {base[2]} for zone 3.
3. `is_oversize(l, w, h)` returns True if any dimension exceeds {lim} or l + w + h exceeds {tot}.

Run the tests with the run_tests tool (task_id "D2"). The task is complete when all pass.
"""
    tests = f"""from d2_shipping import shipping_zone, shipping_cost, is_oversize

def test_zone():
    assert shipping_zone("{zones[0]}") == 1
    assert shipping_zone("{zones[1]}") == 2 and shipping_zone("{zones[2]}") == 2
    assert shipping_zone("ZZ") == 3

def test_cost():
    assert shipping_cost(2, 1) == round({base[0]} + {per_kg} * 2, 2)
    assert shipping_cost(0.5, 3) == round({base[2]} + {per_kg} * 0.5, 2)

def test_oversize():
    assert is_oversize({lim + 1}, 1, 1) is True
    assert is_oversize({lim}, {lim}, {tot - 2 * lim}) is False
    assert is_oversize({lim}, {lim}, {tot - 2 * lim + 1}) is True
"""
    return spec, tests


def make_code_files(seed: int) -> dict[str, str]:
    rng = random.Random(20_000 + seed)
    s1, t1 = _d1(rng)
    s2, t2 = _d2(rng)
    return {
        "sources/d1/spec.md": s1, "sources/d1/test_d1.py": t1,
        "sources/d2/spec.md": s2, "sources/d2/test_d2.py": t2,
        "README.txt": ("Team workspace (Python repo).\n"
                       f"- {module_path('D1')}: task D1, spec in sources/d1/.\n"
                       f"- {module_path('D2')}: task D2, spec in sources/d2/.\n"
                       "A task is complete when its tests pass (run_tests tool).\n"),
    }


_RUNNER = """
import importlib, sys, traceback
sys.path.insert(0, '.')
t = importlib.import_module(sys.argv[1])
names = [n for n in dir(t) if n.startswith('test_')]
fails = 0
for n in names:
    try:
        getattr(t, n)()
        print('PASS', n)
    except Exception as e:
        fails += 1
        print('FAIL', n, type(e).__name__, str(e)[:200])
print('RESULT', len(names) - fails, 'passed', fails, 'failed')
sys.exit(1 if fails or not names else 0)
"""


@lru_cache(maxsize=4096)
def _run(module_src: str, test_src: str, tid: str) -> tuple[bool, str]:
    mod = f"{tid.lower()}_{MODULES[tid]}"
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, f"{mod}.py"), "w").write(module_src)
        open(os.path.join(d, f"test_{tid.lower()}.py"), "w").write(test_src)
        open(os.path.join(d, "_runner.py"), "w").write(_RUNNER)
        try:
            p = subprocess.run([sys.executable, "-I", "_runner.py", f"test_{tid.lower()}"], cwd=d,
                               capture_output=True, text=True, timeout=10,
                               env={"PATH": os.environ.get("PATH", "")})
            out = (p.stdout + p.stderr)[-1500:]
            return p.returncode == 0, out
        except subprocess.TimeoutExpired:
            return False, "Timed out after 10 s."


def run_tests(module_src: str, seed: int, tid: str) -> tuple[bool, str]:
    files = make_code_files(seed)
    return _run(module_src, files[f"sources/{tid.lower()}/test_{tid.lower()}.py"], tid)


def passes(module_src, seed: int, tid: str) -> bool:
    if not isinstance(module_src, str) or "def " not in module_src:
        return False
    return run_tests(module_src, seed, tid)[0]
