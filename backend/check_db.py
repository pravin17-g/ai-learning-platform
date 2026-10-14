"""
check_db.py - Read-only look inside learning.db.
Run from the backend folder:   python check_db.py
It only READS. It never changes the database.
"""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "learning.db"

if not DB_FILE.exists():
    print("learning.db was not found. Start the backend once (uvicorn) so it can be created.")
    raise SystemExit(1)

con = sqlite3.connect(DB_FILE)

print(f"Database file: {DB_FILE}\n")

print("TABLE ROW COUNTS")
tables = con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
).fetchall()
for (table,) in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:<30}{count}")

print("\nCAREERS")
for row in con.execute("SELECT id, slug, career_name FROM careers ORDER BY id"):
    print("  ", row)

print("\nSTUDENTS (password shown only as the first 7 characters of its hash)")
for row in con.execute(
    "SELECT id, name, email, substr(password_hash, 1, 7), career_id FROM students ORDER BY id"
):
    print("  ", row)

print("\nSTUDENT RATINGS (student, skill, level)")
for row in con.execute(
    """SELECT st.id, st.name, sk.skill_name, ss.current_level
       FROM student_skills ss
       JOIN students st ON st.id = ss.student_id
       JOIN skills sk ON sk.id = ss.skill_id
       ORDER BY st.id, sk.id"""
):
    print("  ", row)

print("\nLEARNING PROGRESS (student, skill, status, progress %)")
for row in con.execute(
    """SELECT st.name, sk.skill_name, lp.status, lp.progress
       FROM learning_progress lp
       JOIN students st ON st.id = lp.student_id
       JOIN skills sk ON sk.id = lp.skill_id
       ORDER BY st.id, sk.id"""
):
    print("  ", row)

con.close()
