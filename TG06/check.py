import sqlite3

def view_users():
    conn = sqlite3.connect('user.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    conn.close()

    if rows:
        print("Пользователи в базе данных:")
        for row in rows:
            print(f"ID: {row[0]}, Telegram ID: {row[1]}, Имя: {row[2]}")
            if row[3]:  # category1
                print(f"  Категория 1: {row[3]} - {row[6]} руб.")
            if row[4]:  # category2
                print(f"  Категория 2: {row[4]} - {row[7]} руб.")
            if row[5]:  # category3
                print(f"  Категория 3: {row[5]} - {row[8]} руб.")
            print("-" * 40)
    else:
        print("База данных пуста.")

if __name__ == "__main__":
    view_users()
