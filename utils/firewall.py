import re
from flask import request, render_template_string
from database import db, SecurityAlert

# Custom blocked page template featuring a premium cyber-security lock screen with animations
BLOCKED_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WAF Blocked - Broke Geniuses Security</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {
            background-color: #0b0f19;
            color: #f1f5f9;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .shield-card {
            background: rgba(17, 24, 39, 0.7);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 24px;
            padding: 3rem;
            max-width: 600px;
            width: 100%;
            text-align: center;
            backdrop-filter: blur(12px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), 0 0 50px rgba(239, 68, 68, 0.1);
        }
        .shield-icon-container {
            position: relative;
            width: 100px;
            height: 100px;
            margin: 0 auto 2rem;
        }
        .shield-icon {
            font-size: 5rem;
            color: #ef4444;
            animation: pulseShield 2s infinite ease-in-out;
        }
        .shield-glow {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: rgba(239, 68, 68, 0.3);
            filter: blur(20px);
            z-index: -1;
        }
        @keyframes pulseShield {
            0%, 100% { transform: scale(1); filter: drop-shadow(0 0 0px rgba(239, 68, 68, 0)); }
            50% { transform: scale(1.05); filter: drop-shadow(0 0 15px rgba(239, 68, 68, 0.6)); }
        }
        .tech-logs {
            background: #030712;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.8rem;
            color: #ef4444;
            text-align: left;
            margin-top: 1.5rem;
        }
    </style>
</head>
<body>
    <div class="shield-card">
        <div class="shield-icon-container">
            <div class="shield-glow"></div>
            <i class="bi bi-shield-slash-fill shield-icon"></i>
        </div>
        <h2 class="fw-bold text-danger mb-2">Request Blocked by WAF</h2>
        <h5 class="text-white mb-4">Web Application Security Shield Active</h5>
        <p class="text-muted small px-3">
            An incoming payload match has triggered the security protection system. Your request was identified as a potential security risk and has been terminated.
        </p>
        
        <div class="tech-logs">
            <strong>[SECURITY REPORT]</strong><br>
            Threat Category: {{ threat_type }}<br>
            Target Path: {{ path }}<br>
            Client IP: {{ ip }}<br>
            Timestamp: {{ timestamp }}
        </div>
        
        <div class="mt-4">
            <a href="/" class="btn btn-outline-light rounded-pill px-4 btn-sm">
                <i class="bi bi-arrow-left me-2"></i>Return to Homepage
            </a>
        </div>
    </div>
</body>
</html>
"""

# Common attack patterns
PATTERNS = {
    "SQL Injection": [
        r"(?i)\b(union\s+all\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table)\b",
        r"(?i)\b(or|and)\s+\d+=\d+\b",
        r"(?i)'.*?\b(or|and)\b.*?\d+=\d+",
    ],
    "Cross-Site Scripting (XSS)": [
        r"(?i)<\s*script[^>]*>",
        r"(?i)javascript\s*:",
        r"(?i)\bon(load|error|click|mouseover|focus|submit)\s*=",
        r"(?i)alert\s*\("
    ],
    "Path Traversal": [
        r"\.\./\.\.",
        r"\.\.\\\.\.",
        r"(?i)/etc/passwd",
        r"(?i)\bboot\.ini\b"
    ],
    "Malicious File Scanner": [
        r"(?i)\.(php|asp|aspx|jsp|cgi|pl|py)$",
        r"(?i)\b(wp-admin|wp-login|xmlrpc)\b"
    ]
}

def scan_input(text):
    """Scans a text payload against known WAF security patterns."""
    if not text or not isinstance(text, str):
        return None
    for threat, regex_list in PATTERNS.items():
        for regex in regex_list:
            if re.search(regex, text):
                return threat
    return None

def init_waf(app):
    """Registers the WAF before_request hook inside the Flask application context."""
    
    @app.before_request
    def waf_before_request():
        # Exclude static assets to optimize speed
        if request.path.startswith('/static/') or request.path == '/favicon.ico':
            return
            
        # Scan URL Path itself for malicious file probes or path traversal
        threat = scan_input(request.path)
        bad_payload = request.path
        
        # Scan GET parameters
        if not threat:
            for key, val in request.args.items():
                threat = scan_input(val)
                if threat:
                    bad_payload = f"{key}={val}"
                    break
                    
        # Scan POST parameters (Form data)
        if not threat and request.method == "POST":
            # Avoid breaking multipart uploads
            if not request.content_type or "multipart/form-data" not in request.content_type:
                try:
                    for key, val in request.form.items():
                        threat = scan_input(val)
                        if threat:
                            bad_payload = f"{key}={val}"
                            break
                except Exception:
                    pass
                    
            # Scan JSON post data if any
            if not threat and request.is_json:
                try:
                    json_data = request.get_json(silent=True)
                    if json_data:
                        # Flatten dictionary to inspect all string values
                        def check_dict(d):
                            for k, v in d.items():
                                if isinstance(v, str):
                                    t = scan_input(v)
                                    if t:
                                        return t, f"{k}={v}"
                                elif isinstance(v, dict):
                                    res = check_dict(v)
                                    if res:
                                        return res
                            return None
                        res = check_dict(json_data)
                        if res:
                            threat, bad_payload = res
                except Exception:
                    pass
                    
        # Block if a threat is matched
        if threat:
            from datetime import datetime
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Log the security alert to the DB
            try:
                alert = SecurityAlert(
                    ip_address=ip,
                    path=request.path,
                    method=request.method,
                    threat_type=threat,
                    payload=bad_payload[:250] # Truncate if long
                )
                db.session.add(alert)
                db.session.commit()
            except Exception as e:
                print(f"Error logging WAF alert: {e}")
                
            # Render the stylized blocked screen immediately
            return render_template_string(
                BLOCKED_TEMPLATE,
                threat_type=threat,
                path=request.path,
                ip=ip,
                timestamp=timestamp
            ), 403
