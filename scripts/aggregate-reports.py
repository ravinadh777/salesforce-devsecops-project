# scripts/aggregate-reports.py
import json, os, glob, argparse, datetime

parser = argparse.ArgumentParser()
parser.add_argument('--reports-dir', default='dashboard/reports')
parser.add_argument('--output',      default='dashboard/dashboard-data.json')
parser.add_argument('--run-id',      default='')
parser.add_argument('--commit',      default='')
parser.add_argument('--branch',      default='')
parser.add_argument('--actor',       default='')
args = parser.parse_args()

findings = []

# Pull from PMD
try:
    with open(f'{args.reports_dir}/pmd.json') as f:
        pmd = json.load(f)
    sev_map = {1:'CRITICAL', 2:'HIGH', 3:'MEDIUM', 4:'LOW', 5:'INFO'}
    for file in pmd.get('files', []):
        for v in file.get('violations', []):
            findings.append({
                'id':          f"PMD-{len(findings)+1}",
                'tool':        'PMD',
                'severity':    sev_map.get(v.get('priority', 3), 'MEDIUM'),
                'rule':        v.get('rule', ''),
                'file':        file.get('filename', ''),
                'line':        v.get('beginline', 0),
                'description': v.get('description', '')
            })
except Exception as e:
    print(f'PMD parse skipped: {e}')

# Pull from npm audit
try:
    with open(f'{args.reports_dir}/npm-audit.json') as f:
        audit = json.load(f)
    for pkg, vuln in audit.get('vulnerabilities', {}).items():
        sev = vuln.get('severity', 'low').upper()
        findings.append({
            'id':          f"NPM-{len(findings)+1}",
            'tool':        'npm-audit',
            'severity':    sev if sev in ('CRITICAL','HIGH','MEDIUM','LOW') else 'LOW',
            'rule':        ', '.join(vuln.get('via', [pkg]) if isinstance(vuln.get('via',[]), list) else [pkg]),
            'file':        'package.json',
            'line':        0,
            'description': f"{pkg}@{vuln.get('range','')} — {vuln.get('fixAvailable','')}"
        })
except Exception as e:
    print(f'npm-audit parse skipped: {e}')

# Pull from Gitleaks
try:
    with open(f'{args.reports_dir}/gitleaks.json') as f:
        leaks = json.load(f)
    if isinstance(leaks, list):
        for leak in leaks:
            findings.append({
                'id':          f"GL-{len(findings)+1}",
                'tool':        'Gitleaks',
                'severity':    'CRITICAL',
                'rule':        leak.get('RuleID', 'secret'),
                'file':        leak.get('File', ''),
                'line':        leak.get('StartLine', 0),
                'description': leak.get('Description', 'Potential secret detected')
            })
except Exception as e:
    print(f'Gitleaks parse skipped: {e}')

counts = {'CRITICAL':0,'HIGH':0,'MEDIUM':0,'LOW':0,'INFO':0}
for f in findings:
    counts[f['severity']] = counts.get(f['severity'], 0) + 1

output = {
    'run_id':    args.run_id,
    'commit':    args.commit,
    'branch':    args.branch,
    'actor':     args.actor,
    'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
    'summary':   counts,
    'findings':  findings,
    'pipeline_stages': [],
    'compliance': []
}

os.makedirs(os.path.dirname(args.output), exist_ok=True)
with open(args.output, 'w') as f:
    json.dump(output, f, indent=2)

print(f'Aggregated {len(findings)} findings → {args.output}')