"""
RailSamiksha AI — Zero-Dependency SQL Backend REST API Server
=============================================================
Provides a lightweight HTTP/JSON bridge between the frontend and the SQLite database.
Endpoints:
  - GET  /api/status               - Database health & table metrics
  - POST /api/auth/login           - Authenticate against SQL users table
  - POST /api/auth/register        - Register new user into SQL users table
  - GET  /api/surveys              - Fetch all surveys with live defect data
  - POST /api/surveys/submit       - Submit survey for clearance
  - POST /api/defects/clear        - Clear defect and update IRPWM status in SQL
  - GET  /api/reports/csv          - Fetch TMS CSV content for a survey
  - GET  /api/reports/list         - List all stored CSV reports
  - GET  /api/db/export-schema     - Download raw schema.sql
"""

import http.server
import socketserver
import json
import urllib.parse
import sys
from pathlib import Path

# Add parent directory to path so db_manager can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import (
    get_connection,
    verify_user_login,
    create_user,
    list_all_surveys,
    mark_defect_cleared,
    generate_and_save_survey_csv,
    get_database_stats,
    DB_PATH,
    SCHEMA_PATH
)

PORT = 8000

class RailSamikshaAPIHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data, status_code=200):
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # GET /api/status
        if path == "/api/status":
            stats = get_database_stats()
            self._send_json({
                "status": "healthy",
                "database": "SQLite 3",
                "database_path": str(DB_PATH),
                "table_counts": stats
            })

        # GET /api/surveys
        elif path == "/api/surveys":
            surveys = list_all_surveys()
            self._send_json({"surveys": surveys})

        # GET /api/reports/list
        elif path == "/api/reports/list":
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, survey_id, report_type, file_name, file_size_bytes, sha256_checksum, total_records, generated_at
                    FROM survey_csv_reports
                    ORDER BY generated_at DESC
                """)
                reports = [dict(r) for r in cur.fetchall()]
                self._send_json({"reports": reports})
            finally:
                conn.close()

        # GET /api/reports/csv?survey_id=...
        elif path == "/api/reports/csv":
            survey_id = query.get("survey_id", [""])[0]
            if not survey_id:
                self._send_json({"error": "Missing survey_id parameter"}, 400)
                return
            
            rep, err = generate_and_save_survey_csv(survey_id)
            if err:
                self._send_json({"error": err}, 404)
            else:
                self._send_json(rep)

        # GET /api/db/export-schema
        elif path == "/api/db/export-schema":
            if SCHEMA_PATH.exists():
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    sql_text = f.read()
                body = sql_text.encode("utf-8")
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Disposition", "attachment; filename=\"schema.sql\"")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self._send_json({"error": "schema.sql not found"}, 404)

        else:
            self._send_json({"error": "Not Found", "path": path}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # POST /api/auth/login
        if path == "/api/auth/login":
            identifier = body.get("identifier", "")
            password = body.get("password", "")
            if not identifier or not password:
                self._send_json({"error": "Identifier and password required"}, 400)
                return

            user, err = verify_user_login(identifier, password)
            if user:
                self._send_json({"success": True, "user": user})
            else:
                self._send_json({"success": False, "error": err}, 401)

        # POST /api/auth/register
        elif path == "/api/auth/register":
            username = body.get("username", "")
            email = body.get("email", "")
            password = body.get("password", "")
            full_name = body.get("full_name", "")
            role = body.get("role", "operator")
            division = body.get("division", "")
            employee_id = body.get("employee_id", None)

            if not all([username, email, password, full_name, division]):
                self._send_json({"error": "All fields are required"}, 400)
                return

            user_id, err = create_user(username, email, password, full_name, role, division, employee_id)
            if user_id:
                user, _ = verify_user_login(username, password)
                self._send_json({"success": True, "user": user})
            else:
                self._send_json({"success": False, "error": err}, 400)

        # POST /api/defects/clear
        elif path == "/api/defects/clear":
            defect_id = body.get("defect_id", "")
            gang_name = body.get("gang_name", "Gang 12 (P-Way Agra)")
            je_name = body.get("je_name", "M. Kumar (JE P-Way)")
            action_taken = body.get("action_taken", "IRPWM remedial action applied")

            if not defect_id:
                self._send_json({"error": "Missing defect_id"}, 400)
                return

            ok, err = mark_defect_cleared(defect_id, gang_name, je_name, action_taken)
            if ok:
                self._send_json({"success": True, "defect_id": defect_id})
            else:
                self._send_json({"success": False, "error": err}, 400)

        else:
            self._send_json({"error": "Not Found", "path": path}, 404)

    def log_message(self, format, *args):
        # Concise logging
        print(f"[API] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

def run_server(port=PORT):
    server_address = ("", port)
    httpd = socketserver.TCPServer(server_address, RailSamikshaAPIHandler)
    print(f"[API] RailSamiksha SQL Backend Server listening on http://localhost:{port} ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] Server stopped.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
