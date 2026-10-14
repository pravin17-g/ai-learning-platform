import json
from pathlib import Path

path = Path(__file__).parent / "data" / "career_skills.json"
data = json.loads(path.read_text(encoding="utf-8"))


def describe(value, indent=0, depth=0):
    pad = "  " * indent
    if isinstance(value, dict):
        print(f"{pad}dict with {len(value)} keys: {list(value)[:12]}")
        if depth < 3:
            for key in list(value)[:3]:
                print(f"{pad}- key '{key}':")
                describe(value[key], indent + 1, depth + 1)
    elif isinstance(value, list):
        print(f"{pad}list of {len(value)}")
        if value and depth < 3:
            describe(value[0], indent + 1, depth + 1)
    else:
        print(f"{pad}{type(value).__name__}: {str(value)[:70]!r}")


print("TOP-LEVEL KEYS:", list(data))
print()
describe(data)

careers = data["careers"]
first = careers[0] if isinstance(careers, list) else careers[list(careers)[0]]
print("\nFIRST CAREER (full, first 3000 characters):")
print(json.dumps(first, indent=1, ensure_ascii=False)[:3000])