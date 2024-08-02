from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from database import *
import logging, os, datetime, sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
import importlib
import sqlite3

app = Flask(__name__)
init_db()
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'mini_app', 'screenshots')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Настройка логгирования
logging.basicConfig(level=logging.DEBUG)

def get_translation(lang):
    if lang not in ['en', 'ru', 'es']:
        lang = 'en'
    lexicon_module = importlib.import_module(f'translations.LEXICON_{lang.upper()}')
    return lexicon_module.LEXICON

def initials_color(initials):
    colors = {
        'A': '#FF5733', 'B': '#33FF57', 'C': '#3357FF', 'D': '#FF33A5', 'E': '#A533FF',
        'F': '#FF5733', 'G': '#33FF57', 'H': '#3357FF', 'I': '#FF33A5', 'J': '#A533FF',
        'K': '#FF5733', 'L': '#33FF57', 'M': '#3357FF', 'N': '#FF33A5', 'O': '#A533FF',
        'P': '#FF5733', 'Q': '#33FF57', 'R': '#3357FF', 'S': '#FF33A5', 'T': '#A533FF',
        'U': '#FF5733', 'V': '#33FF57', 'W': '#3357FF', 'X': '#FF33A5', 'Y': '#A533FF',
        'Z': '#FF5733'
    }
    return colors.get(initials[0].upper(), '#333333')

app.jinja_env.filters['initials_color'] = initials_color

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    logging.debug(f"Received registration data: {data}")
    tg_id = data['tg_id']
    username = data['username']
    coins = data['coins']
    referrer_id = data.get('referrer_id')
    is_premium = data.get('is_premium', False)

    logging.debug(f"Adding user: tg_id={tg_id}, username={username}, coins={coins}, referrer_id={referrer_id}")
    add_user(tg_id, username, coins)

    if referrer_id:
        logging.debug(f"Referrer ID provided: {referrer_id}")
        increment_ref_count(referrer_id)
        user_record = get_user_by_tg_id(referrer_id)
        ref_count = user_record[9] + 1  # Assuming ref_count is the 10th field in the user record
        logging.debug(f"New ref_count for referrer {referrer_id}: {ref_count}")

        if ref_count <= 10:
            bonus = 500 if is_premium else 250
            logging.debug(f"Adding referral bonus: {bonus} coins")
            add_referral_bonus(referrer_id, bonus)
        elif ref_count <= 50:
            bonus = 750 if is_premium else 500
            logging.debug(f"Adding referral bonus: {bonus} coins")
            add_referral_bonus(referrer_id, bonus)
        else:
            bonus = 1250 if is_premium else 1000
            logging.debug(f"Adding referral bonus: {bonus} coins")
            add_referral_bonus(referrer_id, bonus)

        # Обновление поля ref_names для пригласившего пользователя
        update_ref_names(referrer_id, username)

    return jsonify({'status': 'success'}), 200

@app.route('/log', methods=['POST'])
def log():
    message = request.json.get('message')
    logging.debug(f"Client log: {message}")
    return jsonify({'status': 'logged'}), 200

@app.route('/main')
def main():
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    
    if user is None:
        logging.debug(f"User with tg_id={tg_id} not found.")
        lang = 'en'
    else:
        logging.debug(f"User data: {user}")
        try:
            lang = user[7]
        except IndexError:
            logging.error(f"User data does not have expected fields: {user}")
            lang = 'en'
    
    translation = get_translation(lang)
    active_news = get_active_news()
    
    return render_template('main.html', tg_id=tg_id, active_news=active_news, translation=translation, lang=lang)

@app.route('/get_tasks')
def get_tasks():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    lang = user[7] if user else 'en'
    translation = get_translation(lang)
    active_tasks = get_active_tasks()
    completed_tasks = user[6].split(',') if user[6] else []
    available_tasks = [task for task in active_tasks if str(task[0]) not in completed_tasks]
    all_tasks = available_tasks + [task for task in active_tasks if str(task[0]) in completed_tasks]
    
    task_statuses = {}
    for task in all_tasks:
        if str(task[0]) in completed_tasks:
            task_statuses[task[0]] = 'completed'
        else:
            cursor.execute('SELECT screen FROM task_check WHERE tg_id = ? AND task_id = ?', (tg_id, task[0]))
            record = cursor.fetchone()
            if record:
                task_statuses[task[0]] = 'screenshot' if record[0] else 'upload'
            else:
                task_statuses[task[0]] = 'link'
    return jsonify({'tasks': all_tasks, 'statuses': task_statuses})

@app.route('/get_news')
def get_news():
    active_news = get_active_news()
    news_data = [{'text': news[1], 'link': news[2]} for news in active_news]
    return jsonify(news_data)

@app.route('/user_data')
def user_data():
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    if user:
        coins = user[3]
        wallet = user[8]  # Assuming wallet is the 9th field in the user record
        return jsonify({'coins': coins, 'wallet': wallet})
    return jsonify({'error': 'User not found'}), 404

@app.route('/check_user')
def check_user():
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    return {'exists': user is not None}

@app.route('/start')
def start():
    tg_id = request.args.get('tg_id')
    username = request.args.get('username')
    referrer_id = request.args.get('ref')
    return render_template('start.html', tg_id=tg_id, username=username, referrer_id=referrer_id)

@app.route('/wallet', methods=['POST'])
def wallet():
    data = request.json
    tg_id = data['tg_id']
    wallet_address = data['account']['address']
    logging.debug(f"Received wallet info: tg_id={tg_id}, wallet_address={wallet_address}")
    update_wallet(tg_id, wallet_address)
    return jsonify({'status': 'success'})

@app.route('/leaderboard')
def leaderboard():
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    lang = user[7] if user else 'en'
    translation = get_translation(lang)
    if not user:
        logging.debug(f"User with tg_id={tg_id} not found.")
    top_users = get_top_users()
    user_rank = get_user_rank(tg_id) if user else None
    total_users = get_total_users()
    logging.debug(f"User: {user}, Top Users: {top_users}, User Rank: {user_rank}, Total Users: {total_users}")
    return render_template('leaderboard.html', user=user, top_users=top_users, user_rank=user_rank, total_users=total_users, translation=translation)

@app.route('/friends')
def friends():
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    lang = user[7] if user else 'en'
    translation = get_translation(lang)
    if not user:
        return redirect(url_for('start', tg_id=tg_id))
    ref_count = user[9] if user[9] is not None else 0
    ref_names = user[9] if user[9] is not None else ''
    return render_template('friends.html', user=user, ref_count=ref_count, translation=translation)

@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != '123':
        return jsonify({'error': 'Access denied'}), 403
    
    users = get_all_users()
    active_tasks = get_active_tasks()
    inactive_tasks = get_inactive_tasks()
    active_news = get_active_news()
    return render_template('admin.html', users=users, active_tasks=active_tasks, inactive_tasks=inactive_tasks, active_news=active_news)

@app.route('/delete_news', methods=['POST'])
def delete_news_route():
    news_id = request.json['id']
    delete_news(news_id)
    return jsonify({'status': 'success'})

@app.route('/create_task', methods=['POST'])
def create_task_route():
    text = request.form['text']
    reward = request.form['reward']
    link = request.form['link']
    create_task(text, reward, link)
    return redirect(url_for('admin', password='123'))

@app.route('/create_news', methods=['POST'])
def create_news():
    text = request.form['text']
    link = request.form.get('link')
    add_news(text, link)
    return redirect(url_for('admin', password='123'))

@app.route('/change_task_status', methods=['POST'])
def change_task_status_route():
    data = request.json
    task_id = data['id']
    status = data['status']
    change_task_status(task_id, status)
    return jsonify({'status': 'success'}), 200

@app.route('/tasks')
def tasks():
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    lang = user[7] if user else 'en'
    translation = get_translation(lang)
    active_tasks = get_active_tasks()
    if not user:
        return redirect(url_for('start', tg_id=tg_id))
    completed_tasks = user[6].split(',') if user[6] else []
    available_tasks = [task for task in active_tasks if str(task[0]) not in completed_tasks]
    available_tasks_ids = ','.join(str(task[0]) for task in available_tasks)
    update_available_tasks(tg_id, available_tasks_ids)
    all_tasks = available_tasks + [task for task in active_tasks if str(task[0]) in completed_tasks]
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    task_statuses = {}
    for task in all_tasks:
        if str(task[0]) in completed_tasks:
            task_statuses[task[0]] = 'completed'
        else:
            cursor.execute('SELECT screen FROM task_check WHERE tg_id = ? AND task_id = ?', (tg_id, task[0]))
            record = cursor.fetchone()
            if record:
                task_statuses[task[0]] = 'screenshot' if record[0] else 'upload'
            else:
                task_statuses[task[0]] = 'link'
    conn.close()
    return render_template('tasks.html', available_tasks=all_tasks, task_statuses=task_statuses, tg_id=tg_id, translation=translation)


@app.route('/record_task_check', methods=['POST'])
def record_task_check():
    data = request.json
    tg_id = data['tg_id']
    task_id = data['task_id']
    reward = data['reward']
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Проверка наличия записи
    cursor.execute('SELECT * FROM task_check WHERE tg_id = ? AND task_id = ?', (tg_id, task_id))
    existing_record = cursor.fetchone()
    if existing_record:
        # Обновление существующей записи
        cursor.execute('''
            UPDATE task_check
            SET reward = ?, date = CURRENT_TIMESTAMP
            WHERE tg_id = ? AND task_id = ?
        ''', (reward, tg_id, task_id))
    else:
        # Вставка новой записи
        cursor.execute('''
            INSERT INTO task_check (tg_id, task_id, reward, date)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (tg_id, task_id, reward))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})


# Маршрут для загрузки скриншота
@app.route('/upload_screenshot', methods=['POST'])
def upload_screenshot():
    tg_id = request.form['tg_id']
    task_id = request.form['task_id']
    file = request.files['screenshot']
    
    if not file.content_type.startswith('image/'):
        return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400
    
    filename = f"{tg_id}-{task_id}.png"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE task_check SET screen = ? WHERE tg_id = ? AND task_id = ?
    ''', (file_path, tg_id, task_id))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/task_checking')
def task_checking():
    password = request.args.get('password')
    if password != '123':  # Проверка пароля
        return redirect(url_for('main'))

    # Получение записей из task_check, где поле screen не пустое
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM task_check WHERE screen IS NOT NULL')
    task_checks = cursor.fetchall()
    conn.close()

    tasks = {task[0]: task for task in get_active_tasks() + get_inactive_tasks()}

    # Подготовка данных для шаблона
    task_checks_data = []
    for task_check in task_checks:
        screen_path = os.path.basename(task_check[3])
        screen_url = url_for('uploaded_file', filename=screen_path)
        task_checks_data.append({
            'tg_id': task_check[0],
            'task_id': task_check[1],
            'reward': task_check[2],
            'screen_url': screen_url,
            'screen_path': task_check[3]
        })

    return render_template('task_checking.html', task_checks=task_checks_data, tasks=tasks)

@app.route('/accept_task', methods=['POST'])
def accept_task():
    data = request.json
    tg_id = data['tg_id']
    task_id = data['task_id']
    reward = data['reward']
    screen = data['screen']

    # Обновление баланса пользователя и добавление выполненного задания
    user = get_user_by_tg_id(tg_id)
    if user:
        coins = int(user[3]) + int(reward)
        completed_tasks = user[6] + f",{task_id}" if user[6] else str(task_id)
        update_user_coins_and_tasks(tg_id, coins, completed_tasks)

    # Удаление записи из task_check и удаление скриншота
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM task_check WHERE tg_id = ? AND task_id = ?', (tg_id, task_id))
    conn.commit()
    conn.close()

    if os.path.exists(screen):
        os.remove(screen)

    return jsonify({'status': 'success'})

@app.route('/screenshots/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/reject_task', methods=['POST'])
def reject_task():
    data = request.json
    tg_id = data['tg_id']
    task_id = data['task_id']
    screen = data['screen']

    # Удаление записи из task_check и удаление скриншота
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM task_check WHERE tg_id = ? AND task_id = ?', (tg_id, task_id))
    conn.commit()
    conn.close()

    if os.path.exists(screen):
        os.remove(screen)

    return jsonify({'status': 'success'})

@app.route('/update_language', methods=['POST'])
def update_language():
    data = request.json
    tg_id = data['tg_id']
    lang = data['lang']
    logging.debug(f"Updating language for user: tg_id={tg_id}, lang={lang}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET lang = ? WHERE tg_id = ?', (lang, tg_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/get_language')
def get_language():
    tg_id = request.args.get('tg_id')
    user = get_user_by_tg_id(tg_id)
    if user:
        lang = user[7]  # Assuming lang is the 8th field in the user record
        return jsonify({'lang': lang})
    return jsonify({'error': 'User not found'}), 404


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
            cursor.execute('DELETE FROM task_check WHERE tg_id = ? AND task_id = ?', (tg_id, task_id))
            conn.commit()
            if os.path.exists(screen):
                os.remove(screen)
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=auto_accept_tasks, trigger="interval", hours=1)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
