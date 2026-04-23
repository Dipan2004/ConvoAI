import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_intent import run as run_intent
from tests.test_rag import run as run_rag
from tests.test_lead import run as run_lead
from tests.test_agent_flow import run as run_agent_flow


_RESET = "\033[0m"
_GREEN = "\033[92m"
_RED = "\033[91m"
_BOLD = "\033[1m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"


def _print_suite(name: str, passed: int, failed: list, duration: float) -> None:
    status = f"{_GREEN}PASS{_RESET}" if not failed else f"{_RED}FAIL{_RESET}"
    print(f"  {_BOLD}{name:<20}{_RESET}  {status}  {passed} passed  {len(failed)} failed  ({duration:.2f}s)")
    for fname, err in failed:
        print(f"    {_RED}✗{_RESET} {fname}")
        print(f"      {_YELLOW}{err}{_RESET}")


def run_all_tests() -> None:
    print(f"\n{_BOLD}{_CYAN}═══════════════════════════════════════{_RESET}")
    print(f"{_BOLD}{_CYAN}  AI AGENT SYSTEM — TEST SUITE{_RESET}")
    print(f"{_BOLD}{_CYAN}═══════════════════════════════════════{_RESET}\n")

    suites = [
        ("Intent Module", run_intent),
        ("RAG Module", run_rag),
        ("Lead Module", run_lead),
        ("Agent Flow", run_agent_flow),
    ]

    total_passed = 0
    total_failed: list = []
    suite_results = []

    for name, run_fn in suites:
        t0 = time.monotonic()
        try:
            passed, failed = run_fn()
        except Exception as exc:
            passed, failed = 0, [(name, str(exc))]
        duration = time.monotonic() - t0
        suite_results.append((name, passed, failed, duration))
        total_passed += passed
        total_failed.extend(failed)

    for name, passed, failed, duration in suite_results:
        _print_suite(name, passed, failed, duration)

    print(f"\n{_BOLD}═══════════════════════════════════════{_RESET}")
    total = total_passed + len(total_failed)
    if not total_failed:
        print(f"{_GREEN}{_BOLD}  ALL {total_passed} TESTS PASSED{_RESET}")
    else:
        print(f"{_RED}{_BOLD}  {len(total_failed)} FAILED / {total_passed} PASSED / {total} TOTAL{_RESET}")
    print(f"{_BOLD}═══════════════════════════════════════{_RESET}\n")

    sys.exit(1 if total_failed else 0)


if __name__ == "__main__":
    run_all_tests()