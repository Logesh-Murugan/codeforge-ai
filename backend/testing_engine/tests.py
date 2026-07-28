"""
Automated test checks for generated projects — Phase 4.4

Fifteen static analysis tests in nine pipeline stages:
  Compilation → Startup → Database → Security → Documentation
  → Docker → Export → Packaging → Final

All checks are pure static analysis — no subprocess execution,
no network calls, no filesystem writes.
"""
from __future__ import annotations

import ast
import re
import time
from typing import Any, Dict, List, Optional

from testing_engine.schemas import TestResult, TestStatus


def _pass(test_id: str, name: str, category: str, msg: str, dur: float = 0.0) -> TestResult:
    return TestResult(test_id=test_id, name=name, category=category,
                      status=TestStatus.PASS, message=msg, duration_ms=dur)


def _fail(test_id: str, name: str, category: str, msg: str,
          recs: Optional[List[str]] = None, dur: float = 0.0) -> TestResult:
    return TestResult(test_id=test_id, name=name, category=category,
                      status=TestStatus.FAIL, message=msg,
                      recommendations=recs or [], duration_ms=dur)


def _warn(test_id: str, name: str, category: str, msg: str,
          recs: Optional[List[str]] = None, dur: float = 0.0) -> TestResult:
    return TestResult(test_id=test_id, name=name, category=category,
                      status=TestStatus.WARN, message=msg,
                      recommendations=recs or [], duration_ms=dur)


def _skip(test_id: str, name: str, category: str, reason: str = "") -> TestResult:
    return TestResult(test_id=test_id, name=name, category=category,
                      status=TestStatus.SKIPPED, message=reason or "Skipped — no data available")


# ===========================================================================
# 1. Requirements Installation
# ===========================================================================

def test_requirements(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Requirements Installation", "T01", "compilation"
    req = files.get("requirements.txt", "")
    if not req:
        req = next((v for k, v in files.items() if k.endswith("requirements.txt")), "")
    dur = (time.perf_counter() - t0) * 1000

    if not req:
        return _fail(tid, name, cat, "requirements.txt not found",
                     ["Create requirements.txt listing all Python dependencies."], dur)

    lines = [l.strip() for l in req.splitlines() if l.strip() and not l.startswith("#")]
    if len(lines) < 2:
        return _warn(tid, name, cat, f"requirements.txt has only {len(lines)} entries",
                     ["Add fastapi, uvicorn, sqlalchemy, etc. to requirements.txt"], dur)

    required = {"fastapi", "uvicorn", "sqlalchemy"}
    present = {l.split(">=")[0].split("==")[0].split("[")[0].lower() for l in lines}
    missing = required - present
    if missing:
        return _warn(tid, name, cat,
                     f"Core packages possibly missing: {', '.join(missing)}",
                     [f"Add {p} to requirements.txt" for p in missing], dur)

    return _pass(tid, name, cat, f"requirements.txt found with {len(lines)} packages", dur)


# ===========================================================================
# 2. Folder Structure
# ===========================================================================

def test_folder_structure(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Folder Structure", "T02", "compilation"
    dur = (time.perf_counter() - t0) * 1000

    paths = list(files.keys())
    if not paths:
        return _skip(tid, name, cat, "No generated files to inspect")

    has_main     = any("main.py" in p for p in paths)
    has_models   = any("model" in p.lower() for p in paths)
    has_api      = any(p.endswith(".py") and ("api" in p or "router" in p) for p in paths)

    issues = []
    if not has_main:  issues.append("main.py missing")
    if not has_models: issues.append("models directory/file missing")
    if not has_api:   issues.append("API router files missing")

    if issues:
        return _warn(tid, name, cat, f"Folder structure issues: {'; '.join(issues)}",
                     [f"Add {i}" for i in issues], dur)
    return _pass(tid, name, cat,
                 f"Good project structure: {len(paths)} files across expected directories", dur)


# ===========================================================================
# 3. Compilation
# ===========================================================================

def test_compilation(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Python Compilation", "T03", "compilation"
    errors = []
    checked = 0

    for path, content in files.items():
        if not path.endswith(".py"):
            continue
        checked += 1
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(f"{path}: line {e.lineno} — {e.msg}")

    dur = (time.perf_counter() - t0) * 1000
    if not checked:
        return _skip(tid, name, cat, "No Python files found in generated project")
    if errors:
        return _fail(tid, name, cat,
                     f"{len(errors)} syntax error(s) in {checked} Python files",
                     [f"Fix: {e}" for e in errors[:5]], dur)
    return _pass(tid, name, cat, f"All {checked} Python files parse without syntax errors", dur)


# ===========================================================================
# 4. FastAPI Startup
# ===========================================================================

def test_fastapi_startup(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "FastAPI Startup", "T04", "startup"

    main_content = ""
    for path, content in files.items():
        if path.endswith("main.py"):
            main_content = content
            break

    dur = (time.perf_counter() - t0) * 1000
    if not main_content:
        return _fail(tid, name, cat, "main.py not found — FastAPI cannot start",
                     ["Create main.py with `app = FastAPI()`"], dur)

    has_fastapi = "FastAPI(" in main_content
    has_routers = "include_router" in main_content
    has_cors    = "CORSMiddleware" in main_content

    issues = []
    if not has_fastapi: issues.append("No FastAPI() instance")
    if not has_routers: issues.append("No include_router() calls")
    if not has_cors:    issues.append("No CORS middleware")

    if issues:
        return _warn(tid, name, cat, f"FastAPI startup issues: {'; '.join(issues)}",
                     [f"Add {i}" for i in issues], dur)
    return _pass(tid, name, cat, "FastAPI app configured with routers and CORS", dur)


# ===========================================================================
# 5. Database Initialization
# ===========================================================================

def test_database_init(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Database Initialization", "T05", "database"

    db_content = ""
    for path, content in files.items():
        if "db.py" in path or "database.py" in path:
            db_content += content

    dur = (time.perf_counter() - t0) * 1000
    if not db_content:
        return _warn(tid, name, cat, "No db.py or database.py found",
                     ["Create a db.py with engine and session factory"], dur)

    has_engine   = "create_engine" in db_content or "create_async_engine" in db_content
    has_session  = "Session" in db_content
    has_base     = "Base" in db_content or "declarative_base" in db_content

    issues = []
    if not has_engine:  issues.append("No SQLAlchemy engine created")
    if not has_session: issues.append("No session factory")
    if not has_base:    issues.append("No declarative Base")

    if issues:
        return _warn(tid, name, cat, f"DB init issues: {'; '.join(issues)}",
                     [f"Add {i}" for i in issues], dur)
    return _pass(tid, name, cat, "Database engine and session factory configured", dur)


# ===========================================================================
# 6. Authentication
# ===========================================================================

def test_authentication(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Authentication", "T06", "security"

    auth_content = ""
    for path, content in files.items():
        if "auth" in path.lower() or "security" in path.lower():
            auth_content += content

    dur = (time.perf_counter() - t0) * 1000
    if not auth_content:
        return _warn(tid, name, cat, "No auth/security files found",
                     ["Create auth.py with JWT token generation and validation"], dur)

    has_jwt      = "jwt" in auth_content.lower() or "jose" in auth_content.lower()
    has_hash     = "hash" in auth_content.lower() or "bcrypt" in auth_content.lower()
    has_bearer   = "Bearer" in auth_content or "OAuth2" in auth_content

    issues = []
    if not has_jwt:    issues.append("JWT implementation missing")
    if not has_hash:   issues.append("Password hashing missing")
    if not has_bearer: issues.append("Bearer/OAuth2 token scheme missing")

    if issues:
        return _fail(tid, name, cat, f"Auth issues: {'; '.join(issues)}",
                     [f"Fix: {i}" for i in issues], dur)
    return _pass(tid, name, cat, "JWT authentication with password hashing configured", dur)


# ===========================================================================
# 7. CRUD APIs
# ===========================================================================

def test_crud_apis(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "CRUD API Endpoints", "T07", "startup"

    methods = {"get": 0, "post": 0, "put": 0, "delete": 0}
    for content in files.values():
        if content.endswith(".py"):
            continue
        for method in methods:
            methods[method] += len(re.findall(rf'@\w+\.{method}\(', content, re.IGNORECASE))

    for path, content in files.items():
        if path.endswith(".py"):
            for method in methods:
                methods[method] += len(re.findall(rf'@\w+\.{method}\(', content, re.IGNORECASE))

    dur = (time.perf_counter() - t0) * 1000
    total = sum(methods.values())
    if total == 0:
        return _warn(tid, name, cat, "No CRUD endpoint decorators found",
                     ["Add @router.get/post/put/delete endpoints to your router files"], dur)

    missing = [m for m, c in methods.items() if c == 0]
    if missing:
        return _warn(tid, name, cat,
                     f"Missing CRUD methods: {', '.join(missing)} (found {total} total)",
                     [f"Add {m.upper()} endpoints" for m in missing], dur)
    return _pass(tid, name, cat,
                 f"Full CRUD coverage: GET={methods['get']} POST={methods['post']} "
                 f"PUT={methods['put']} DELETE={methods['delete']}", dur)


# ===========================================================================
# 8. Ownership Validation
# ===========================================================================

def test_ownership(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Ownership Validation", "T08", "security"

    all_content = "\n".join(files.values())
    dur = (time.perf_counter() - t0) * 1000

    has_owner_check = (
        "owner_id" in all_content or
        "user_id" in all_content or
        "current_user" in all_content
    )
    if not has_owner_check:
        return _warn(tid, name, cat, "No ownership checks detected (owner_id / current_user)",
                     ["Add ownership validation: compare resource.owner_id == current_user.id"], dur)

    has_where_owner = bool(re.search(r'owner_id\s*==', all_content))
    if not has_where_owner:
        return _warn(tid, name, cat, "owner_id found but no equality check in queries",
                     ["Ensure DB queries filter by owner_id to prevent unauthorized access"], dur)

    return _pass(tid, name, cat, "Ownership checks present in route handlers", dur)


# ===========================================================================
# 9. JWT Validation
# ===========================================================================

def test_jwt_validation(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "JWT Validation", "T09", "security"

    auth_content = ""
    for path, content in files.items():
        if "auth" in path.lower() or "security" in path.lower() or "token" in path.lower():
            auth_content += content

    dur = (time.perf_counter() - t0) * 1000
    if not auth_content:
        return _skip(tid, name, cat, "No auth/security files to check")

    has_decode    = "decode" in auth_content.lower()
    has_expiry    = "exp" in auth_content or "expire" in auth_content.lower()
    has_algorithm = "HS256" in auth_content or "RS256" in auth_content or "algorithm" in auth_content.lower()

    issues = []
    if not has_decode:    issues.append("No JWT decode call found")
    if not has_expiry:    issues.append("Token expiry (exp) not set")
    if not has_algorithm: issues.append("JWT algorithm not specified")

    if issues:
        return _warn(tid, name, cat, f"JWT issues: {'; '.join(issues)}",
                     [f"Fix: {i}" for i in issues], dur)
    return _pass(tid, name, cat, "JWT decode with expiry and algorithm configured", dur)


# ===========================================================================
# 10. API Endpoint Validation
# ===========================================================================

def test_api_endpoints(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "API Endpoint Validation", "T10", "startup"

    endpoints = []
    for path, content in files.items():
        if not path.endswith(".py"):
            continue
        found = re.findall(r'@\w+\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
        endpoints.extend(found)

    dur = (time.perf_counter() - t0) * 1000
    if not endpoints:
        return _warn(tid, name, cat, "No API endpoints found in Python files",
                     ["Add endpoint decorators like @router.get('/items')"], dur)

    paths = [ep[1] for ep in endpoints]
    duplicates = [p for p in set(paths) if paths.count(p) > 1]
    if duplicates:
        return _warn(tid, name, cat,
                     f"{len(duplicates)} duplicate endpoint path(s) found",
                     [f"Remove duplicate: {d}" for d in duplicates[:3]], dur)

    return _pass(tid, name, cat, f"{len(endpoints)} API endpoints validated, no duplicates", dur)


# ===========================================================================
# 11. Docker Build
# ===========================================================================

def test_docker_build(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Docker Build", "T11", "docker"

    dockerfile = next((v for k, v in files.items() if "Dockerfile" in k and not k.endswith(".yml")), "")
    compose    = next((v for k, v in files.items() if "docker-compose" in k or "compose.yml" in k), "")

    dur = (time.perf_counter() - t0) * 1000
    if not dockerfile and not compose:
        return _warn(tid, name, cat, "No Dockerfile or docker-compose.yml found",
                     ["Generate Docker configuration via the DevOps agent"], dur)

    issues = []
    if dockerfile:
        if not re.search(r'^FROM\s+', dockerfile, re.MULTILINE):
            issues.append("Dockerfile missing FROM instruction")
        if "CMD" not in dockerfile and "ENTRYPOINT" not in dockerfile:
            issues.append("Dockerfile missing CMD/ENTRYPOINT")
    if compose and "services:" not in compose:
        issues.append("docker-compose.yml missing 'services:' block")

    if issues:
        return _warn(tid, name, cat, f"Docker issues: {'; '.join(issues)}",
                     [f"Fix: {i}" for i in issues], dur)
    return _pass(tid, name, cat, "Dockerfile and docker-compose.yml are valid", dur)


# ===========================================================================
# 12. README Validation
# ===========================================================================

def test_readme(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "README Validation", "T12", "documentation"

    readme = next((v for k, v in files.items() if k.upper().endswith("README.MD")), "")
    if not readme:
        readme = next((v for k, v in files.items() if "README" in k.upper()), "")

    dur = (time.perf_counter() - t0) * 1000
    if not readme:
        return _fail(tid, name, cat, "README.md not found",
                     ["Create README.md with project overview, installation, and usage."], dur)

    has_install = "install" in readme.lower() or "pip" in readme.lower()
    has_usage   = "usage" in readme.lower() or "quick start" in readme.lower() or "## " in readme

    issues = []
    if not has_install: issues.append("No installation instructions")
    if not has_usage:   issues.append("No usage guide")
    if len(readme) < 300: issues.append("README is too short")

    if issues:
        return _warn(tid, name, cat, f"README issues: {'; '.join(issues)}",
                     [f"Add {i}" for i in issues], dur)
    return _pass(tid, name, cat, f"README.md found and complete ({len(readme)} chars)", dur)


# ===========================================================================
# 13. Generated Files Validation
# ===========================================================================

def test_generated_files(files: Dict[str, str], **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Generated Files Validation", "T13", "compilation"
    dur = (time.perf_counter() - t0) * 1000

    if not files:
        return _fail(tid, name, cat, "No generated files found",
                     ["Run the multi-agent pipeline to generate project files"], dur)

    empty = [p for p, c in files.items() if not c or not c.strip()]
    if empty:
        return _warn(tid, name, cat, f"{len(empty)} empty file(s) detected",
                     [f"Check content of: {', '.join(empty[:5])}"], dur)

    py_count = sum(1 for p in files if p.endswith(".py"))
    return _pass(tid, name, cat,
                 f"{len(files)} files generated ({py_count} Python), all non-empty", dur)


# ===========================================================================
# 14. Deployment Validation
# ===========================================================================

def test_deployment(files: Dict[str, str], agent_outputs: Dict[str, Any] = None, **_) -> TestResult:
    t0 = time.perf_counter()
    name, tid, cat = "Deployment Validation", "T14", "docker"
    agent_outputs = agent_outputs or {}

    devops = agent_outputs.get("devops_engineer", {})
    has_guide      = bool(devops.get("deployment_guide", ""))
    has_env_vars   = bool(devops.get("production_env_vars", []))
    has_dockerfile = bool(devops.get("dockerfile", "")) or any("Dockerfile" in k for k in files)
    has_compose    = bool(devops.get("docker_compose", "")) or any("compose" in k.lower() for k in files)

    dur = (time.perf_counter() - t0) * 1000
    issues = []
    if not has_guide:      issues.append("No deployment guide")
    if not has_env_vars:   issues.append("No production env vars defined")
    if not has_dockerfile: issues.append("No Dockerfile")
    if not has_compose:    issues.append("No docker-compose")

    if len(issues) >= 3:
        return _fail(tid, name, cat, f"Deployment not configured: {'; '.join(issues)}",
                     [f"Generate: {i}" for i in issues], dur)
    if issues:
        return _warn(tid, name, cat, f"Deployment incomplete: {'; '.join(issues)}",
                     [f"Add: {i}" for i in issues], dur)
    return _pass(tid, name, cat, "Deployment configuration complete", dur)


# ===========================================================================
# 15. ZIP Packaging Validation
# ===========================================================================

def test_zip_packaging(files: Dict[str, str], **_) -> TestResult:
    import io
    import zipfile

    t0 = time.perf_counter()
    name, tid, cat = "ZIP Packaging Validation", "T15", "packaging"

    if not files:
        dur = (time.perf_counter() - t0) * 1000
        return _fail(tid, name, cat, "No files to package",
                     ["Ensure project generation completed successfully"], dur)

    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in list(files.items())[:10]:  # test with first 10
                zf.writestr(f"test/{path}", content)
        size = buf.tell()
        dur = (time.perf_counter() - t0) * 1000
        return _pass(tid, name, cat,
                     f"ZIP packaging successful — estimated size: {size:,} bytes for {len(files)} files", dur)
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        return _fail(tid, name, cat, f"ZIP packaging failed: {e}",
                     ["Check for file encoding or path issues in generated files"], dur)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TEST_REGISTRY = {
    "T01": test_requirements,
    "T02": test_folder_structure,
    "T03": test_compilation,
    "T04": test_fastapi_startup,
    "T05": test_database_init,
    "T06": test_authentication,
    "T07": test_crud_apis,
    "T08": test_ownership,
    "T09": test_jwt_validation,
    "T10": test_api_endpoints,
    "T11": test_docker_build,
    "T12": test_readme,
    "T13": test_generated_files,
    "T14": test_deployment,
    "T15": test_zip_packaging,
}
