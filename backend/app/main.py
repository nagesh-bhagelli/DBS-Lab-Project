# app/main.py
import os
import json
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
from database import get_db,init_db
from models import User, Item, Order
from sqlalchemy import func
from sqlalchemy.orm import Session


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://demo:demo@localhost:5432/demo")
RECS_FILE = os.path.join(os.path.dirname(__file__), "../../data/recommendations.json")
AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS index_audit (
  id serial PRIMARY KEY,
  action text,
  index_name text,
  table_name text,
  column_name text,
  user_name text,
  ts timestamptz default now(),
  details jsonb
);
"""

app = FastAPI()

def get_conn():
    return psycopg2.connect(DATABASE_URL)

@app.on_event("startup")
async def startup():
    init_db()
    # ensure audit table exists
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(AUDIT_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()

@app.get("/recommendations")
def get_recommendations():
    if not os.path.exists(RECS_FILE):
        return []
    with open(RECS_FILE, 'r') as f:
        recs = json.load(f)
    return recs

@app.get("/indexes")
def get_indexes():
    """Get current list of indexes created by the system"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Get indexes from audit table that still exist in the database
        # Get the most recent create action for each index that still exists
        cur.execute("""
            SELECT 
                a.index_name,
                a.table_name,
                a.column_name,
                a.ts as created_at,
                a.user_name,
                COALESCE(pg_size_pretty(pg_relation_size(i.indexname::regclass)), 'N/A') as size
            FROM (
                SELECT DISTINCT ON (index_name)
                    index_name, table_name, column_name, ts, user_name
                FROM index_audit
                WHERE action = 'create'
                ORDER BY index_name, ts DESC
            ) a
            JOIN pg_indexes i ON i.indexname = a.index_name
            WHERE i.schemaname = 'public'
            ORDER BY a.ts DESC
        """)
        indexes = []
        for row in cur.fetchall():
            indexes.append({
                "index_name": row[0],
                "table_name": row[1],
                "column_name": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "user_name": row[4],
                "size": row[5] if row[5] else "N/A"
            })
        return indexes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

class ApplyRequest(BaseModel):
    table: str
    column: str
    force: bool = False
    user: str = "api"

@app.get("/ping")
def ping():
    return {"status":"ok"}

@app.post("/apply")
def apply_index(req: ApplyRequest):
    # must set force true to actually create index
    # build index name
    idx_name = f"idx_{req.table}_{req.column}"
    create_sql = f'CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx_name} ON {req.table}({req.column});'
    conn = get_conn()
    conn.autocommit = True
    cur = conn.cursor()
    # simple dry-run: check if index exists
    cur.execute("SELECT indexname FROM pg_indexes WHERE tablename=%s;", (req.table,))
    existing = [r[0] for r in cur.fetchall()]
    if req.force:
        try:
            # Check current indexes count from audit table (only successful creates)
            cur.execute("""
                SELECT index_name, table_name, column_name, ts 
                FROM index_audit 
                WHERE action = 'create' 
                AND index_name IN (
                    SELECT indexname FROM pg_indexes 
                    WHERE schemaname = 'public'
                )
                ORDER BY ts ASC
            """)
            current_indexes = cur.fetchall()
            
            # If we have 3 or more indexes, delete the oldest one
            deleted_index = None
            if len(current_indexes) >= 3:
                oldest = current_indexes[0]  # oldest is first due to ORDER BY ts ASC
                oldest_idx_name = oldest[0]
                oldest_table = oldest[1]
                
                # Delete the oldest index
                drop_sql = f'DROP INDEX CONCURRENTLY IF EXISTS {oldest_idx_name};'
                try:
                    cur.execute(drop_sql)
                    # Audit the deletion
                    cur.execute("INSERT INTO index_audit (action,index_name,table_name,column_name,user_name,details) VALUES (%s,%s,%s,%s,%s,%s);",
                                ("delete", oldest_idx_name, oldest_table, oldest[2] if len(oldest) > 2 else None, req.user, json.dumps({"reason":"rotation_limit", "replaced_by": idx_name})))
                    deleted_index = oldest_idx_name
                except Exception as drop_err:
                    # Log drop failure but continue with creation
                    cur.execute("INSERT INTO index_audit (action,index_name,table_name,column_name,user_name,details) VALUES (%s,%s,%s,%s,%s,%s);",
                                ("delete_failed", oldest_idx_name, oldest_table, oldest[2] if len(oldest) > 2 else None, req.user, json.dumps({"error": str(drop_err)})))
            
            # Create the new index
            cur.execute(create_sql)
            # audit entry
            cur.execute("INSERT INTO index_audit (action,index_name,table_name,column_name,user_name,details) VALUES (%s,%s,%s,%s,%s,%s);",
                        ("create", idx_name, req.table, req.column, req.user, json.dumps({"note":"applied via API"})))
            conn.commit()
            
            result = {"status":"applied", "index": idx_name}
            if deleted_index:
                result["deleted_index"] = deleted_index
            return result
        except Exception as e:
            # try to record failure
            try:
                cur.execute("INSERT INTO index_audit (action,index_name,table_name,column_name,user_name,details) VALUES (%s,%s,%s,%s,%s,%s);",
                            ("create_failed", idx_name, req.table, req.column, req.user, json.dumps({"error": str(e)})))
                conn.commit()
            except:
                pass
            raise HTTPException(status_code=500, detail=str(e))
    else:
        return {"status":"dry-run", "index": idx_name, "exists": existing}



@app.get("/byCity")
def by_city(db: Session = Depends(get_db)):
    results = (
        db.query(User.city, func.count(User.id).label("user_count"))
        .group_by(User.city)
        .all()
    )
    return results

@app.get("/status")
def status(db: Session = Depends(get_db)):
    results = (
        db.query(Order.status, func.count(Order.id).label("order_count"))
        .group_by(Order.status)
        .all()
    )
    return results

@app.get("/byAge")
def by_age(db: Session = Depends(get_db)):
    results = (
        db.query(User.age, func.count(User.id).label("user_count"))
        .group_by(User.age)
        .all()
    )
    return results

@app.get("/mostOrderedItem")
def most_ordered_item(db: Session = Depends(get_db)):
    results = (
        db.query(Item.name, func.count(Order.id).label("order_count"))
        .join(Order)
        .group_by(Item.name)
        .order_by(func.count(Order.id).desc())
        .limit(10)
        .all()
    )
    return results