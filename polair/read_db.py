import sqlite3

# połączenie z bazą
conn = sqlite3.connect("polair.db")
cursor = conn.cursor()

# pobranie listy tabel
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if not tables:
    print("Brak tabel w bazie.")
else:
    for table_name_tuple in tables:
        table_name = table_name_tuple[0]
        print(f"\nTabela: {table_name}")
        print("-" * (7 + len(table_name)))

        # pobranie nazw kolumn
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        print(" | ".join(columns))

        # pobranie wszystkich wierszy
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        if not rows:
            print("Brak danych w tabeli.")
        else:
            for row in rows:
                print(" | ".join(str(r) for r in row))

conn.close()
