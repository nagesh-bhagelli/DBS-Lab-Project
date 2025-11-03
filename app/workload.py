import psycopg2
import random
import time

conn = psycopg2.connect(dbname='demo', user='demo', password='demo', host='localhost')
cur = conn.cursor()

cities = ["Delhi", "Mumbai", "Pune", "Chennai", "Kolkata"]
statuses = ["pending", "delivered", "cancelled"]

print("🏃 Running workload... Press Ctrl+C to stop.")
try:
    while True:
        q_type = random.choice(["users", "orders"])
        if q_type == "users":
            city = random.choice(cities)
            cur.execute("SELECT COUNT(*) FROM users WHERE city = %s;", (city,))
        else:
            status = random.choice(statuses)
            cur.execute("SELECT COUNT(*) FROM orders WHERE status = %s;", (status,))
        _ = cur.fetchone()
        conn.commit()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("⏹ Workload stopped.")
finally:
    cur.close()
    conn.close()
