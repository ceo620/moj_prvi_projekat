# Live Central Brain v2.3 Web

Features:
- User login with role permissions (admin, reviewer, viewer)
- Upload CSV/XLSX input files
- Run pipeline into SQLite-backed master tables
- Full conflict lineage view
- Side-by-side diff for formula and metadata review
- One-click promote from review queue into master
- Bulk approve / reject preserved from v2.2

## Quick start

```bash
python -m pip install -r requirements.txt
streamlit run webapp.py
```

Default demo users:
- admin / admin123
- reviewer / review123
- viewer / view123

## Files
- `webapp.py` - main Streamlit app
- `src/live_central_brain/core.py` - storage, ingestion, conflict detection, lineage, promotion
- `data/central_brain.sqlite` - SQLite database created at first run

## Notes
This is a lightweight enterprise-style review layer for Central Brain workflows. It is intended as a strong operational prototype.
