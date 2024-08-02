import sqlite3
import logging, datetime, os

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            reward INTEGER NOT NULL,
            link TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            link TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_check (
            tg_id TEXT NOT NULL,
            task_id INTEGER NOT NULL,
            reward INTEGER NOT NULL,
            screen TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()



def get_user_by_tg_id(tg_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE tg_id = ?', (tg_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(tg_id, username, coins):
    logging.debug(f"Adding user to database: tg_id={tg_id}, username={username}, coins={coins}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (tg_id, username, coins, available_tasks, completed_tasks)
        VALUES (?, ?, ?, '', '')
    ''', (tg_id, username, coins))
    conn.commit()
    conn.close()

def update_wallet(tg_id, wallet_address):
    logging.debug(f"Updating wallet for user: tg_id={tg_id}, wallet_address={wallet_address}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET wallet = ? WHERE tg_id = ?', (wallet_address, tg_id))
    conn.commit()
    conn.close()

def get_top_users(limit=500):
    logging.debug(f"Getting top {limit} users by coins")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tg_id, username, coins
        FROM users
        ORDER BY coins DESC
        LIMIT ?
    ''', (limit,))
    top_users = cursor.fetchall()
    conn.close()
    return top_users

def get_user_rank(tg_id):
    logging.debug(f"Getting rank for user: tg_id={tg_id}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*)
        FROM users
        WHERE coins > (SELECT coins FROM users WHERE tg_id = ?)
    ''', (tg_id,))
    rank = cursor.fetchone()[0] + 1
    conn.close()
    return rank

def get_total_users():
    logging.debug("Getting total number of users")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    conn.close()
    return total_users

def increment_ref_count(tg_id):
    logging.debug(f"Incrementing ref count for user: tg_id={tg_id}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET ref = ref + 1 WHERE tg_id = ?', (tg_id,))
    conn.commit()
    conn.close()

def add_referral_bonus(tg_id, bonus_coins):
    logging.debug(f"Adding referral bonus: tg_id={tg_id}, bonus_coins={bonus_coins}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET coins = coins + ? WHERE tg_id = ?', (bonus_coins, tg_id))
    conn.commit()
    conn.close()

def update_ref_names(tg_id, username):
    logging.debug(f"Updating ref names for user: tg_id={tg_id}, new_ref_name={username}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ref_names FROM users WHERE tg_id = ?', (tg_id,))
    ref_names = cursor.fetchone()[0]
    if ref_names:
        new_ref_names = ref_names + ',' + username
    else:
        new_ref_names = username
    cursor.execute('UPDATE users SET ref_names = ? WHERE tg_id = ?', (new_ref_names, tg_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def add_news(text, link=None):
    logging.debug(f"Adding news to database: text={text}, link={link}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO news (text, link)
        VALUES (?, ?)
    ''', (text, link))
    conn.commit()
    conn.close()

def create_task(text, reward, link):
    logging.debug(f"Creating task: text={text}, reward={reward}, link={link}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (text, reward, link)
        VALUES (?, ?, ?)
    ''', (text, reward, link))
    conn.commit()
    conn.close()

def get_active_tasks():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE status = "active"')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_inactive_tasks():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE status = "inactive"')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def change_task_status(task_id, status):
    logging.debug(f"Changing status of task {task_id} to {status}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
    conn.commit()
    conn.close()

def get_active_news():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM news')
    active_news = cursor.fetchall()
    conn.close()
    return active_news

def delete_news(news_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()

def update_available_tasks(tg_id, available_tasks):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET available_tasks = ? WHERE tg_id = ?', (available_tasks, tg_id))
    conn.commit()
    conn.close()


def update_user_coins_and_tasks(tg_id, coins, completed_tasks):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET coins = ?, completed_tasks = ? WHERE tg_id = ?', (coins, completed_tasks, tg_id))
    conn.commit()
    conn.close()

def auto_accept_tasks():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM task_check WHERE screen IS NOT NULL')
    task_checks = cursor.fetchall()
    
    now = datetime.datetime.now()
    for task_check in task_checks:
        tg_id, task_id, reward, screen, date = task_check
        date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        if (now - date).total_seconds() > 48 * 3600:
            if screen:
                user = get_user_by_tg_id(tg_id)
                if user:
                    coins = user[3] + reward
                    completed_tasks = user[6] + f",{task_id}" if user[6] else str(task_id)
                    update_user_coins_and_tasks(tg_id, coins, completed_tasks)
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM task_check WHERE tg_id = ? AND task_id = ?', (tg_id, task_id))
            conn.commit()
            if os.path.exists(screen):
                os.remove(screen)
    conn.close()