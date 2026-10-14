"""
audit_project.py - Read-only project audit (Phase 8).
Run from the project root, with the backend virtual environment active:

    python audit_project.py

It only READS your files. It never changes anything.
[FAIL] = a real problem to fix.   [WARN] = please review.
"""
import importlib.util
import json
import os
import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
fails, warns = [], []


def ok(label):
    print(f"  [OK]   {label}")


def fail(label, hint=""):
    print(f"  [FAIL] {label}" + (f"  -> {hint}" if hint else ""))
    fails.append(label)


def warn(label, hint=""):
    print(f"  [WARN] {label}" + (f"  -> {hint}" if hint else ""))
    warns.append(label)


def check(label, condition, hint=""):
    ok(label) if condition else fail(label, hint)


def section(title):
    print(f"\n=== {title} ===")


def source_files(folder, patterns, skip=("node_modules", "venv", "__pycache__", "dist")):
    for pattern in patterns:
        for path in folder.rglob(pattern):
            if not any(part in skip for part in path.parts):
                yield path


# ---------------------------------------------------------------- 1. files
section("1. Required files")
backend_files = [
    "main.py", "database.py", "models.py", "schemas.py", "auth.py", "crud.py", "seed.py",
    "requirements.txt", "services/__init__.py", "services/skill_analyzer.py",
    "services/roadmap_generator.py", "data/career_skills.json",
    "tests/conftest.py", "tests/test_api.py", "tests/test_skill_analyzer.py",
]
for name in backend_files:
    check(f"backend/{name}", (BACKEND / name).exists(), "file is missing")

frontend_files = [
    "package.json", "index.html", "src/main.jsx", "src/App.jsx", "src/services/api.js",
    "src/context/AppContext.jsx",
]
pages = ["Login", "Register", "Dashboard", "StudentProfile", "CareerGoals", "SkillAssessment",
         "SkillGapAnalysis", "LearningRoadmap", "ProgressTracker"]
components = ["Navbar", "SkillCard", "ProgressChart", "RoadmapCard", "ProgressBar",
              "LoadingIndicator", "ErrorMessage"]
frontend_files += [f"src/pages/{p}.jsx" for p in pages]
frontend_files += [f"src/components/{c}.jsx" for c in components]
for name in frontend_files:
    check(f"frontend/{name}", (FRONTEND / name).exists(), "file is missing (renamed in Phase 7?)")

check("backend/temp_store.py is deleted", not (BACKEND / "temp_store.py").exists(),
      "Phase 4 said to delete it")
if not (BACKEND / "services" / "recommendation_engine.py").exists():
    warn("backend/services/recommendation_engine.py not found",
         "fine only if you put resource matching inside roadmap_generator.py")

# ---------------------------------------------------------------- 2. syntax
section("2. Python syntax")
bad = 0
for path in source_files(BACKEND, ["*.py"]):
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as error:
        bad += 1
        fail(f"syntax error in {path.relative_to(ROOT)}", str(error).strip().splitlines()[-1])
if bad == 0:
    ok("all backend .py files compile")

# ---------------------------------------------------------------- 3. imports + routes
section("3. Backend imports and routes")
backend_routes = set()
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
try:
    import main as backend_main  # noqa: E402

    ok("main.py imports without errors (so every import inside it resolves)")
    for route in backend_main.app.routes:
        for method in getattr(route, "methods", None) or []:
            backend_routes.add((method, route.path))
    required = [
        ("GET", "/"), ("GET", "/health"), ("POST", "/register"), ("POST", "/login"),
        ("GET", "/profile"), ("PUT", "/profile"), ("PUT", "/profile/career"),
        ("GET", "/careers"), ("GET", "/careers/{career_id}"),
        ("GET", "/assessment"), ("POST", "/assessment"), ("GET", "/skill-gap"),
        ("POST", "/roadmap"), ("GET", "/progress"), ("POST", "/progress"),
    ]
    for method, path in required:
        check(f"route {method} {path}", (method, path) in backend_routes, "route is missing")
except Exception as error:  # noqa: BLE001
    fail("main.py could not be imported", f"{type(error).__name__}: {error}")

# ---------------------------------------------------------------- 4. frontend -> backend paths
section("4. Frontend API calls match backend routes")
call_pattern = re.compile(r"""\.(get|post|put|delete|patch)\(\s*([`'"])(/[^`'"]*)\2""")
found_calls = set()
for path in source_files(FRONTEND / "src", ["*.js", "*.jsx"]):
    for method, _, url in call_pattern.findall(path.read_text(encoding="utf-8", errors="ignore")):
        url = re.sub(r"\$\{[^}]*\}", "{x}", url.split("?")[0])
        found_calls.add((method.upper(), url, path.name))

if not found_calls:
    warn("no Axios calls like apiClient.get('/careers') were found in frontend/src",
         "is the Phase 7 API connection in place, or does it use a different style?")
elif backend_routes:
    for method, url, filename in sorted(found_calls):
        matched = any(
            m == method and re.fullmatch(re.sub(r"\{[^}]+\}", "[^/]+", p), url)
            for m, p in backend_routes
        )
        check(f"{filename}: {method} {url}", matched, "no such backend route (wrong path or method)")

section("5. Leftover Phase 2 sample data")
for path in source_files(FRONTEND / "src" / "pages", ["*.jsx"]):
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "sampleData" in text:
        warn(f"{path.name} imports sampleData", "pages should use the real API after Phase 7")
api_js = FRONTEND / "src" / "services" / "api.js"
if api_js.exists():
    text = api_js.read_text(encoding="utf-8", errors="ignore")
    if "simulateRequest" in text:
        warn("api.js still contains simulateRequest", "fake data may still be used somewhere")
    check("api.js points to port 8000", "8000" in text, "base URL should be http://127.0.0.1:8000 or localhost:8000")

# ---------------------------------------------------------------- 6. dependencies
section("6. Dependencies")
backend_packages = {
    "fastapi": ("fastapi", ""), "uvicorn": ("uvicorn", "started from the command line"),
    "sqlalchemy": ("sqlalchemy", ""), "pydantic": ("pydantic", ""),
    "email-validator": ("email_validator", "used internally by EmailStr"),
    "pyjwt": ("jwt", ""), "bcrypt": ("bcrypt", ""), "pandas": ("pandas", ""),
    "scikit-learn": ("sklearn", "reserved for future work, intentionally unused"),
    "pytest": ("pytest", "tests"), "httpx": ("httpx", "needed by FastAPI TestClient"),
}
all_python = "\n".join(
    p.read_text(encoding="utf-8", errors="ignore") for p in source_files(BACKEND, ["*.py"])
)
for package, (module, note) in backend_packages.items():
    installed = importlib.util.find_spec(module) is not None
    used = re.search(rf"^\s*(import|from)\s+{module}\b", all_python, re.M) is not None
    if not installed:
        fail(f"{package} is not installed", "pip install -r requirements.txt")
    elif used:
        ok(f"{package}: installed and imported in code")
    else:
        print(f"  [INFO] {package}: installed, not imported directly" + (f" ({note})" if note else ""))

package_json = FRONTEND / "package.json"
if package_json.exists():
    dependencies = json.loads(package_json.read_text(encoding="utf-8")).get("dependencies", {})
    all_js = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in source_files(FRONTEND / "src", ["*.js", "*.jsx"])
    )
    for dependency in dependencies:
        if f"'{dependency}" in all_js or f'"{dependency}' in all_js:
            ok(f"frontend {dependency}: used")
        else:
            warn(f"frontend {dependency} is in package.json but never imported", "remove it if not needed")
    check("node_modules exists (npm install was run)", (FRONTEND / "node_modules").exists(),
          "run npm install in the frontend folder")

# ---------------------------------------------------------------- 7. config
section("7. Configuration")
gitignore = BACKEND / ".gitignore"
if gitignore.exists():
    content = gitignore.read_text(encoding="utf-8")
    check(".gitignore hides learning.db and .secret_key", "learning.db" in content and ".secret_key" in content)
check("requirements.txt lists pytest and httpx",
      (BACKEND / "requirements.txt").exists()
      and all(w in (BACKEND / "requirements.txt").read_text(encoding="utf-8") for w in ("pytest", "httpx")))
if "CORS_ORIGINS" in os.environ:
    warn("CORS_ORIGINS environment variable is set", f"value: {os.environ['CORS_ORIGINS']}")

print(f"\nSUMMARY: {len(fails)} FAIL, {len(warns)} WARN")
print("No FAIL items means the structure looks consistent. It does NOT prove the app works: run the tests.")
sys.exit(1 if fails else 0)