import psycopg2
import pandas as pd
from datetime import datetime
import os

def collect():

    # ✅ 1. Define folder path for collected data
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    os.makedirs(data_dir, exist_ok=True)  # create if not exists


    conn = psycopg2.connect(dbname='demo', user='demo', password='demo', host='localhost')
    cur = conn.cursor()
    
    query = """
    SELECT query, calls, total_exec_time, mean_exec_time, rows
    FROM pg_stat_statements
    WHERE dbid = (SELECT oid FROM pg_database WHERE datname = 'demo')
    ORDER BY total_exec_time DESC
    LIMIT 100;
    """
    cur.execute(query)
    rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=['query','calls','total_time','mean_time','rows'])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(data_dir, f"pg_stats_{timestamp}.csv")

    df.to_csv(file_path, index=False)
    
    print(f"✅ Collected {len(df)} queries into {file_path}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    collect()
