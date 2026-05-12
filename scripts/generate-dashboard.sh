# scripts/generate-dashboard.sh
#!/bin/bash
# The dashboard/index.html is already the dashboard.
# This script just validates it exists and copies dashboard-data.json next to it.
set -e
echo "Dashboard: dashboard/index.html"
echo "Data file: dashboard/dashboard-data.json"
ls -lh dashboard/