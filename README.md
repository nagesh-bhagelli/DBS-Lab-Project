# DBS-Lab-Project

Small demo/lab project for running a local PostgreSQL instance, seeding it with synthetic data, generating a lightweight workload, and collecting query statistics using pg_stat_statements.

Overview
- `app/data/infra/docker-compose.yml` — Postgres service (postgres:15) configured to load `pg_stat_statements`.
- `app/data/infra/seed_db.py` — creates `users` and `orders` tables and inserts synthetic data (10k users, 20k orders).
- `app/workload.py` — continuous workload generator that issues simple `SELECT COUNT(*)` queries to produce activity.
- `app/collector.py` — snapshots top queries from `pg_stat_statements` and writes a timestamped CSV into `app/data/`.

Quick start (Windows cmd.exe)

1) Start Postgres (from the infra folder):

```cmd
cd "c:\Users\nageshbhagelli\OneDrive\Desktop\DBS Project\DBS-Lab-Project\app\data\infra"
docker compose up -d
```

2) Create a Python venv and install dependencies (from repo root):

```cmd
cd "c:\Users\nageshbhagelli\OneDrive\Desktop\DBS Project\DBS-Lab-Project"
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

3) Seed the database (runs on host Python and connects to `localhost:5432`):

```cmd
cd app\data\infra
python seed_db.py
```

4) Run the workload generator (open another terminal):

```cmd
cd "c:\Users\nageshbhagelli\OneDrive\Desktop\DBS Project\DBS-Lab-Project\app"
.venv\Scripts\activate
python workload.py
```

5) Collect query stats while the workload runs (writes CSV to `app/data/`):

```cmd
cd "c:\Users\nageshbhagelli\OneDrive\Desktop\DBS Project\DBS-Lab-Project\app"
.venv\Scripts\activate
python collector.py
```

Notes
- The Docker Compose file maps Postgres to host port 5432 and creates a database/user/password all set to `demo`.
- `pg_stat_statements` is enabled in the compose service via `shared_preload_libraries` so `collector.py` can query it.
- `requirements.txt` (repo root) currently lists `psycopg2-binary` and `pandas`.
- For automation, consider adding a small wait-for-postgres helper before running the seeder, parameterizing DB connection settings via environment variables, and adding a README section describing optional configuration.

If you want, I can also add a `wait-for-postgres` helper script, parameterize connection strings with environment variables, or create a Docker service to run the seeder inside a Python container.
