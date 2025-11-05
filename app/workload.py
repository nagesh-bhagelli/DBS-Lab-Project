import psycopg2
import random
import time
import csv

# Connect to PostgreSQL
conn = psycopg2.connect(dbname='demo', user='demo', password='demo', host='localhost')
cur = conn.cursor()

cities = ["Delhi", "Mumbai", "Pune", "Chennai", "Kolkata"]
statuses = ["pending", "delivered", "cancelled"]

# Open CSV file to log queries
csv_file = open("../data/query_log.csv", "a", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "query", "params", "execution_time_ms", "rows_returned"])

print("🏃 Running workload... Press Ctrl+C to stop.")
try:
    while True:
        q_type = random.choice(["users", "orders"])
        if q_type == "users":
            query = "SELECT COUNT(*) FROM users WHERE city = %s;"
            param = (random.choice(cities),)
        else:
            query = "SELECT COUNT(*) FROM orders WHERE status = %s;"
            param = (random.choice(statuses),)

        # Measure execution time
        start_time = time.time()
        cur.execute(query, param)
        rows = cur.fetchone()
        conn.commit()
        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000  # convert to milliseconds

        # Log to CSV
        csv_writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            cur.mogrify(query, param).decode(),  # full query with parameters
            param,
            round(execution_time_ms, 3),
            rows[0] if rows else 0
        ])
        csv_file.flush()  # make sure data is written immediately

        time.sleep(0.1)

except KeyboardInterrupt:
    print("⏹ Workload stopped.")

finally:
    cur.close()
    conn.close()
    csv_file.close()
