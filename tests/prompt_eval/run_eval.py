"""
GustoBot Prompt 评测运行器（骨架）

用法:
  python -m tests.prompt_eval.run_eval --list
  python -m tests.prompt_eval.run_eval --case-file tests/prompt_eval/cases/L0_router.jsonl
  python -m tests.prompt_eval.run_eval --suite smoke
  python -m tests.prompt_eval.run_eval --layer E2E --priority P0 --report reports/eval.json

集成测试需设置 GUSTOBOT_RUN_INTEGRATION_TESTS=1 且配置 .env / Docker。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = Path(__file__).resolve().parent / "cases"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class CaseResult:
    case_id: str
    layer: str
    passed: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    actual: Dict[str, Any] = field(default_factory=dict)
    expected: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    response_preview: str = ""


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cases.append(json.loads(line))
    return cases


def discover_case_files() -> List[Path]:
    return sorted(CASES_DIR.glob("*.jsonl"))


def filter_cases(
    cases: Iterable[Dict[str, Any]],
    *,
    layer: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in cases:
        if layer and c.get("layer") != layer:
            continue
        if priority and c.get("priority") != priority:
            continue
        if tags:
            case_tags = set(c.get("tags") or [])
            if not case_tags.intersection(tags):
                continue
        out.append(c)
    return out


def check_must_strings(text: str, must: List[str], must_not: List[str]) -> Dict[str, bool]:
    checks: Dict[str, bool] = {}
    lowered = text.lower()
    for s in must or []:
        checks[f"must_contain:{s}"] = s.lower() in lowered or s in text
    for s in must_not or []:
        checks[f"must_not_contain:{s}"] = not (s.lower() in lowered or s in text)
    return checks


def evaluate_router(actual: str, expected: str, acceptable: Optional[List[str]] = None) -> bool:
    if actual == expected:
        return True
    if acceptable and actual in acceptable:
        return True
    return False


async def run_e2e_case(case: Dict[str, Any]) -> CaseResult:
    from langchain_core.messages import HumanMessage
    from gustobot.application.agents.lg_builder import graph

    inp = case.get("input") or {}
    exp = case.get("expected") or {}
    hints = case.get("eval_hints") or {}
    session_id = inp.get("session_id") or f"prompt_eval_{case['case_id']}"

    config = {
        "configurable": {
            "thread_id": session_id,
            "image_path": inp.get("image_path"),
            "file_path": inp.get("file_path"),
            **(inp.get("config_overrides") or {}),
        }
    }

    messages = []
    for h in inp.get("history") or []:
        role = h.get("role", "user")
        if role in ("user", "human"):
            messages.append(HumanMessage(content=h.get("content", "")))
        else:
            from langchain_core.messages import AIMessage
            messages.append(AIMessage(content=h.get("content", "")))
    messages.append(HumanMessage(content=inp.get("message", "")))

    t0 = time.perf_counter()
    try:
        result = await graph.ainvoke({"messages": messages}, config=config)
        latency_ms = (time.perf_counter() - t0) * 1000

        router = result.get("router") or {}
        actual_route = router.get("type", "unknown")
        response_text = ""
        if result.get("messages"):
            response_text = result["messages"][-1].content or ""

        checks: Dict[str, bool] = {}
        expected_route = exp.get("router_type")
        if expected_route:
            checks["router_type"] = evaluate_router(
                actual_route,
                expected_route,
                hints.get("acceptable_router_types"),
            )

        checks.update(
            check_must_strings(
                response_text,
                exp.get("must_contain") or [],
                exp.get("must_not_contain") or [],
            )
        )

        passed = all(checks.values()) if checks else True

        return CaseResult(
            case_id=case["case_id"],
            layer=case.get("layer", "E2E"),
            passed=passed,
            checks=checks,
            actual={"router_type": actual_route, "logic": router.get("logic")},
            expected=exp,
            latency_ms=round(latency_ms, 1),
            response_preview=response_text[:300],
        )
    except Exception as exc:
        return CaseResult(
            case_id=case["case_id"],
            layer=case.get("layer", "E2E"),
            passed=False,
            error=str(exc),
            expected=exp,
        )


async def run_cases(cases: List[Dict[str, Any]], *, e2e_only: bool = False) -> List[CaseResult]:
    results: List[CaseResult] = []
    for case in cases:
        layer = case.get("layer", "")
        if e2e_only and layer != "E2E":
            results.append(
                CaseResult(
                    case_id=case["case_id"],
                    layer=layer,
                    passed=False,
                    error="skipped: use --layer or full integration for non-E2E",
                )
            )
            continue
        if layer == "E2E" or not e2e_only:
            results.append(await run_e2e_case(case))
    return results


def summarize(results: List[CaseResult]) -> Dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    by_layer: Dict[str, Dict[str, int]] = {}
    for r in results:
        bucket = by_layer.setdefault(r.layer, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if r.passed:
            bucket["passed"] += 1
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "by_layer": by_layer,
    }


def build_report(results: List[CaseResult]) -> Dict[str, Any]:
    return {
        "summary": summarize(results),
        "results": [asdict(r) for r in results],
    }


SUITE_MAP = {
    "smoke": {"priority": "P0"},
    "core": {"priority": None},
    "all": {"priority": None},
}


async def main_async(args: argparse.Namespace) -> int:
    if args.list:
        for p in discover_case_files():
            n = len(load_jsonl(p))
            print(f"{p.name}: {n} cases")
        return 0

    if args.case_file:
        paths = [Path(args.case_file)]
    else:
        paths = discover_case_files()
        if args.case_file_exclude_template:
            paths = [p for p in paths if not p.name.startswith("_")]

    all_cases: List[Dict[str, Any]] = []
    for p in paths:
        if p.name.startswith("_"):
            continue
        all_cases.extend(load_jsonl(p))

    suite_cfg = SUITE_MAP.get(args.suite or "", {})
    priority = args.priority or suite_cfg.get("priority")
    all_cases = filter_cases(
        all_cases,
        layer=args.layer,
        priority=priority,
        tags=args.tags.split(",") if args.tags else None,
    )

    if args.suite == "smoke":
        all_cases = [c for c in all_cases if c.get("priority") == "P0" or "smoke" in (c.get("tags") or [])]

    if not all_cases:
        print("No cases matched filters.")
        return 1

    print(f"Running {len(all_cases)} case(s)...")
    results = await run_cases(all_cases, e2e_only=bool(args.layer == "E2E" or args.e2e_only))

    report = build_report(results)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))

    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report written to {out}")

    failed = [r for r in results if not r.passed]
    for r in failed[:10]:
        print(f"FAIL {r.case_id}: {r.checks} error={r.error}")

    return 0 if report["summary"]["failed"] == 0 else 2


def main() -> None:
    parser = argparse.ArgumentParser(description="GustoBot prompt evaluation runner")
    parser.add_argument("--list", action="store_true", help="List case files")
    parser.add_argument("--case-file", type=str, help="Single JSONL file")
    parser.add_argument("--suite", choices=["smoke", "core", "all"], default="smoke")
    parser.add_argument("--layer", type=str, help="Filter by layer (e.g. E2E, L0_router)")
    parser.add_argument("--priority", choices=["P0", "P1", "P2"])
    parser.add_argument("--tags", type=str, help="Comma-separated tags")
    parser.add_argument("--report", type=str, help="Write JSON report path")
    parser.add_argument("--e2e-only", action="store_true", help="Only run E2E via full graph")
    parser.add_argument("--case-file-exclude-template", action="store_true", default=True)
    args = parser.parse_args()

    if not args.list and not os.getenv("GUSTOBOT_RUN_INTEGRATION_TESTS"):
        print(
            "Set GUSTOBOT_RUN_INTEGRATION_TESTS=1 to run live graph evaluation.\n"
            "Without it, use --list to inspect case inventory."
        )
        if args.list:
            for p in discover_case_files():
                print(f"  {p}")
        sys.exit(0)

    import asyncio
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
