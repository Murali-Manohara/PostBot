"""
auth.py — India Post Officer Login System
Stores officer credentials and handles authentication.
"""

import hashlib

# ── Officer Database ──────────────────────────────────────────────────────────
# Format: { "OFFICER_ID": { "password_hash": ..., "name": ..., "circle": ..., "role": ... } }

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


OFFICERS = {
    "IP2024KA001": {
        "password_hash": _hash("post@Karnataka"),
        "name":   "Ravi Kumar",
        "circle": "Karnataka",
        "role":   "Divisional Manager",
        "email":  "ravi.kumar@indiapost.gov.in",
    },
    "IP2024MH001": {
        "password_hash": _hash("post@Maharashtra"),
        "name":   "Priya Desai",
        "circle": "Maharashtra",
        "role":   "Postmaster General",
        "email":  "priya.desai@indiapost.gov.in",
    },
    "IP2024TN001": {
        "password_hash": _hash("post@TamilNadu"),
        "name":   "Arjun Raj",
        "circle": "Tamil Nadu",
        "role":   "Assistant Superintendent",
        "email":  "arjun.raj@indiapost.gov.in",
    },
    "IP2024UP001": {
        "password_hash": _hash("post@UttarPradesh"),
        "name":   "Amit Singh",
        "circle": "Uttar Pradesh",
        "role":   "Inspector of Posts",
        "email":  "amit.singh@indiapost.gov.in",
    },
    "IP2024GJ001": {
        "password_hash": _hash("post@Gujarat"),
        "name":   "Neha Shah",
        "circle": "Gujarat",
        "role":   "Senior Postmaster",
        "email":  "neha.shah@indiapost.gov.in",
    },
    "IP2024RJ001": {
        "password_hash": _hash("post@Rajasthan"),
        "name":   "Suresh Meena",
        "circle": "Rajasthan",
        "role":   "Divisional Manager",
        "email":  "suresh.meena@indiapost.gov.in",
    },
    "DEMO": {
        "password_hash": _hash("demo123"),
        "name":   "Demo Officer",
        "circle": "All India",
        "role":   "Analyst",
        "email":  "demo@indiapost.gov.in",
    },
}


def authenticate(officer_id: str, password: str):
    """
    Returns officer dict if credentials are valid, else None.
    """
    officer_id = officer_id.strip().upper()
    officer = OFFICERS.get(officer_id)
    if officer and officer["password_hash"] == _hash(password):
        return {
            "id":     officer_id,
            "name":   officer["name"],
            "circle": officer["circle"],
            "role":   officer["role"],
            "email":  officer["email"],
        }
    return None


def get_demo_credentials():
    """Return list of demo credentials for display on login page."""
    return [
        {"id": "IP2024KA001", "pw": "post@Karnataka",    "name": "Ravi Kumar",   "circle": "Karnataka"},
        {"id": "IP2024MH001", "pw": "post@Maharashtra",  "name": "Priya Desai",  "circle": "Maharashtra"},
        {"id": "IP2024TN001", "pw": "post@TamilNadu",    "name": "Arjun Raj",    "circle": "Tamil Nadu"},
        {"id": "IP2024GJ001", "pw": "post@Gujarat",      "name": "Neha Shah",    "circle": "Gujarat"},
        {"id": "DEMO",        "pw": "demo123",            "name": "Demo Officer", "circle": "All India"},
    ]
