"""H2866 bypass census — a NEW paid call site must not be able to skip the policy.

The tests in `test_ai_spend_policy.py` prove the policy works on the two
routes that exist today. They say nothing about the third route somebody
adds in six months. This file is the structural half: it discovers paid
surfaces from the source tree and the live FastAPI app rather than from a
hand-maintained list, and fails when a new one appears outside the policy.

Three independent nets, because each catches a different mistake:

1. **Import census** — only `app.routers.ai` may import `ai_service`. A new
   router, background job or CLI that imports the provider helpers directly
   would bypass the route-level auth+quota gate.
2. **HTTP census** — only `ai_service` may name the provider endpoint or
   open an httpx client toward it. A second provider integration written
   from scratch would bypass the policy entirely.
3. **Route census** — every `/api/ai/*` route must depend on the H2772
   quota gate, and the single provider dispatch inside `ai_service` must be
   preceded by the H2866 policy call.

These are deliberately source-shaped assertions. They are annoying to a
developer adding a legitimate second provider path — which is exactly the
moment somebody should be forced to read this file and extend the policy
instead of quietly widening the bill.
"""
import ast
import pathlib

import pytest
from fastapi.routing import APIRoute

import app.routers.ai as ai_router
from app.main import app

APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"

#: The one module allowed to talk to a paid provider.
PROVIDER_MODULE = APP_DIR / "services" / "ai_service.py"

#: The one module allowed to import that module's calling helpers.
PAID_ROUTER = APP_DIR / "routers" / "ai.py"

#: Modules that legitimately reference `ai_service` for non-calling reasons
#: (prompt building, tests helpers). Kept explicit so adding one is a
#: reviewed decision, not a silent drift.
IMPORT_ALLOWLIST = {PAID_ROUTER, PROVIDER_MODULE}

#: Settings that only a provider-request builder has any use for.
PROVIDER_SETTINGS = {"AI_BASE_URL", "AI_API_KEY"}

#: Path fragment of the OpenAI-compatible endpoint.
PROVIDER_PATH = "chat/completions"


def _python_files() -> list[pathlib.Path]:
    return [
        p
        for p in APP_DIR.rglob("*.py")
        if "__pycache__" not in p.parts
    ]


def _imports_module(path: pathlib.Path, dotted: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(dotted):
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(dotted):
                    return True
    return False


def test_only_the_paid_router_imports_the_provider_service():
    offenders = sorted(
        str(p.relative_to(APP_DIR))
        for p in _python_files()
        if p not in IMPORT_ALLOWLIST and _imports_module(p, "app.services.ai_service")
    )
    assert offenders == [], (
        "a module outside app/routers/ai.py imports app.services.ai_service; "
        "route it through the paid router (auth + quota + spend policy) or add "
        "it to IMPORT_ALLOWLIST with a reviewed reason: " + ", ".join(offenders)
    )


def _builds_a_provider_request(path: pathlib.Path) -> bool:
    """True if this module reads the provider credentials/endpoint or names
    the chat-completions path *in code*.

    AST-based on purpose: `routers/ai.py` and `services/rate_limit.py` both
    discuss `AI_API_KEY` in their docstrings (that is the H2772 rationale,
    and deleting it to please a test would be the wrong trade). Prose is not
    a provider call; attribute access and string literals are.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in PROVIDER_SETTINGS:
            return True
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if PROVIDER_PATH in node.value and not _is_docstring(tree, node):
                return True
    return False


def _is_docstring(tree: ast.AST, target: ast.Constant) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and body[0].value is target:
                return True
    return False


def test_only_the_provider_service_names_the_provider_endpoint():
    # `settings.py` declares the fields; it issues no request. `ai_policy.py`
    # is deliberately NOT exempt — it must decide without ever holding the
    # credentials, and this test is what keeps that true.
    exempt = {PROVIDER_MODULE, APP_DIR / "settings.py"}
    offenders = [
        str(p.relative_to(APP_DIR))
        for p in _python_files()
        if p not in exempt and _builds_a_provider_request(p)
    ]
    assert sorted(offenders) == [], (
        "a module outside app/services/ai_service.py builds a provider request; "
        "every paid call must converge on _openai_chat so the H2866 policy sees "
        "it: " + ", ".join(sorted(offenders))
    )


def test_provider_dispatch_is_preceded_by_the_policy_call():
    """Inside `_openai_chat`, `evaluate_call` must appear before the HTTP post.

    Line-order on the AST, not a substring search, so reordering the
    function (the actual regression risk) fails the test.
    """
    tree = ast.parse(PROVIDER_MODULE.read_text(encoding="utf-8"))
    func = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef)) and n.name == "_openai_chat"
    )
    policy_lines = [
        n.lineno
        for n in ast.walk(func)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "evaluate_call"
    ]
    post_lines = [
        n.lineno
        for n in ast.walk(func)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "post"
    ]
    assert policy_lines, "_openai_chat no longer calls evaluate_call — the spend policy is bypassed"
    assert post_lines, "census is stale: _openai_chat no longer posts to a provider"
    assert min(policy_lines) < min(post_lines), (
        "the H2866 policy must be evaluated BEFORE the provider request, "
        "otherwise a rejection still costs money"
    )


def test_no_other_async_function_in_the_service_calls_the_provider():
    tree = ast.parse(PROVIDER_MODULE.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        if node.name == "_openai_chat":
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == "post"
            ):
                offenders.append(node.name)
    assert offenders == [], (
        "a second provider dispatch appeared in ai_service; all paid traffic must "
        "converge on _openai_chat: " + ", ".join(offenders)
    )


def _paid_routes() -> list[APIRoute]:
    return [
        r
        for r in app.routes
        if isinstance(r, APIRoute) and r.path.startswith("/api/ai")
    ]


def test_paid_routes_exist_so_the_census_is_not_vacuous():
    paths = sorted(r.path for r in _paid_routes())
    assert paths == ["/api/ai/compare-translations", "/api/ai/explain"], (
        "the set of paid AI routes changed; re-read H2866 and confirm the new "
        f"route is policy-covered before updating this list: {paths}"
    )


@pytest.mark.parametrize("route", _paid_routes(), ids=lambda r: r.path)
def test_every_paid_route_requires_auth_and_quota(route: APIRoute):
    """Walk the dependency tree; `_require_quota` must be in it."""
    seen = []
    stack = list(route.dependant.dependencies)
    while stack:
        dep = stack.pop()
        if dep.call is not None:
            seen.append(dep.call)
        stack.extend(dep.dependencies)
    assert ai_router._require_quota in seen, (
        f"{route.path} does not depend on _require_quota — it is reachable "
        "without a session and without consuming the monthly quota"
    )
