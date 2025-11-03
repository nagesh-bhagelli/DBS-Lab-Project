import psycopg2
from random import choice, randint

conn = psycopg2.connect(dbname='demo', user='demo', password='demo', host='localhost')
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id serial PRIMARY KEY,
    name text,
    city text,
    age int
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id serial PRIMARY KEY,
    user_id int REFERENCES users(id),
    amount numeric,
    status text
);
""")

# Insert synthetic data
cities = ["Delhi", "Mumbai", "Pune", "Bangalore", "Hyderabad"]
statuses = ["pending", "shipped", "delivered", "cancelled"]

for i in range(1, 10001):
    cur.execute("INSERT INTO users (name, city, age) VALUES (%s, %s, %s)",
                (f"name{i}", choice(cities), randint(18, 60)))

for i in range(1, 20001):
    cur.execute("INSERT INTO orders (user_id, amount, status) VALUES (%s, %s, %s)",
                (randint(1, 10000), randint(100, 10000), choice(statuses)))

conn.commit()
cur.close()
conn.close()
print("Database seeded ✅")
