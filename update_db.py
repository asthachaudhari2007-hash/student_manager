import sqlite3

db_path = "instance/campusflow.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Connected to:", db_path)

# Show current columns
cursor.execute("PRAGMA table_info(attendance)")
print("Current columns:")
for col in cursor.fetchall():
    print(col)

try:
    cursor.execute("""
        ALTER TABLE attendance
        ADD COLUMN remarks TEXT
    """)
    conn.commit()
    print("\n✓ 'remarks' column added successfully.")
except sqlite3.OperationalError as e:
    print("\nSQLite Error:", e)

conn.close()
print("Done.")