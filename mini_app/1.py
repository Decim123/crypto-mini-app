import sqlite3

def migrate_db():
    # Подключение к базе данных
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Переименование старой таблицы
    cursor.execute('ALTER TABLE users RENAME TO users_old')

    # Создание новой таблицы с дополнительным полем 'ref'
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            coins INTEGER DEFAULT 0,
            leaderboard_place INTEGER DEFAULT 0,
            available_tasks TEXT,
            completed_tasks TEXT,
            lang TEXT DEFAULT 'en',
            wallet TEXT,
            ref INTEGER DEFAULT 0,
            ref_names TEXT
        )
    ''')

    # Копирование данных из старой таблицы в новую
    cursor.execute('''
        INSERT INTO users (id, tg_id, username, coins, leaderboard_place, available_tasks, completed_tasks, lang, wallet)
        SELECT id, tg_id, username, coins, leaderboard_place, available_tasks, completed_tasks, lang, wallet
        FROM users_old
    ''')

    # Удаление старой таблицы
    cursor.execute('DROP TABLE users_old')

    # Сохранение изменений
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate_db()
