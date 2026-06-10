import sqlite3

def migrate():
    conn = sqlite3.connect('twisterlab_trader.db')
    cursor = conn.cursor()
    
    columns = [
        ("exit_price", "FLOAT"),
        ("exit_reason", "VARCHAR(50)"),
        ("realized_pnl", "FLOAT"),
        ("realized_pnl_pct", "FLOAT"),
        ("trailing_sl_trigger", "FLOAT"),
        ("highest_price_observed", "FLOAT"),
        ("trailing_sl_distance", "FLOAT")
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE live_orders ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists or error.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
