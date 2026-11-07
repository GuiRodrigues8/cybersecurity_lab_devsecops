A static security review of the provided application source code
(baseline_secure_coding_api.py) has been conducted.
Findings Table
  ID        Title        Affected File, Function, &       Attacker-Controlled Input        Impact
Lines                                                                 
  VULN-01   Path Traversal / baseline_secure_coding_api.py,   path query parameter               Read arbitrary files
Arbitrary File   download_file(), lines 135--139  (flask.request.args.get("path"))   readable by the
Read                                                                                     application process on
the host filesystem.

  VULN-02   Missing          baseline_secure_coding_api.py,   JSON body payload (student_id,     Unauthorized creation
Authentication & update_grade(), lines 120--133   course_id, grade)                or modification of
Authorization on                                                                         student grades by
Grade                                                                                    unauthenticated users.
Modification                                                                             

  VULN-03   Broken Object    baseline_secure_coding_api.py,   student_id path parameter          Unauthorized exposure
Level            get_profile() & get_grades(),                                       of sensitive student
Authorization    lines 106--118                                                          personal identifiable
(BOLA) on                                                                                information (PII) and
Profiles and                                                                             academic records.
Grades                                                                                   

  VULN-04   Hardcoded        baseline_secure_coding_api.py,   None (static configuration)          Session forgery,
Cryptographic    line 8                                                                  tampering, and
Secret Key                                                                               privilege escalation if
session contents are
manipulated.
VULN-05   Verbose Error    baseline_secure_coding_api.py,   Arbitrary malformed requests causing Information leakage
Disclosure and   handle_error(), lines 141--147,  runtime exceptions                   regarding internal
Debug Mode       and line 150                                                            application logic, file
Enabled                                                                                  paths, and types.
Detailed Supporting Explanations
VULN-01: Path Traversal / Arbitrary File Read
1. Identifier & Title: VULN-01 - Path Traversal / Arbitrary File
   Read
2. Affected Location: baseline_secure_coding_api.py, function
   download_file(), lines 135--139.
3. Data-Flow Path: An attacker supplies an HTTP GET request to
   /files?path=../../etc/passwd. The input is retrieved via
   flask.request.args.get("path", "") (raw_path) and appended
   directly to MATERIALS_DIR using the pathlib division operator
   (MATERIALS_DIR / raw_path). This path is passed directly to
   flask.send_file(target).
4. Missing Control & Root Cause: The application lacks path
   normalization verification (e.g., ensuring the resolved target path
   strictly resides within MATERIALS_DIR via
   .resolve().is_relative_to(MATERIALS_DIR)). The root cause is blind
   trust in user-supplied path components combined with unsafe path
   concatenation.
5. Preconditions & Impact:
   - Preconditions: The application must have read permissions on
     target system files.
   - Impact: Confidentiality breach via disclosure of sensitive
     system or source code files.
6. Proposed Test: Send an HTTP request:
   GET /files?path=../../../../etc/passwd and check if the response
   returns the contents of /etc/passwd (confirm) or a 404/403/error
   response (reject).
7. Assumptions & Confidence: Demonstrated code fact. Confidence:
   High.
VULN-02: Missing Authentication & Authorization on Grade Modification
1. Identifier & Title: VULN-02 - Missing Authentication and
   Authorization on Grade Modification
2. Affected Location: baseline_secure_coding_api.py, function
   update_grade(), lines 120--133.
3. Data-Flow Path: An HTTP POST request is sent to /grades/update
   with a JSON payload. The application reads
   flask.request.get_json() without checking flask.session for
   authentication state or verifying whether the current user holds the
   professor or admin role.
4. Missing Control & Root Cause: Absence of session validation
   checks and Role-Based Access Control (RBAC) checks on the
   /grades/update route handler. The root cause is omitting decorator
   or conditional guards restricting write actions to privileged users.
5. Preconditions & Impact:
   - Preconditions: None (endpoint is publicly accessible without a
     session token).
   - Impact: Integrity compromise; unauthenticated users can
     arbitrarily create or modify student grades.
6. Proposed Test: Send an unauthenticated POST /grades/update
   with JSON {"student_id": 1001, "course_id": "SRS", "grade": 20}
   and verify if the grade is updated or added successfully (confirm).
7. Assumptions & Confidence: Demonstrated code fact. Confidence:
   High.
VULN-04: Hardcoded Cryptographic Secret Key
1. Identifier & Title: VULN-04 - Hardcoded Cryptographic Secret Key
2. Affected Location: baseline_secure_coding_api.py, line 8
   (app.config["SECRET_KEY"] = "dev-secret-key").
3. Data-Flow Path: Flask uses app.config["SECRET_KEY"] to
   cryptographically sign session cookies stored on the client side.
4. Missing Control & Root Cause: Use of a predictable, hardcoded
   static secret key instead of loading a cryptographically secure
   random secret from environment variables or secure secret stores.
5. Preconditions & Impact:
   - Preconditions: Knowledge of the source code repository or
     default template values.
   - Impact: Attackers can decrypt, tamper with, or forge session
     cookies, allowing complete session hijacking and privilege
     escalation (e.g., forging a session with role="admin").
6. Proposed Test: Inspect source code / configuration defaults, or
   use a known secret cracking tool (like flask-unsign) with the
   string "dev-secret-key" against a captured session cookie to
   decode/forge session state.
7. Assumptions & Confidence: Demonstrated code fact. Confidence:
   High.
VULN-05: Verbose Error Disclosure and Debug Mode Enabled
1. Identifier & Title: VULN-05 - Verbose Error Disclosure and Debug
   Mode Enabled
2. Affected Location: baseline_secure_coding_api.py,
   handle_error() (lines 141--147) and execution block (line 150:
   app.run(debug=True, ...)).
3. Data-Flow Path: When an unhandled exception occurs anywhere in
   the application, handle_error catches it and returns a JSON
   response containing str(exc) and exc.__class__.__name__ with a
   500 status code. Additionally, debug=True is enabled when running
   locally.
4. Missing Control & Root Cause: Lack of sanitized generic error
   messaging for production environments and insecure development
   configurations enabled in production/deployment templates.
5. Preconditions & Impact:
   - Preconditions: An exception is triggered by malformed input.
   - Impact: Information disclosure assisting attackers in mapping
     internal application structures, database query failures, or
     library versions.
6. Proposed Test: Send a malformed payload or request that triggers
   an exception (e.g., sending a non-JSON body to /grades/update) and
   inspect whether raw exception details are returned in the JSON
   response body.
7. Assumptions & Confidence: Demonstrated code fact. Confidence:
   High.
