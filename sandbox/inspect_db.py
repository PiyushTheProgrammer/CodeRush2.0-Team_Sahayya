import sqlite3

def main():
    conn = sqlite3.connect('aura_app.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print("=== SQLite Database on SSD (d:\\CodeRush2.0-Team_Sahayya\\aura_app.db) ===")
    print("Database File Path: d:\\CodeRush2.0-Team_Sahayya\\aura_app.db\n")
    for t in tables:
        tname = t[0]
        c.execute(f"SELECT count(*) FROM {tname}")
        cnt = c.fetchone()[0]
        print(f"Table '{tname}': {cnt} stored records")

if __name__ == "__main__":
    main()
