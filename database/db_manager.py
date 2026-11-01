"""
RailSamiksha AI — Database Manager & SQLite Engine
==================================================
Manages the relational SQL database (SQLite/PostgreSQL) for:
- User Authentication & RBAC accounts
- Flight Surveys & GIS Waypoints
- AI Defect Detections & IRPWM Remedial Standard Codes
- Field Gang Defect Clearance Tracking
- Indian Railways Track Management System (TMS) CSV Reports
"""

import sqlite3
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "railsamiksha.db"
SCHEMA_PATH = DB_DIR / "schema.sql"

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_password(password: str, salt: str = "railsamiksha_salt_2026") -> str:
    """Hashes a password using SHA-256 with project salt."""
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def init_database(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH, verbose: bool = True):
    """Initializes the database using schema.sql."""
    if verbose:
        print(f"[DB] Initializing database at {db_path} ...")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    conn = get_connection(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        if verbose:
            print("[DB] ✓ Database initialized and seeded successfully.")
    finally:
        conn.close()

def verify_user_login(identifier: str, password: str, db_path: Path = DB_PATH):
    """Authenticates a user by email or username."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email, password_hash, full_name, role, role_label, division, employee_id, avatar, is_active
            FROM users
            WHERE (email = ? OR username = ?) AND is_active = 1
        """, (identifier.lower().strip(), identifier.lower().strip()))
        user = cur.fetchone()
        if not user:
            return None, "User not found or account disabled"
        
        expected_hash = hash_password(password)
        if user["password_hash"] != expected_hash:
            return None, "Invalid password"
        
        # Update last login
        cur.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.utcnow().isoformat(), user["id"]))
        conn.commit()
        
        user_dict = dict(user)
        del user_dict["password_hash"]
        return user_dict, None
    finally:
        conn.close()

def create_user(username: str, email: str, password: str, full_name: str, role: str, division: str, employee_id: str = None, db_path: Path = DB_PATH):
    """Registers a new user in the SQL database."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        user_id = f"USR-{int(datetime.utcnow().timestamp())}"
        pwd_hash = hash_password(password)
        
        role_labels = {
            "admin": "Super Admin (HQ)",
            "operator": "Field Drone Pilot",
            "clearance": "P-Way Field Gang"
        }
        avatars = {
            "admin": "👑",
            "operator": "🎮",
            "clearance": "🔧"
        }
        
        cur.execute("""
            INSERT INTO users (id, username, email, password_hash, full_name, role, role_label, division, employee_id, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            username.lower().strip(),
            email.lower().strip(),
            pwd_hash,
            full_name.strip(),
            role,
            role_labels.get(role, role),
            division.strip(),
            employee_id or f"IR-{role.upper()}-{user_id[-4:]}",
            avatars.get(role, "👤")
        ))
        conn.commit()
        return user_id, None
    except sqlite3.IntegrityError as e:
        return None, f"Username or email already exists: {str(e)}"
    finally:
        conn.close()

def list_all_surveys(db_path: Path = DB_PATH):
    """Fetches all surveys along with their defect counts and clearance percentages."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                s.id, s.corridor_name, s.survey_date, s.pilot_name, s.clearance_gang_name,
                s.status, s.status_label, s.status_badge_class, s.total_defects, s.cleared_defects,
                s.survey_coordinates_json
            FROM surveys s
            ORDER BY s.survey_date DESC, s.created_at DESC
        """)
        surveys = [dict(row) for row in cur.fetchall()]
        
        for s in surveys:
            # Fetch defects for this survey
            cur.execute("""
                SELECT 
                    d.id, d.defect_name, d.category, d.severity, d.confidence,
                    d.chainage, d.latitude, d.longitude, d.track_side, d.irpwm_action_code,
                    COALESCE(c.is_cleared, 0) AS is_cleared,
                    c.assigned_gang, c.irpwm_action_applied, c.repaired_at
                FROM defects d
                LEFT JOIN defect_clearances c ON d.id = c.defect_id
                WHERE d.survey_id = ?
                ORDER BY d.chainage_km ASC
            """, (s["id"],))
            s["defects"] = [dict(d) for d in cur.fetchall()]
            if s["survey_coordinates_json"]:
                try:
                    s["coordinates"] = json.loads(s["survey_coordinates_json"])
                except Exception:
                    s["coordinates"] = []
            else:
                s["coordinates"] = []
        return surveys
    finally:
        conn.close()

def mark_defect_cleared(defect_id: str, gang_name: str, je_name: str, action_taken: str, db_path: Path = DB_PATH):
    """Updates defect clearance status in SQL and recalculates survey status."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check clearance row
        cur.execute("SELECT id, survey_id FROM defect_clearances WHERE defect_id = ?", (defect_id,))
        row = cur.fetchone()
        
        if row:
            survey_id = row["survey_id"]
            cur.execute("""
                UPDATE defect_clearances 
                SET is_cleared = 1, assigned_gang = ?, irpwm_action_applied = ?, verified_by_je = ?, repaired_at = ?
                WHERE defect_id = ?
            """, (gang_name, action_taken, je_name, now, defect_id))
        else:
            # Look up survey_id from defects
            cur.execute("SELECT survey_id FROM defects WHERE id = ?", (defect_id,))
            d_row = cur.fetchone()
            if not d_row:
                return False, "Defect not found"
            survey_id = d_row["survey_id"]
            cur.execute("""
                INSERT INTO defect_clearances (id, defect_id, survey_id, assigned_gang, is_cleared, irpwm_action_applied, verified_by_je, repaired_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            """, (f"CLR-{defect_id}", defect_id, survey_id, gang_name, action_taken, je_name, now))
        
        # Update cleared_defects count on survey
        cur.execute("""
            SELECT COUNT(*) AS total, SUM(CASE WHEN c.is_cleared = 1 THEN 1 ELSE 0 END) AS cleared
            FROM defects d
            LEFT JOIN defect_clearances c ON d.id = c.defect_id
            WHERE d.survey_id = ?
        """, (survey_id,))
        counts = cur.fetchone()
        total = counts["total"]
        cleared = counts["cleared"] or 0
        
        if cleared == total and total > 0:
            new_status = "CLEARED_100%"
            new_label = "✓ 100% Cleared"
            new_badge = "badge-green"
            cleared_at = now
        else:
            new_status = "IN_CLEARANCE"
            new_label = f"In Progress ({int(cleared/total*100)}%)"
            new_badge = "badge-yellow"
            cleared_at = None
            
        cur.execute("""
            UPDATE surveys 
            SET cleared_defects = ?, status = ?, status_label = ?, status_badge_class = ?, cleared_at = ?
            WHERE id = ?
        """, (cleared, new_status, new_label, new_badge, cleared_at, survey_id))
        
        conn.commit()
        return True, None
    finally:
        conn.close()

def generate_and_save_survey_csv(survey_id: str, generated_by_user_id: str = "USR-001", db_path: Path = DB_PATH):
    """Generates a TMS-compliant CSV string and stores it in the survey_csv_reports SQL table."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, corridor_name, survey_date, pilot_name FROM surveys WHERE id = ?", (survey_id,))
        s = cur.fetchone()
        if not s:
            return None, "Survey not found"
        
        cur.execute("""
            SELECT d.id, d.defect_name, d.category, d.severity, d.chainage, d.latitude, d.longitude, d.irpwm_action_code,
                   COALESCE(c.is_cleared, 0) AS is_cleared
            FROM defects d
            LEFT JOIN defect_clearances c ON d.id = c.defect_id
            WHERE d.survey_id = ?
            ORDER BY d.chainage_km ASC
        """, (survey_id,))
        defects = cur.fetchall()
        
        csv_lines = [
            "Survey_ID,Corridor,Date,Defect_ID,Defect_Category,Severity,Chainage,Latitude,Longitude,IRPWM_Remedial_Standard,Clearance_Status"
        ]
        for d in defects:
            status_text = "CLEARED" if d["is_cleared"] == 1 else "PENDING"
            csv_lines.append(
                f'"{s["id"]}","{s["corridor_name"]}","{s["survey_date"]}","{d["id"]}","{d["defect_name"]}","{d["severity"]}","{d["chainage"]}",{d["latitude"]},{d["longitude"]},"{d["irpwm_action_code"]}","{status_text}"'
            )
        
        csv_content = "\n".join(csv_lines)
        file_name = f"RailSamiksha_TMS_{survey_id}.csv"
        file_size = len(csv_content.encode('utf-8'))
        sha256 = hashlib.sha256(csv_content.encode('utf-8')).hexdigest()
        report_id = f"REP-CSV-{survey_id[-8:]}"
        
        cur.execute("""
            INSERT OR REPLACE INTO survey_csv_reports (id, survey_id, report_type, file_name, file_size_bytes, sha256_checksum, total_records, csv_content, generated_by_user_id)
            VALUES (?, ?, 'INDIAN_RAILWAYS_TMS_STANDARD', ?, ?, ?, ?, ?, ?)
        """, (report_id, survey_id, file_name, file_size, sha256, len(defects), csv_content, generated_by_user_id))
        
        conn.commit()
        return {
            "report_id": report_id,
            "file_name": file_name,
            "file_size": file_size,
            "sha256": sha256,
            "total_records": len(defects),
            "csv_content": csv_content
        }, None
    finally:
        conn.close()

def get_database_stats(db_path: Path = DB_PATH):
    """Returns row counts and metadata across all relational tables."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        tables = [
            "users", "user_sessions", "audit_logs", "corridors", 
            "surveys", "defects", "defect_clearances", "survey_csv_reports", "track_safety_certificates"
        ]
        stats = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            stats[t] = cur.fetchone()[0]
        return stats
    finally:
        conn.close()

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("=" * 70)
    print("RailSamiksha AI - Database Engine CLI")
    print("=" * 70)
    init_database()
    stats = get_database_stats()
    print("\nDatabase Table Row Summary:")
    for table, count in stats.items():
        print(f"  * {table.ljust(26)} : {count} rows")
    
    print("\nVerifying Demo User Authentication:")
    for cred in [("admin@railsamiksha.gov.in", "admin123"), ("operator@railsamiksha.gov.in", "pilot123"), ("clearance@railsamiksha.gov.in", "gang123")]:
        u, err = verify_user_login(cred[0], cred[1])
        if u:
            print(f"  [PASS] {u['role_label'].ljust(24)} ({u['email']}) -> AUTH SUCCESSFUL")
        else:
            print(f"  [FAIL] {cred[0]} -> FAILED ({err})")
    print("=" * 70)
