#!/usr/bin/env python3
"""
.github/scripts/update-dashboard.py

Called at the end of every pipeline job.
Reads env vars set by the workflow, merges the job result
into dashboard-data.json, and ingests any available reports.
"""
import json, os, glob, datetime, sys

REPORTS_DIR   = os.environ.get("REPORTS_DIR",   "dashboard/reports")
DASHBOARD_DIR = os.environ.get("DASHBOARD_DIR", "dashboard")
STATE_PATH    = os.path.join(DASHBOARD_DIR, "dashboard-data.json")

STAGE_NAME    = os.environ.get("STAGE_NAME",  "unknown")
STAGE_LABEL   = os.environ.get("STAGE_LABEL", STAGE_NAME)
STAGE_ICON    = os.environ.get("STAGE_ICON",  "⚙️")
JOB_STATUS    = os.environ.get("JOB_STATUS",  "unknown")
RUN_ID        = os.environ.get("RUN_ID",       os.environ.get("GITHUB_RUN_ID", ""))
COMMIT        = os.environ.get("COMMIT",       os.environ.get("GITHUB_SHA", ""))
BRANCH        = os.environ.get("BRANCH",       os.environ.get("GITHUB_REF_NAME", ""))
ACTOR         = os.environ.get("ACTOR",        os.environ.get("GITHUB_ACTOR", ""))
PIPELINE_COMPLETE = os.environ.get("PIPELINE_COMPLETE", "false").lower() == "true"

os.makedirs(DASHBOARD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR,   exist_ok=True)

# ── Load existing state ──────────────────────────────────
try:
    with open(STATE_PATH) as f:
        state = json.load(f)
except Exception:
    state = {
        "run_id":   RUN_ID,
        "commit":   COMMIT,
        "branch":   BRANCH,
        "actor":    ACTOR,
        "pipeline_complete": False,
        "pipeline_stages": [],
        "findings":   [],
        "compliance": [],
        "summary":    {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
    }

# ── Refresh metadata ─────────────────────────────────────
state.update({
    "run_id":    RUN_ID,
    "commit":    COMMIT,
    "branch":    BRANCH,
    "actor":     ACTOR,
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "last_updated_by": STAGE_NAME,
    "pipeline_complete": PIPELINE_COMPLETE,
})

# ── Map job result to dashboard status ───────────────────
STATUS_MAP = {
    "success":   {"status": "pass",    "pct": 100},
    "failure":   {"status": "fail",    "pct": 20},
    "cancelled": {"status": "skip",    "pct": 0},
    "skipped":   {"status": "skip",    "pct": 0},
}
mapped = STATUS_MAP.get(JOB_STATUS, {"status": "skip", "pct": 0})

# ── Upsert this stage in pipeline_stages ─────────────────
stages = state.get("pipeline_stages", [])
existing = next((s for s in stages if s.get("name") == STAGE_LABEL), None)
detail_map = {
    "pass": f"Completed successfully",
    "fail": f"Failed — check run logs",
    "skip": f"Skipped",
}
if existing:
    existing.update({
        "status":     mapped["status"],
        "raw_status": JOB_STATUS,
        "pct":        mapped["pct"],
        "detail":     detail_map[mapped["status"]],
        "updated_at": state["timestamp"],
    })
else:
    stages.append({
        "name":       STAGE_LABEL,
        "icon":       STAGE_ICON,
        "status":     mapped["status"],
        "raw_status": JOB_STATUS,
        "pct":        mapped["pct"],
        "detail":     detail_map[mapped["status"]],
        "updated_at": state["timestamp"],
    })
state["pipeline_stages"] = stages

# ── Ingest findings from available reports ───────────────
findings    = state.get("findings", [])
existing_ids = {f["id"] for f in findings}

def safe_open(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception as e:
        print(f"  skip {path}: {e}")
        return None

# PMD
for path in glob.glob(f"{REPORTS_DIR}/**/pmd.json", recursive=True):
    data = safe_open(path)
    if not data:
        continue
    SEV = {1:"CRITICAL",2:"HIGH",3:"MEDIUM",4:"LOW",5:"INFO"}
    for fi in data.get("files", []):
        for v in fi.get("violations", []):
            fid = f"PMD-{fi.get('filename','')}-{v.get('beginline',0)}-{v.get('rule','')}"
            if fid not in existing_ids:
                existing_ids.add(fid)
                findings.append({
                    "id": fid, "tool": "PMD",
                    "severity": SEV.get(v.get("priority", 3), "MEDIUM"),
                    "rule": v.get("rule", ""), "file": fi.get("filename", ""),
                    "line": v.get("beginline", 0), "description": v.get("description", ""),
                })

# npm audit
for path in glob.glob(f"{REPORTS_DIR}/**/npm-audit.json", recursive=True):
    data = safe_open(path)
    if not data:
        continue
    for pkg, vuln in data.get("vulnerabilities", {}).items():
        sev = vuln.get("severity", "low").upper()
        fid = f"NPM-{pkg}"
        if fid not in existing_ids:
            existing_ids.add(fid)
            findings.append({
                "id": fid, "tool": "npm-audit",
                "severity": sev if sev in ("CRITICAL","HIGH","MEDIUM","LOW") else "LOW",
                "rule": pkg, "file": "package.json", "line": 0,
                "description": f"{pkg} — {vuln.get('severity','')} severity, fix: {vuln.get('fixAvailable', 'unknown')}",
            })

# Gitleaks JSON
for path in glob.glob(f"{REPORTS_DIR}/**/gitleaks.json", recursive=True):
    data = safe_open(path)
    if not data or not isinstance(data, list):
        continue
    for leak in data:
        fid = f"GL-{leak.get('RuleID','')}-{leak.get('File','')}-{leak.get('StartLine',0)}"
        if fid not in existing_ids:
            existing_ids.add(fid)
            findings.append({
                "id": fid, "tool": "Gitleaks", "severity": "CRITICAL",
                "rule": leak.get("RuleID", "secret"), "file": leak.get("File", ""),
                "line": leak.get("StartLine", 0),
                "description": leak.get("Description", "Potential secret detected"),
            })

# Trivy
for path in glob.glob(f"{REPORTS_DIR}/**/trivy.json", recursive=True):
    data = safe_open(path)
    if not data:
        continue
    for result in data.get("Results", []):
        for v in result.get("Vulnerabilities", []) or []:
            fid = f"TRIVY-{v.get('VulnerabilityID','')}-{result.get('Target','')}"
            if fid not in existing_ids:
                existing_ids.add(fid)
                findings.append({
                    "id": fid, "tool": "Trivy",
                    "severity": v.get("Severity", "LOW"),
                    "rule": v.get("VulnerabilityID", ""), "file": result.get("Target", ""),
                    "line": 0, "description": v.get("Title", v.get("Description", "")),
                })

# SF Scanner
for path in glob.glob(f"{REPORTS_DIR}/**/sf-scanner*.json", recursive=True):
    data = safe_open(path)
    if not data or not isinstance(data, list):
        continue
    for item in data:
        for v in item.get("violations", []) or []:
            fid = f"SF-{item.get('fileName','')}-{v.get('line',0)}-{v.get('ruleName','')}"
            if fid not in existing_ids:
                existing_ids.add(fid)
                sev_raw = str(v.get("severity","3"))
                sev_map = {"1":"CRITICAL","2":"HIGH","3":"MEDIUM","4":"LOW","5":"INFO"}
                findings.append({
                    "id": fid, "tool": "SFScanner",
                    "severity": sev_map.get(sev_raw, "MEDIUM"),
                    "rule": v.get("ruleName",""), "file": item.get("fileName",""),
                    "line": v.get("line",0), "description": v.get("message",""),
                })

# OWASP DC
for path in glob.glob(f"{REPORTS_DIR}/**/dependency-check-report.json", recursive=True):
    data = safe_open(path)
    if not data:
        continue
    for dep in data.get("dependencies", []):
        for vuln in dep.get("vulnerabilities", []):
            fid = f"OWASP-{vuln.get('name','')}-{dep.get('fileName','')}"
            if fid not in existing_ids:
                existing_ids.add(fid)
                sev_raw = vuln.get("severity","MEDIUM").upper()
                findings.append({
                    "id": fid, "tool": "OWASP-DC",
                    "severity": sev_raw if sev_raw in ("CRITICAL","HIGH","MEDIUM","LOW") else "MEDIUM",
                    "rule": vuln.get("name",""), "file": dep.get("fileName",""),
                    "line": 0, "description": vuln.get("description","")[:200],
                })

# Compliance
compliance = []
for path in glob.glob(f"{REPORTS_DIR}/**/compliance-*.json", recursive=True):
    data = safe_open(path)
    if data and "framework" in data:
        passed = data.get("controls_passed", data.get("passed", 0))
        total  = passed + data.get("controls_failed", data.get("failed", 0))
        if total == 0:
            total = data.get("total", 10)
        compliance.append({
            "framework": data["framework"],
            "passed":    passed,
            "total":     total,
            "status":    data.get("status","unknown"),
        })
if compliance:
    state["compliance"] = compliance

state["findings"] = findings

# Recount summary
counts = {"critical":0,"high":0,"medium":0,"low":0,"info":0}
for f in findings:
    k = f.get("severity","LOW").lower()
    counts[k] = counts.get(k, 0) + 1
state["summary"] = counts

# ── If final run, stamp overall pipeline results ──────────
if PIPELINE_COMPLETE:
    result_map = {
        "secret-detection":           os.environ.get("R_SECRET",      "skipped"),
        "sast-pmd-apex":              os.environ.get("R_PMD",         "skipped"),
        "sast-codeql":                os.environ.get("R_CODEQL",      "skipped"),
        "sast-salesforce-scanner":    os.environ.get("R_SF_SCANNER",  "skipped"),
        "sca-npm-audit":              os.environ.get("R_NPM",         "skipped"),
        "sca-owasp-dependency-check": os.environ.get("R_OWASP",       "skipped"),
        "sca-trivy":                  os.environ.get("R_TRIVY",       "skipped"),
        "ai-vulnerability-intelligence": os.environ.get("R_AI_INTEL", "skipped"),
        "sonarqube-governance":       os.environ.get("R_SONAR",       "skipped"),
        "salesforce-org-security":    os.environ.get("R_ORG_SEC",     "skipped"),
        "compliance-checkov":         os.environ.get("R_CHECKOV",     "skipped"),
        "compliance-validation":      os.environ.get("R_COMPLIANCE",  "skipped"),
        "ai-remediation-engine":      os.environ.get("R_REMEDIATION", "skipped"),
    }
    state["job_results"] = result_map
    any_failed = any(v == "failure" for v in result_map.values())
    state["overall_status"] = "fail" if any_failed else "pass"

# ── Persist ───────────────────────────────────────────────
with open(STATE_PATH, "w") as fh:
    json.dump(state, fh, indent=2)

print(f"[update-dashboard] stage={STAGE_NAME} status={JOB_STATUS}")
print(f"[update-dashboard] findings={len(findings)} stages={len(stages)}")
print(f"[update-dashboard] summary={state['summary']}")
