"""
Individual category validators — Phase 4.2

Each validator receives a ProjectFiles object and returns a CategoryResult.
All validators perform purely static analysis — no subprocess execution.
"""
from __future__ import annotations

import re
from typing import List

from validation_engine.schemas import (
    CategoryResult,
    ProjectFiles,
    ValidationIssue,
    ValidationSeverity,
    ValidationStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _issue(
    category: str,
    severity: ValidationSeverity,
    code: str,
    message: str,
    file: str | None = None,
    recommendation: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        category=category,
        severity=severity,
        code=code,
        message=message,
        file=file,
        recommendation=recommendation,
    )


def _result(
    category: str,
    issues: List[ValidationIssue],
    checks_run: int,
) -> CategoryResult:
    errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
    checks_passed = checks_run - errors
    score = int((checks_passed / checks_run) * 100) if checks_run else 100
    status = ValidationStatus.PASS if errors == 0 else ValidationStatus.FAIL
    return CategoryResult(
        category=category,
        status=status,
        score=score,
        issues=issues,
        checks_run=checks_run,
        checks_passed=max(0, checks_passed),
    )


# ===========================================================================
# 1. Source Code Validator
# ===========================================================================

def validate_source_code(files: ProjectFiles) -> CategoryResult:
    CAT = "source_code"
    issues: List[ValidationIssue] = []
    checks = 0

    # Check for key structural files
    key_files = [
        ("main.py", "FastAPI entry point"),
        ("requirements.txt", "Python dependencies"),
    ]
    for fname, desc in key_files:
        checks += 1
        matches = files.find(fname)
        if not matches:
            issues.append(_issue(CAT, ValidationSeverity.WARNING, "MISSING_FILE",
                                 f"Expected {desc} not found: {fname}",
                                 recommendation=f"Create a {fname} at the project root."))

    # Check for .env.example
    checks += 1
    env_files = files.find(".env")
    env_example = files.find(".env.example")
    if not env_files and not env_example:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "MISSING_ENV",
                             "No .env or .env.example found",
                             recommendation="Add a .env.example listing all required environment variables."))

    # Check for obvious hardcoded secrets
    checks += 1
    secret_patterns = [r'SECRET_KEY\s*=\s*["\'][^"\']{3,}', r'password\s*=\s*["\'][^"\']{3,}',
                       r'API_KEY\s*=\s*["\'][^"\']{3,}']
    found_hardcoded = False
    for path, content in files.files.items():
        if path.endswith((".py", ".env", ".txt")):
            for pat in secret_patterns:
                if re.search(pat, content, re.IGNORECASE):
                    found_hardcoded = True
                    issues.append(_issue(CAT, ValidationSeverity.ERROR, "HARDCODED_SECRET",
                                         f"Possible hardcoded secret in {path}",
                                         file=path,
                                         recommendation="Move secrets to environment variables."))
                    break
    if not found_hardcoded:
        pass  # good

    # Check Python files parse (syntax check via compile)
    py_files = [p for p in files.files if p.endswith(".py")]
    for path in py_files[:20]:  # limit to first 20
        checks += 1
        content = files.content_of(path)
        try:
            compile(content, path, "exec")
        except SyntaxError as e:
            issues.append(_issue(CAT, ValidationSeverity.ERROR, "SYNTAX_ERROR",
                                 f"Syntax error in {path}: {e}",
                                 file=path,
                                 recommendation="Fix the syntax error in this file."))

    # Check for circular import patterns (basic)
    checks += 1
    import_graph: dict[str, list] = {}
    for path, content in files.files.items():
        if path.endswith(".py"):
            module = path.replace("/", ".").replace(".py", "")
            imports = re.findall(r'^from\s+([\w.]+)\s+import|^import\s+([\w.]+)', content, re.MULTILINE)
            import_graph[module] = [i[0] or i[1] for i in imports]

    return _result(CAT, issues, checks)


# ===========================================================================
# 2. FastAPI Validator
# ===========================================================================

def validate_fastapi(files: ProjectFiles) -> CategoryResult:
    CAT = "fastapi"
    issues: List[ValidationIssue] = []
    checks = 0

    # Find FastAPI app files
    main_files = files.find("main.py")
    checks += 1
    if not main_files:
        issues.append(_issue(CAT, ValidationSeverity.ERROR, "NO_MAIN",
                             "No main.py found — FastAPI app entry point missing",
                             recommendation="Create a main.py with FastAPI app instantiation."))

    # Check app instantiation
    checks += 1
    has_fastapi_app = False
    for path in main_files:
        content = files.content_of(path)
        if "FastAPI(" in content:
            has_fastapi_app = True
            break
    if not has_fastapi_app:
        issues.append(_issue(CAT, ValidationSeverity.ERROR, "NO_FASTAPI_APP",
                             "No FastAPI() instance found in main.py",
                             recommendation="Add `app = FastAPI()` to main.py."))

    # Check router registration
    checks += 1
    has_routers = False
    for path in main_files:
        content = files.content_of(path)
        if "include_router" in content:
            has_routers = True
            break
    if not has_routers:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_ROUTERS",
                             "No `app.include_router()` calls found",
                             recommendation="Register your API routers in main.py."))

    # Check CORS middleware
    checks += 1
    has_cors = False
    for path in main_files:
        if "CORSMiddleware" in files.content_of(path):
            has_cors = True
    if not has_cors:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_CORS",
                             "CORSMiddleware not configured",
                             recommendation="Add CORSMiddleware to allow frontend connections."))

    # Check router files have APIRouter
    router_files = files.find("router") + files.find("api/")
    checks += 1
    router_count = 0
    for path in router_files:
        if path.endswith(".py") and "APIRouter" in files.content_of(path):
            router_count += 1
    if router_count == 0 and router_files:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_API_ROUTER",
                             "Router files found but no APIRouter instances detected",
                             recommendation="Use `router = APIRouter()` in route modules."))

    # Check response models on endpoints
    checks += 1
    endpoints_without_response = 0
    for path, content in files.files.items():
        if path.endswith(".py"):
            # Simple heuristic: @router.get/post without response_model
            bare_decorators = re.findall(r'@router\.(get|post|put|delete|patch)\(["\'][^"\']+["\'][^)]*\)', content)
            with_model = re.findall(r'response_model', content)
            if len(bare_decorators) > len(with_model) + 2:
                endpoints_without_response += 1
    if endpoints_without_response > 2:
        issues.append(_issue(CAT, ValidationSeverity.INFO, "MISSING_RESPONSE_MODELS",
                             f"{endpoints_without_response} route files may lack response_model",
                             recommendation="Add response_model= to all endpoint decorators."))

    return _result(CAT, issues, checks)


# ===========================================================================
# 3. Database Validator
# ===========================================================================

def validate_database(files: ProjectFiles) -> CategoryResult:
    CAT = "database"
    issues: List[ValidationIssue] = []
    checks = 0

    # Check for SQLAlchemy models
    checks += 1
    model_files = files.find("model")
    has_models = any("Column" in files.content_of(p) or "Base" in files.content_of(p)
                     for p in model_files)
    if not has_models:
        issues.append(_issue(CAT, ValidationSeverity.ERROR, "NO_SQLALCHEMY_MODELS",
                             "No SQLAlchemy model definitions found",
                             recommendation="Create SQLAlchemy models with Base and Column definitions."))

    # Check for Base.metadata
    checks += 1
    has_base = any("declarative_base" in files.content_of(p) or "DeclarativeBase" in files.content_of(p)
                   for p in files.files)
    if not has_base:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_DECLARATIVE_BASE",
                             "declarative_base() not found",
                             recommendation="Use `Base = declarative_base()` from sqlalchemy.orm."))

    # Check for async engine
    checks += 1
    db_files = files.find("db.py") + files.find("database.py")
    has_async = any("create_async_engine" in files.content_of(p) or "AsyncSession" in files.content_of(p)
                    for p in db_files)
    if db_files and not has_async:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "SYNC_DB",
                             "Database engine appears to be synchronous",
                             recommendation="Use create_async_engine + AsyncSession for async FastAPI compatibility."))

    # Check for migrations (alembic)
    checks += 1
    has_alembic = bool(files.find("alembic") or files.find("migrations"))
    if not has_alembic:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_MIGRATIONS",
                             "No Alembic migrations directory found",
                             recommendation="Set up Alembic with `alembic init alembic`."))

    # Check for foreign key constraints
    checks += 1
    has_fk = any("ForeignKey" in files.content_of(p) for p in model_files)
    if model_files and not has_fk:
        issues.append(_issue(CAT, ValidationSeverity.INFO, "NO_FOREIGN_KEYS",
                             "No ForeignKey constraints found in models",
                             recommendation="Add ForeignKey relationships between related models."))

    return _result(CAT, issues, checks)


# ===========================================================================
# 4. Authentication Validator
# ===========================================================================

def validate_authentication(files: ProjectFiles) -> CategoryResult:
    CAT = "authentication"
    issues: List[ValidationIssue] = []
    checks = 0

    # Check for JWT handling
    checks += 1
    auth_files = files.find("auth") + files.find("security")
    has_jwt = any(
        "jwt" in files.content_of(p).lower() or "jose" in files.content_of(p).lower()
        for p in auth_files
    )
    if auth_files and not has_jwt:
        issues.append(_issue(CAT, ValidationSeverity.ERROR, "NO_JWT",
                             "No JWT library usage found in auth/security files",
                             recommendation="Use python-jose or PyJWT for JWT token generation and validation."))

    # Check for password hashing
    checks += 1
    has_password_hashing = any(
        "bcrypt" in files.content_of(p).lower() or "passlib" in files.content_of(p).lower()
        or "hash" in files.content_of(p).lower()
        for p in auth_files
    )
    if auth_files and not has_password_hashing:
        issues.append(_issue(CAT, ValidationSeverity.ERROR, "NO_PASSWORD_HASHING",
                             "No password hashing found in auth files",
                             recommendation="Use passlib with bcrypt to hash passwords before storage."))

    # Check for token expiry
    checks += 1
    has_expiry = any(
        "expire" in files.content_of(p).lower() or "exp" in files.content_of(p)
        for p in auth_files
    )
    if auth_files and not has_expiry:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_TOKEN_EXPIRY",
                             "Token expiry (exp claim) not found in JWT handling",
                             recommendation="Always set an expiry time on JWT tokens."))

    # Check for ownership/authorization patterns
    checks += 1
    router_files = [p for p in files.files if p.endswith(".py")]
    has_ownership = any(
        "owner_id" in files.content_of(p) or "current_user" in files.content_of(p)
        for p in router_files
    )
    if not has_ownership:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_OWNERSHIP_CHECK",
                             "No owner_id or current_user checks found in route handlers",
                             recommendation="Add ownership validation: verify resource belongs to authenticated user."))

    # Check for Depends(get_current_user) pattern
    checks += 1
    has_auth_dep = any(
        "get_current_user" in files.content_of(p) or "Depends" in files.content_of(p)
        for p in router_files
    )
    if not has_auth_dep:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_AUTH_DEPENDENCY",
                             "No FastAPI Depends authentication dependency found",
                             recommendation="Use `current_user = Depends(get_current_user)` on protected endpoints."))

    return _result(CAT, issues, checks)


# ===========================================================================
# 5. Documentation Validator
# ===========================================================================

def validate_documentation(files: ProjectFiles) -> CategoryResult:
    CAT = "documentation"
    issues: List[ValidationIssue] = []
    checks = 0

    # README
    checks += 1
    readme_files = files.find("README")
    if not readme_files:
        issues.append(_issue(CAT, ValidationSeverity.ERROR, "NO_README",
                             "README.md not found",
                             recommendation="Create a README.md with project overview, installation and usage instructions."))
    else:
        readme = files.content_of(readme_files[0])
        checks += 1
        if len(readme) < 200:
            issues.append(_issue(CAT, ValidationSeverity.WARNING, "THIN_README",
                                 "README.md is very short (< 200 chars)",
                                 file=readme_files[0],
                                 recommendation="Add project description, installation guide, and API usage examples."))

    # Installation instructions
    checks += 1
    has_install = any(
        "pip install" in files.content_of(p).lower() or "installation" in files.content_of(p).lower()
        for p in readme_files
    )
    if readme_files and not has_install:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_INSTALL_GUIDE",
                             "README lacks installation instructions",
                             recommendation="Add a ## Installation section with pip install / docker commands."))

    # API docs
    checks += 1
    has_api_docs = bool(files.find("API_Documentation") or files.find("api_docs") or files.find("openapi"))
    if not has_api_docs:
        issues.append(_issue(CAT, ValidationSeverity.INFO, "NO_API_DOCS",
                             "No API documentation file found",
                             recommendation="Generate API_Documentation.md using the Export Engine."))

    # Deployment guide
    checks += 1
    has_deploy = bool(files.find("Deployment") or files.find("deploy"))
    if not has_deploy:
        issues.append(_issue(CAT, ValidationSeverity.INFO, "NO_DEPLOY_GUIDE",
                             "No deployment guide found",
                             recommendation="Generate a Deployment_Guide.md with Docker and cloud deployment instructions."))

    return _result(CAT, issues, checks)


# ===========================================================================
# 6. Docker Validator
# ===========================================================================

def validate_docker(files: ProjectFiles) -> CategoryResult:
    CAT = "docker"
    issues: List[ValidationIssue] = []
    checks = 0

    # Dockerfile
    checks += 1
    dockerfile_paths = files.find("Dockerfile")
    if not dockerfile_paths:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_DOCKERFILE",
                             "Dockerfile not found",
                             recommendation="Create a Dockerfile for containerised deployment."))
    else:
        dockerfile = files.content_of(dockerfile_paths[0])
        # FROM instruction
        checks += 1
        if not re.search(r'^FROM\s+', dockerfile, re.MULTILINE):
            issues.append(_issue(CAT, ValidationSeverity.ERROR, "NO_FROM",
                                 "Dockerfile missing FROM instruction",
                                 file=dockerfile_paths[0],
                                 recommendation="Start Dockerfile with `FROM python:3.11-slim`."))
        # EXPOSE
        checks += 1
        if "EXPOSE" not in dockerfile:
            issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_EXPOSE",
                                 "Dockerfile missing EXPOSE instruction",
                                 file=dockerfile_paths[0],
                                 recommendation="Add `EXPOSE 8000` to document the port."))

    # Docker Compose
    checks += 1
    compose_paths = files.find("docker-compose") + files.find("compose.yml")
    if not compose_paths:
        issues.append(_issue(CAT, ValidationSeverity.WARNING, "NO_COMPOSE",
                             "docker-compose.yml not found",
                             recommendation="Create a docker-compose.yml for multi-service orchestration."))
    else:
        compose = files.content_of(compose_paths[0])
        checks += 1
        if "services:" not in compose:
            issues.append(_issue(CAT, ValidationSeverity.ERROR, "INVALID_COMPOSE",
                                 "docker-compose.yml missing 'services:' key",
                                 file=compose_paths[0],
                                 recommendation="Ensure docker-compose.yml has a 'services:' block."))

    # .dockerignore
    checks += 1
    if not files.find(".dockerignore"):
        issues.append(_issue(CAT, ValidationSeverity.INFO, "NO_DOCKERIGNORE",
                             ".dockerignore not found",
                             recommendation="Add a .dockerignore to reduce image build context size."))

    return _result(CAT, issues, checks)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

VALIDATOR_REGISTRY = {
    "source_code":     validate_source_code,
    "fastapi":         validate_fastapi,
    "database":        validate_database,
    "authentication":  validate_authentication,
    "documentation":   validate_documentation,
    "docker":          validate_docker,
}
