import sqlite3

def check_students():
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()

    if rows:
        print("Список учеников:")
        for row in rows:
            print(f"ID: {row[0]}, Имя: {row[1]}, Возраст: {row[2]}, Класс: {row[3]}")
    else:
        print("База данных пуста.")

    conn.close()

if __name__ == "__main__":
    check_students()
