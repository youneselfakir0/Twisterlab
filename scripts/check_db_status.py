
import sqlite3
import os

db_path = os.path.join("src", "twisterlab_trader.db")

def check_db():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {', '.join([t[0] for t in tables])}")
        
        # Count rows in key tables
        for table in [t[0] for t in tables]:
            cursor.execute(f"SELECT count(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Table '{table}': {count} rows")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
