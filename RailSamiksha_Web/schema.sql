-- ============================================================================
-- RailSamiksha AI — Autonomous Aerial Track Inspection & P-Way Defect Platform
-- Indian Railways Track Management System (TMS) Relational Database Schema
-- Compatible with: SQLite 3, PostgreSQL 12+, MySQL 8.0+
-- ============================================================================

-- Disable foreign key checks during initialization (SQLite & MySQL compatible)
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. USERS & ROLE-BASED ACCESS CONTROL (RBAC)
-- ============================================================================

DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS track_safety_certificates;
DROP TABLE IF EXISTS survey_csv_reports;
DROP TABLE IF EXISTS defect_clearances;
DROP TABLE IF EXISTS defects;
DROP TABLE IF EXISTS surveys;
DROP TABLE IF EXISTS corridors;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    salt VARCHAR(64) DEFAULT 'railsamiksha_salt_2026',
    full_name VARCHAR(120) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'operator', 'clearance')),
    role_label VARCHAR(60) NOT NULL,
    division VARCHAR(120) NOT NULL,
    employee_id VARCHAR(50),
    avatar VARCHAR(10) DEFAULT '👤',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- 2. USER SESSIONS & TOKENS
-- ============================================================================

CREATE TABLE user_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_token VARCHAR(256) NOT NULL UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);

-- ============================================================================
-- 3. AUDIT & SYSTEM ACTION LOGS
-- ============================================================================

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(36),
    action VARCHAR(60) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50),
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at);

-- ============================================================================
-- 4. RAILWAY CORRIDORS & TRACK SECTIONS
-- ============================================================================

CREATE TABLE corridors (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    zone VARCHAR(50) NOT NULL,             -- e.g. 'Northern Railway (NR)'
    division VARCHAR(60) NOT NULL,         -- e.g. 'Delhi Division'
    start_chainage_km REAL NOT NULL,       -- e.g. 88.200
    end_chainage_km REAL NOT NULL,         -- e.g. 90.100
    track_gauge VARCHAR(30) DEFAULT 'Broad Gauge (1676mm)',
    line_category VARCHAR(30) DEFAULT 'Group A (Max 160 kmph)',
    electrification VARCHAR(30) DEFAULT '25 kV AC OHE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_corridors_division ON corridors(division);

-- ============================================================================
-- 5. DRONE AERIAL SURVEY MISSIONS
-- ============================================================================

CREATE TABLE surveys (
    id VARCHAR(36) PRIMARY KEY,            -- e.g. 'SURV-2026-001'
    corridor_id VARCHAR(36),
    corridor_name VARCHAR(150) NOT NULL,
    survey_date DATE NOT NULL,
    pilot_id VARCHAR(36),
    pilot_name VARCHAR(120) NOT NULL,
    clearance_gang_id VARCHAR(36),
    clearance_gang_name VARCHAR(120),
    drone_model VARCHAR(80) DEFAULT 'DJI Matrice 300 RTK - Dual 4K Thermal/RGB',
    flight_altitude_m REAL DEFAULT 4.80,
    flight_speed_mps REAL DEFAULT 3.20,
    ground_sampling_distance_mm REAL DEFAULT 0.65,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW' CHECK (status IN ('PENDING_REVIEW', 'SUBMITTED_FOR_CLEARANCE', 'IN_CLEARANCE', 'CLEARED_100%')),
    status_label VARCHAR(50) NOT NULL DEFAULT 'Review In Progress',
    status_badge_class VARCHAR(30) DEFAULT 'badge-purple',
    total_defects INTEGER DEFAULT 0,
    cleared_defects INTEGER DEFAULT 0,
    survey_coordinates_json TEXT,          -- GPS flight path waypoints [[lat, lon], ...]
    submitted_at TIMESTAMP,
    cleared_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (corridor_id) REFERENCES corridors(id) ON DELETE SET NULL,
    FOREIGN KEY (pilot_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_surveys_status ON surveys(status);
CREATE INDEX idx_surveys_date ON surveys(survey_date);
CREATE INDEX idx_surveys_pilot_id ON surveys(pilot_id);

-- ============================================================================
-- 6. DETECTED DEFECTS (RT-DETR-L HIGH-PRECISION INFERENCE)
-- ============================================================================

CREATE TABLE defects (
    id VARCHAR(36) PRIMARY KEY,            -- e.g. 'DEF-001-A'
    survey_id VARCHAR(36) NOT NULL,
    defect_name VARCHAR(80) NOT NULL,      -- e.g. 'Rail Crack', 'Missing Fastener'
    category VARCHAR(30) NOT NULL,         -- 'fastener', 'rail', 'sleeper', 'ballast', 'foreign_object'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    confidence REAL NOT NULL,              -- 0.000 to 1.000
    chainage VARCHAR(50) NOT NULL,         -- e.g. 'KM 88.350'
    chainage_km REAL,                      -- numeric KM for GIS sorting
    latitude REAL NOT NULL,                -- GPS lat e.g. 27.1772
    longitude REAL NOT NULL,               -- GPS lon e.g. 78.0090
    track_side VARCHAR(30) DEFAULT 'LEFT_RAIL' CHECK (track_side IN ('LEFT_RAIL', 'RIGHT_RAIL', 'CENTRAL_BALLAST', 'SLEEPER_CRIB')),
    irpwm_action_code VARCHAR(255) NOT NULL, -- Indian Railways P-Way Manual Para e.g. 'IRPWM Para 257: Replace Pandrol e-clip'
    bbox_x1 REAL,                          -- normalized / pixel coordinates
    bbox_y1 REAL,
    bbox_x2 REAL,
    bbox_y2 REAL,
    verified_by_pilot INTEGER NOT NULL DEFAULT 1,
    image_evidence_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE
);

CREATE INDEX idx_defects_survey_id ON defects(survey_id);
CREATE INDEX idx_defects_category ON defects(category);
CREATE INDEX idx_defects_severity ON defects(severity);
CREATE INDEX idx_defects_chainage_km ON defects(chainage_km);

-- ============================================================================
-- 7. DEFECT REMEDIATION & CLEARANCE TRACKING (P-WAY FIELD GANGS)
-- ============================================================================

CREATE TABLE defect_clearances (
    id VARCHAR(36) PRIMARY KEY,
    defect_id VARCHAR(36) NOT NULL UNIQUE,
    survey_id VARCHAR(36) NOT NULL,
    assigned_gang VARCHAR(100) NOT NULL,
    repaired_by_user_id VARCHAR(36),
    is_cleared INTEGER NOT NULL DEFAULT 0,
    irpwm_action_applied TEXT,
    repaired_at TIMESTAMP,
    verified_by_je VARCHAR(120),
    replacement_part_sr_no VARCHAR(100),
    post_repair_photo_url TEXT,
    gang_remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (defect_id) REFERENCES defects(id) ON DELETE CASCADE,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE,
    FOREIGN KEY (repaired_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_clearances_defect_id ON defect_clearances(defect_id);
CREATE INDEX idx_clearances_is_cleared ON defect_clearances(is_cleared);
CREATE INDEX idx_clearances_survey_id ON defect_clearances(survey_id);

-- ============================================================================
-- 8. CSV SURVEY REPORTS (INDIAN RAILWAYS TMS MASTER REPOSITORY)
-- ============================================================================

CREATE TABLE survey_csv_reports (
    id VARCHAR(36) PRIMARY KEY,            -- e.g. 'REP-CSV-2026-001'
    survey_id VARCHAR(36) NOT NULL,
    report_type VARCHAR(60) NOT NULL DEFAULT 'INDIAN_RAILWAYS_TMS_STANDARD',
    file_name VARCHAR(150) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    sha256_checksum VARCHAR(64) NOT NULL,
    total_records INTEGER NOT NULL,
    csv_content TEXT NOT NULL,             -- Full raw CSV content stored directly
    generated_by_user_id VARCHAR(36),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_count INTEGER DEFAULT 0,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE,
    FOREIGN KEY (generated_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_csv_survey_id ON survey_csv_reports(survey_id);
CREATE INDEX idx_csv_file_name ON survey_csv_reports(file_name);

-- ============================================================================
-- 9. TRACK SAFETY CERTIFICATES (FORM P-14)
-- ============================================================================

CREATE TABLE track_safety_certificates (
    id VARCHAR(36) PRIMARY KEY,
    certificate_no VARCHAR(80) NOT NULL UNIQUE, -- e.g. 'CERT-NR-DEL-2026-8812'
    survey_id VARCHAR(36) NOT NULL,
    corridor VARCHAR(150) NOT NULL,
    chainage_span VARCHAR(80) NOT NULL,
    certified_by VARCHAR(120) NOT NULL,
    certifier_designation VARCHAR(100) NOT NULL,
    certified_date DATE NOT NULL,
    safety_status VARCHAR(40) DEFAULT 'CERTIFIED_SAFE_FOR_FULL_SPEED',
    max_permissible_speed_kmph INTEGER DEFAULT 130,
    speed_restriction_notes TEXT,
    digital_signature_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE
);

CREATE INDEX idx_cert_survey_id ON track_safety_certificates(survey_id);
CREATE INDEX idx_cert_certificate_no ON track_safety_certificates(certificate_no);

-- ============================================================================
-- 10. ANALYTICAL VIEWS
-- ============================================================================

DROP VIEW IF EXISTS v_corridor_risk_analytics;
DROP VIEW IF EXISTS v_pending_clearance_punchlist;

-- View: Corridor Defect & Severity Summary
CREATE VIEW v_corridor_risk_analytics AS
SELECT 
    s.id AS survey_id,
    s.corridor_name,
    s.survey_date,
    s.status AS survey_status,
    s.total_defects,
    s.cleared_defects,
    ROUND((CAST(s.cleared_defects AS REAL) / MAX(s.total_defects, 1)) * 100, 1) AS clearance_pct,
    COUNT(CASE WHEN d.severity = 'CRITICAL' THEN 1 END) AS critical_defects,
    COUNT(CASE WHEN d.severity = 'HIGH' THEN 1 END) AS high_defects,
    COUNT(CASE WHEN d.severity = 'MEDIUM' THEN 1 END) AS medium_defects,
    COUNT(CASE WHEN d.severity = 'LOW' THEN 1 END) AS low_defects
FROM surveys s
LEFT JOIN defects d ON s.id = d.survey_id
GROUP BY s.id, s.corridor_name, s.survey_date, s.status, s.total_defects, s.cleared_defects;

-- View: Pending Field Gang Punch-List
CREATE VIEW v_pending_clearance_punchlist AS
SELECT 
    d.id AS defect_id,
    s.id AS survey_id,
    s.corridor_name,
    d.defect_name,
    d.category,
    d.severity,
    d.chainage,
    d.latitude,
    d.longitude,
    d.irpwm_action_code,
    c.assigned_gang,
    c.is_cleared
FROM defects d
JOIN surveys s ON d.survey_id = s.id
LEFT JOIN defect_clearances c ON d.id = c.defect_id
WHERE c.is_cleared = 0 OR c.is_cleared IS NULL
ORDER BY 
    CASE d.severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        ELSE 4 
    END;

-- ============================================================================
-- 11. DEFAULT SEED DATA (CORE USERS, CORRIDORS, HISTORICAL SURVEYS)
-- ============================================================================

-- Seed Users (Pre-hashed SHA-256 with salt 'railsamiksha_salt_2026')
-- admin123  -> fc28b87954a9d45f3c414417366fa40cd3d02fd8a31949bb911cfaa12bf7d286
-- pilot123  -> 217e97a26a8222c1a616f9245cf299eced094eb9c97181110851db8768f273ff
-- gang123   -> 146c912a5afdca2c4f50f0e2719f2bab5271f6a573edb3df4d3b3e93d90f42d3

INSERT INTO users (id, username, email, password_hash, full_name, role, role_label, division, employee_id, avatar)
VALUES 
('USR-001', 'superadmin', 'admin@railsamiksha.gov.in', 'fc28b87954a9d45f3c414417366fa40cd3d02fd8a31949bb911cfaa12bf7d286', 'Er. Rajesh Singhania', 'admin', 'Super Admin (HQ)', 'Railway Board & Northern Railway HQ', 'IR-HQ-7710', '👑'),
('USR-002', 'dronepilot', 'operator@railsamiksha.gov.in', '217e97a26a8222c1a616f9245cf299eced094eb9c97181110851db8768f273ff', 'Capt. A. Verma', 'operator', 'Field Drone Pilot', 'Northern Railway, Delhi Division', 'IR-PL-9921', '🎮'),
('USR-003', 'gang12', 'clearance@railsamiksha.gov.in', '146c912a5afdca2c4f50f0e2719f2bab5271f6a573edb3df4d3b3e93d90f42d3', 'M. Kumar (JE P-Way)', 'clearance', 'P-Way Field Gang 12', 'North Central Railway, Agra North', 'IR-JE-4412', '🔧');

-- Seed Corridors
INSERT INTO corridors (id, name, zone, division, start_chainage_km, end_chainage_km)
VALUES 
('CORR-001', 'Agra Cantt Fast-Line', 'NCR - North Central Railway', 'Agra Division', 88.200, 90.100),
('CORR-002', 'Delhi-Rewari Freight Corridor', 'NR - Northern Railway', 'Delhi Division', 14.000, 16.500),
('CORR-003', 'Kanpur Central Curve Section', 'NCR - North Central Railway', 'Prayagraj Division', 102.400, 103.800),
('CORR-LIVE', 'Tundla - Ghaziabad High Speed Loop', 'NCR - North Central Railway', 'Agra Division', 44.100, 45.800);

-- Seed Surveys
INSERT INTO surveys (id, corridor_id, corridor_name, survey_date, pilot_id, pilot_name, clearance_gang_name, status, status_label, status_badge_class, total_defects, cleared_defects, survey_coordinates_json, submitted_at, cleared_at)
VALUES 
('SURV-2026-001', 'CORR-001', 'Agra Cantt Fast-Line (KM 88.200 - 90.100)', '2026-10-30', 'USR-002', 'Capt. R. Sharma (IR-8821)', 'Gang 08 (JE P-Way M. Kumar)', 'CLEARED_100%', '✓ 100% Cleared', 'badge-green', 2, 2, '[[27.1767, 78.0081], [27.1780, 78.0105], [27.1802, 78.0140]]', '2026-10-30 11:30:00', '2026-10-30 15:45:00'),
('SURV-2026-002', 'CORR-002', 'Delhi-Rewari Freight (KM 14.000 - 16.500)', '2026-10-31', 'USR-002', 'Capt. A. Verma (IR-9921)', 'Gang 14 (JE P-Way D. Joshi)', 'IN_CLEARANCE', 'In Progress (50%)', 'badge-yellow', 2, 1, '[[28.4595, 77.0266], [28.4620, 77.0300], [28.4650, 77.0345]]', '2026-10-31 09:15:00', NULL),
('SURV-2026-003', 'CORR-003', 'Kanpur Central Curve (KM 102.400 - 103.800)', '2026-10-31', 'USR-002', 'Capt. S. Patil (IR-5542)', 'Gang 03 (JE P-Way R. Yadav)', 'CLEARED_100%', '✓ 100% Cleared', 'badge-green', 1, 1, '[[26.4499, 80.3319], [26.4520, 80.3350]]', '2026-10-31 16:00:00', '2026-10-31 18:30:00'),
('SURV-2026-LIVE', 'CORR-LIVE', 'Tundla - Ghaziabad Loop (KM 44.100 - 45.800)', '2026-11-01', 'USR-002', 'Capt. A. Verma (IR-9921)', 'Gang 12 (P-Way Agra)', 'SUBMITTED_FOR_CLEARANCE', 'Pending Clearance (0%)', 'badge-purple', 4, 0, '[[27.2050, 78.2390], [27.2085, 78.2435], [27.2120, 78.2480], [27.2160, 78.2530]]', '2026-11-01 10:15:00', NULL);

-- Seed Defects
INSERT INTO defects (id, survey_id, defect_name, category, severity, confidence, chainage, chainage_km, latitude, longitude, track_side, irpwm_action_code, verified_by_pilot)
VALUES 
('DEF-001-A', 'SURV-2026-001', 'Damaged Fastener', 'fastener', 'MEDIUM', 0.942, 'KM 88.350', 88.350, 27.1772, 78.0090, 'LEFT_RAIL', 'IRPWM Para 257: Replace Pandrol e-clip', 1),
('DEF-001-B', 'SURV-2026-001', 'Rail Wear', 'rail', 'LOW', 0.884, 'KM 89.120', 89.120, 27.1795, 78.0125, 'RIGHT_RAIL', 'IRPWM Para 302: Lubricate rail gauge face', 1),
('DEF-002-A', 'SURV-2026-002', 'Rail Joint Damage', 'rail', 'HIGH', 0.961, 'KM 14.620', 14.620, 28.4608, 77.0280, 'LEFT_RAIL', 'IRPWM Para 241: Re-torque fishplate bolts to 650 Nm', 1),
('DEF-002-B', 'SURV-2026-002', 'Ballast Defect', 'ballast', 'LOW', 0.915, 'KM 15.100', 15.100, 28.4635, 77.0320, 'CENTRAL_BALLAST', 'IRPWM Para 228: Replenish 250mm ballast cushion', 1),
('DEF-003-A', 'SURV-2026-003', 'Missing Fastener', 'fastener', 'HIGH', 0.953, 'KM 102.750', 102.750, 26.4510, 80.3335, 'RIGHT_RAIL', 'IRPWM Para 257: Insert missing ERC clip & liner', 1),
('DEF-LIVE-01', 'SURV-2026-LIVE', 'Rail Crack', 'rail', 'CRITICAL', 0.978, 'KM 44.250', 44.250, 27.2062, 78.2405, 'RIGHT_RAIL', 'IRPWM Para 268: Emergency fishplate clamping & 20 kmph stop order', 1),
('DEF-LIVE-02', 'SURV-2026-LIVE', 'Missing Fastener', 'fastener', 'HIGH', 0.942, 'KM 44.410', 44.410, 27.2078, 78.2422, 'LEFT_RAIL', 'IRPWM Para 257: Install standard ERC clip & rubber pad', 1),
('DEF-LIVE-03', 'SURV-2026-LIVE', 'Sleeper Defect', 'sleeper', 'MEDIUM', 0.912, 'KM 44.920', 44.920, 27.2105, 78.2458, 'SLEEPER_CRIB', 'IRPWM Para 234: Mark for spot sleeper replacement', 1),
('DEF-LIVE-04', 'SURV-2026-LIVE', 'Foreign Objects', 'foreign_object', 'MEDIUM', 0.985, 'KM 45.300', 45.300, 27.2140, 78.2505, 'CENTRAL_BALLAST', 'IRPWM Para 219: Immediate manual track clearance', 1);

-- Seed Defect Clearances
INSERT INTO defect_clearances (id, defect_id, survey_id, assigned_gang, is_cleared, irpwm_action_applied, repaired_at, verified_by_je, gang_remarks)
VALUES 
('CLR-001-A', 'DEF-001-A', 'SURV-2026-001', 'Gang 08', 1, 'Replaced damaged Pandrol e-clip with RDSO approved MK-III clip', '2026-10-30 14:22:00', 'M. Kumar (JE P-Way)', 'Track gauge verified at 1676mm'),
('CLR-001-B', 'DEF-001-B', 'SURV-2026-001', 'Gang 08', 1, 'Applied heavy grease lubrication to gauge face', '2026-10-30 15:40:00', 'M. Kumar (JE P-Way)', 'Within permissible wear tolerances'),
('CLR-002-A', 'DEF-002-A', 'SURV-2026-002', 'Gang 14', 1, 'Torqued all 4 fishbolts to 650 Nm with torque wrench', '2026-10-31 11:45:00', 'D. Joshi (JE P-Way)', 'Joint clearance verified at 4mm'),
('CLR-002-B', 'DEF-002-B', 'SURV-2026-002', 'Gang 14', 0, 'Ballast train scheduled for crib filling', NULL, NULL, 'Pending ballast train supply'),
('CLR-003-A', 'DEF-003-A', 'SURV-2026-003', 'Gang 03', 1, 'Fitted new ERC clip and glass-filled nylon liner', '2026-10-31 18:15:00', 'R. Yadav (JE P-Way)', 'Fastener toe load checked > 850 kg'),
('CLR-LIVE-01', 'DEF-LIVE-01', 'SURV-2026-LIVE', 'Gang 12', 0, 'Jogoggled fishplate clamp prepared for site deployment', NULL, NULL, 'Critical site alert broadcasted'),
('CLR-LIVE-02', 'DEF-LIVE-02', 'SURV-2026-LIVE', 'Gang 12', 0, 'Materials issued from Agra North P-Way depot', NULL, NULL, 'Pending field gang intervention'),
('CLR-LIVE-03', 'DEF-LIVE-03', 'SURV-2026-LIVE', 'Gang 12', 0, 'Sleeper marked with yellow fluorescent paint', NULL, NULL, 'Scheduled for night block'),
('CLR-LIVE-04', 'DEF-LIVE-04', 'SURV-2026-LIVE', 'Gang 12', 0, 'Gang trolley en route to KM 45.300', NULL, NULL, 'High priority clearance');

-- Seed CSV Reports
INSERT INTO survey_csv_reports (id, survey_id, report_type, file_name, file_size_bytes, sha256_checksum, total_records, csv_content, generated_by_user_id)
VALUES 
('REP-CSV-001', 'SURV-2026-001', 'INDIAN_RAILWAYS_TMS_STANDARD', 'RailSamiksha_TMS_SURV-2026-001.csv', 482, 'd4f5e889a7761001bcde99104fa2e1a34b22c8109d43ef10aa812300bde54321', 2, 
'Survey_ID,Corridor,Date,Defect_ID,Defect_Category,Severity,Chainage,Latitude,Longitude,IRPWM_Remedial_Standard,Clearance_Status
"SURV-2026-001","Agra Cantt Fast-Line (KM 88.200 - 90.100)","2026-10-30","DEF-001-A","Damaged Fastener","MEDIUM","KM 88.350",27.1772,78.0090,"IRPWM Para 257: Replace Pandrol e-clip","CLEARED"
"SURV-2026-001","Agra Cantt Fast-Line (KM 88.200 - 90.100)","2026-10-30","DEF-001-B","Rail Wear","LOW","KM 89.120",27.1795,78.0125,"IRPWM Para 302: Lubricate rail gauge face","CLEARED"', 'USR-001'),

('REP-CSV-002', 'SURV-2026-002', 'INDIAN_RAILWAYS_TMS_STANDARD', 'RailSamiksha_TMS_SURV-2026-002.csv', 510, 'c83210459aa831bce7812903fe4100dc89a34bc00912ef34aa11109988776655', 2, 
'Survey_ID,Corridor,Date,Defect_ID,Defect_Category,Severity,Chainage,Latitude,Longitude,IRPWM_Remedial_Standard,Clearance_Status
"SURV-2026-002","Delhi-Rewari Freight (KM 14.000 - 16.500)","2026-10-31","DEF-002-A","Rail Joint Damage","HIGH","KM 14.620",28.4608,77.0280,"IRPWM Para 241: Re-torque fishplate bolts to 650 Nm","CLEARED"
"SURV-2026-002","Delhi-Rewari Freight (KM 14.000 - 16.500)","2026-10-31","DEF-002-B","Ballast Defect","LOW","KM 15.100",28.4635,77.0320,"IRPWM Para 228: Replenish 250mm ballast cushion","PENDING"', 'USR-001'),

('REP-CSV-003', 'SURV-2026-003', 'INDIAN_RAILWAYS_TMS_STANDARD', 'RailSamiksha_TMS_SURV-2026-003.csv', 312, 'a7182903b41299cdef812345091234567890abcdef1234567890abcdef123456', 1, 
'Survey_ID,Corridor,Date,Defect_ID,Defect_Category,Severity,Chainage,Latitude,Longitude,IRPWM_Remedial_Standard,Clearance_Status
"SURV-2026-003","Kanpur Central Curve (KM 102.400 - 103.800)","2026-10-31","DEF-003-A","Missing Fastener","HIGH","KM 102.750",26.4510,80.3335,"IRPWM Para 257: Insert missing ERC clip & liner","CLEARED"', 'USR-001');

-- Seed Certificates
INSERT INTO track_safety_certificates (id, certificate_no, survey_id, corridor, chainage_span, certified_by, certifier_designation, certified_date, safety_status, max_permissible_speed_kmph, digital_signature_hash)
VALUES 
('CERT-001', 'CERT-NCR-AGRA-2026-8820', 'SURV-2026-001', 'Agra Cantt Fast-Line', 'KM 88.200 to KM 90.100', 'M. Kumar', 'Junior Engineer (P-Way), Agra Cantt', '2026-10-30', 'CERTIFIED_SAFE_FOR_FULL_SPEED', 130, 'e88129034bc77109284102ef192348b0a9912cde44109823ef1029384756abcd'),
('CERT-003', 'CERT-NCR-KANP-2026-1024', 'SURV-2026-003', 'Kanpur Central Curve Section', 'KM 102.400 to KM 103.800', 'R. Yadav', 'Junior Engineer (P-Way), Kanpur', '2026-10-31', 'CERTIFIED_SAFE_FOR_FULL_SPEED', 110, 'f993301294ba8821937401de203459c1b0023def55210934fa2130495867bcde');