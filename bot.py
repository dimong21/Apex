import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import json
import random
import re
import time
from datetime import datetime, timedelta
import os
import traceback

# ============================================================
# КОНФИГУРАЦИЯ (ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ДЛЯ BOTHOST)
# ============================================================
VK_TOKEN = os.environ.get('VK_TOKEN')
GROUP_ID = int(os.environ.get('GROUP_ID', 0))
OWNER_ID = int(os.environ.get('OWNER_ID', 0))

PREFIXES = ['/', '.', '!', '*']

EXCHANGE_RATES = {
    "euro_to_ruble": 98.5,
    "dollar_to_ruble": 91.2,
    "btc_to_dollar": 65000,
    "btc_to_euro": 60000,
    "btc_to_ruble": 5900000
}

# ============================================================
# ПОДКЛЮЧЕНИЕ К VK
# ============================================================
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# ============================================================
# БАЗА ДАННЫХ
# ============================================================
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

# Таблица пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    nickname TEXT,
    balance_euro REAL DEFAULT 100,
    balance_dollar REAL DEFAULT 100,
    balance_ruble REAL DEFAULT 5000,
    balance_btc REAL DEFAULT 0,
    vip_level INTEGER DEFAULT 0,
    vip_until TEXT,
    messages_count INTEGER DEFAULT 0,
    stickers_count INTEGER DEFAULT 0,
    commands_count INTEGER DEFAULT 0,
    warns INTEGER DEFAULT 0,
    join_date TEXT,
    invited_by INTEGER,
    activity_level TEXT DEFAULT "🌱 Новичок",
    agent_number INTEGER,
    agent_rating REAL DEFAULT 0,
    sysban_level INTEGER DEFAULT 0,
    sysban_reason TEXT,
    sysban_by INTEGER,
    last_work TEXT,
    last_bonus TEXT,
    reputation INTEGER DEFAULT 0
)
''')

# Таблица чатов
cursor.execute('''
CREATE TABLE IF NOT EXISTS chats (
    peer_id INTEGER PRIMARY KEY,
    active INTEGER DEFAULT 0,
    games_allowed INTEGER DEFAULT 1,
    max_warns INTEGER DEFAULT 3,
    links_block INTEGER DEFAULT 0,
    on_leave_action TEXT DEFAULT "none",
    union_id INTEGER,
    welcome_message TEXT
)
''')

# Таблица браков
cursor.execute('''
CREATE TABLE IF NOT EXISTS marriages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER,
    user2_id INTEGER,
    date TEXT,
    love_points INTEGER DEFAULT 0,
    UNIQUE(user1_id, user2_id)
)
''')

# Таблица рабов
cursor.execute('''
CREATE TABLE IF NOT EXISTS slaves (
    slave_id INTEGER PRIMARY KEY,
    owner_id INTEGER,
    chains INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    profit_today INTEGER DEFAULT 0,
    last_collect TEXT
)
''')

# Таблица объединений
cursor.execute('''
CREATE TABLE IF NOT EXISTS unions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    owner_id INTEGER,
    created_date TEXT
)
''')

# Таблица ролей в объединениях
cursor.execute('''
CREATE TABLE IF NOT EXISTS union_roles (
    union_id INTEGER,
    user_id INTEGER,
    role_name TEXT,
    priority INTEGER DEFAULT 0,
    PRIMARY KEY(union_id, user_id)
)
''')

# Таблица чатов объединений
cursor.execute('''
CREATE TABLE IF NOT EXISTS union_chats (
    union_id INTEGER,
    peer_id INTEGER,
    PRIMARY KEY(union_id, peer_id)
)
''')

# Таблица агентов
cursor.execute('''
CREATE TABLE IF NOT EXISTS agents (
    user_id INTEGER PRIMARY KEY,
    agent_number INTEGER UNIQUE,
    added_by INTEGER,
    added_date TEXT,
    tickets_closed INTEGER DEFAULT 0,
    commands_access TEXT
)
''')

# Таблица репортов
cursor.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    peer_id INTEGER,
    message TEXT,
    status TEXT DEFAULT "open",
    agent_id INTEGER,
    created_date TEXT,
    closed_date TEXT,
    closed_by INTEGER,
    rating INTEGER
)
''')

# Таблица сообщений репортов
cursor.execute('''
CREATE TABLE IF NOT EXISTS report_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER,
    from_id INTEGER,
    message TEXT,
    date TEXT
)
''')

# Таблица логов
cursor.execute('''
CREATE TABLE IF NOT EXISTS suspicious_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    details TEXT,
    date TEXT
)
''')

# Таблица мутов в репортах
cursor.execute('''
CREATE TABLE IF NOT EXISTS muted_in_reports (
    user_id INTEGER PRIMARY KEY,
    muted_until TEXT
)
''')

# Таблица временных банов
cursor.execute('''
CREATE TABLE IF NOT EXISTS temp_bans (
    user_id INTEGER,
    peer_id INTEGER,
    until TEXT,
    reason TEXT,
    PRIMARY KEY(user_id, peer_id)
)
''')

# Таблица временных мутов
cursor.execute('''
CREATE TABLE IF NOT EXISTS temp_mutes (
    user_id INTEGER,
    peer_id INTEGER,
    until TEXT,
    reason TEXT,
    PRIMARY KEY(user_id, peer_id)
)
''')

# Таблица предложений брака
cursor.execute('''
CREATE TABLE IF NOT EXISTS marriage_proposals (
    from_id INTEGER,
    to_id INTEGER,
    date TEXT,
    PRIMARY KEY(from_id, to_id)
)
''')

# Таблица ролей чата
cursor.execute('''
CREATE TABLE IF NOT EXISTS chat_roles (
    peer_id INTEGER,
    role_name TEXT,
    priority INTEGER,
    PRIMARY KEY(peer_id, role_name)
)
''')

# Таблица для хранения ответов на команды
cursor.execute('''
CREATE TABLE IF NOT EXISTS pending_answers (
    user_id INTEGER,
    command TEXT,
    step INTEGER,
    data TEXT,
    date TEXT
)
''')

conn.commit()

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def send_message(peer_id, text, keyboard=None, attachment=None, reply_to=None):
    try:
        data = {
            'peer_id': peer_id,
            'message': text,
            'random_id': 0
        }
        if keyboard:
            data['keyboard'] = keyboard
        if attachment:
            data['attachment'] = attachment
        if reply_to:
            data['reply_to'] = reply_to
        vk.messages.send(**data)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def get_user_link(user_id, name=None):
    if not name:
        try:
            user = vk.users.get(user_ids=user_id)[0]
            name = f"{user['first_name']} {user['last_name']}"
        except:
            name = f"Пользователь"
    return f"[id{user_id}|{name}]"

def get_user_from_text(text):
    match = re.search(r'@id(\d+)', text)
    if match:
        return int(match.group(1))
    match = re.search(r'vk\.(com|ru)/id(\d+)', text)
    if match:
        return int(match.group(2))
    match = re.search(r'(\d{5,})', text)
    if match:
        return int(match.group(1))
    match = re.search(r'\[id(\d+)\|', text)
    if match:
        return int(match.group(1))
    return None

def parse_time(time_str):
    if time_str == "-1":
        return -1
    match = re.match(r'(\d+)([dhms])', time_str)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == 'd':
        return value * 1440
    elif unit == 'h':
        return value * 60
    elif unit == 'm':
        return value
    elif unit == 's':
        return value // 60
    return None

def get_user_data(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        cursor.execute('''
            INSERT INTO users (user_id, join_date, balance_euro, balance_dollar, balance_ruble, balance_btc)
            VALUES (?, ?, 100, 100, 5000, 0)
        ''', (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return get_user_data(user_id)
    return result

def update_balance(user_id, currency, amount):
    cursor.execute(f"UPDATE users SET balance_{currency} = balance_{currency} + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def has_permission(peer_id, user_id, require_owner=False):
    if user_id == OWNER_ID:
        return True
    try:
        members = vk.messages.getConversationMembers(peer_id=peer_id)
        for member in members['items']:
            if member['member_id'] == user_id:
                if 'is_owner' in member and member['is_owner']:
                    return True
                if 'is_admin' in member and member['is_admin']:
                    return True
                if not require_owner and 'is_admin' in member:
                    return True
    except:
        pass
    return False

def get_next_agent_number():
    cursor.execute("SELECT MAX(agent_number) FROM agents")
    result = cursor.fetchone()
    return (result[0] or 0) + 1

def is_agent(user_id):
    cursor.execute("SELECT user_id FROM agents WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def has_agent_access(user_id, command):
    if user_id == OWNER_ID:
        return True
    cursor.execute("SELECT commands_access FROM agents WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        access = json.loads(result[0])
        return access.get(command, False)
    return False

def add_suspicious_log(user_id, action, details):
    cursor.execute('''
        INSERT INTO suspicious_logs (user_id, action, details, date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, action, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def check_temp_bans_and_mutes():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT user_id, peer_id FROM temp_bans WHERE until < ?", (now,))
    for user_id, peer_id in cursor.fetchall():
        cursor.execute("DELETE FROM temp_bans WHERE user_id = ? AND peer_id = ?", (user_id, peer_id))
    cursor.execute("SELECT user_id, peer_id FROM temp_mutes WHERE until < ?", (now,))
    for user_id, peer_id in cursor.fetchall():
        cursor.execute("DELETE FROM temp_mutes WHERE user_id = ? AND peer_id = ?", (user_id, peer_id))
    conn.commit()

def get_agent_number(user_id):
    cursor.execute("SELECT agent_number FROM agents WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# ============================================================
# КЛАВИАТУРЫ
# ============================================================
def get_vip_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button("👑 VIP 1 (1000€)", VkKeyboardColor.PRIMARY, payload={"action": "buy_vip", "level": 1})
    keyboard.add_callback_button("💎 VIP 2 (5000€)", VkKeyboardColor.POSITIVE, payload={"action": "buy_vip", "level": 2})
    keyboard.add_line()
    keyboard.add_callback_button("⭐ VIP 3 (15000€)", VkKeyboardColor.NEGATIVE, payload={"action": "buy_vip", "level": 3})
    keyboard.add_callback_button("❌ Закрыть", VkKeyboardColor.SECONDARY, payload={"action": "close"})
    return keyboard

def get_admin_keyboard(target_id):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button("⚠ Варн", VkKeyboardColor.SECONDARY, payload={"action": "admin_warn", "target_id": target_id})
    keyboard.add_callback_button("🔇 Мут", VkKeyboardColor.PRIMARY, payload={"action": "admin_mute", "target_id": target_id})
    keyboard.add_line()
    keyboard.add_callback_button("👢 Кик", VkKeyboardColor.NEGATIVE, payload={"action": "admin_kick", "target_id": target_id})
    keyboard.add_callback_button("🔨 Бан", VkKeyboardColor.NEGATIVE, payload={"action": "admin_ban", "target_id": target_id})
    keyboard.add_line()
    keyboard.add_callback_button("🗑 Снять мут", VkKeyboardColor.SECONDARY, payload={"action": "admin_unmute", "target_id": target_id})
    return keyboard

def get_top_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button("💬 Сообщения", VkKeyboardColor.PRIMARY, payload={"action": "top_messages"})
    keyboard.add_callback_button("🎨 Стикеры", VkKeyboardColor.POSITIVE, payload={"action": "top_stickers"})
    keyboard.add_line()
    keyboard.add_callback_button("⚡ Команды", VkKeyboardColor.SECONDARY, payload={"action": "top_commands"})
    keyboard.add_callback_button("💰 Деньги", VkKeyboardColor.PRIMARY, payload={"action": "top_money"})
    return keyboard

def get_report_keyboard(report_id):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button("📋 Взять репорт", VkKeyboardColor.PRIMARY, payload={"action": "take_report", "report_id": report_id})
    keyboard.add_callback_button("ℹ Инфо", VkKeyboardColor.SECONDARY, payload={"action": "report_info", "report_id": report_id})
    return keyboard

def get_agent_access_keyboard(user_id, current_access):
    keyboard = VkKeyboard(inline=True)
    sysban_status = "✅" if current_access.get("sysban", False) else "❌"
    sysinfo_status = "✅" if current_access.get("sysinfo", False) else "❌"
    logs_status = "✅" if current_access.get("logs", False) else "❌"
    
    keyboard.add_callback_button(f"{sysban_status} /sysban", VkKeyboardColor.PRIMARY if current_access.get("sysban") else VkKeyboardColor.SECONDARY, 
                                 payload={"action": "toggle_access", "target_id": user_id, "command": "sysban"})
    keyboard.add_callback_button(f"{sysinfo_status} /sysinfo", VkKeyboardColor.PRIMARY if current_access.get("sysinfo") else VkKeyboardColor.SECONDARY,
                                 payload={"action": "toggle_access", "target_id": user_id, "command": "sysinfo"})
    keyboard.add_line()
    keyboard.add_callback_button(f"{logs_status} /logs", VkKeyboardColor.PRIMARY if current_access.get("logs") else VkKeyboardColor.SECONDARY,
                                 payload={"action": "toggle_access", "target_id": user_id, "command": "logs"})
    keyboard.add_callback_button("🔒 Закрыть", VkKeyboardColor.NEGATIVE, payload={"action": "close"})
    return keyboard

def get_staff_nick_keyboard(peer_id):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button("📋 Показать с никами", VkKeyboardColor.PRIMARY, payload={"action": "staff_with_nicks", "peer_id": peer_id})
    return keyboard

# ============================================================
# ОСНОВНЫЕ КОМАНДЫ
# ============================================================
def handle_ban(peer_id, user_id, args):
    if not has_permission(peer_id, user_id):
        send_message(peer_id, "❌ У вас нет прав для этой команды!")
        return
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /ban @пользователь [время: 1d/2h/30m/-1] [причина]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    time_str = args[1]
    minutes = parse_time(time_str)
    if minutes is None:
        reason = " ".join(args[1:])
        minutes = 1440
    else:
        reason = " ".join(args[2:]) if len(args) > 2 else "Не указана"
    until = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S") if minutes != -1 else "никогда"
    try:
        if minutes == -1:
            vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
            send_message(peer_id, f"🔨 {get_user_link(user_id)} забанил {get_user_link(target_id)} НАВСЕГДА\n📝 Причина: {reason}")
        else:
            cursor.execute("INSERT OR REPLACE INTO temp_bans (user_id, peer_id, until, reason) VALUES (?, ?, ?, ?)",
                          (target_id, peer_id, until, reason))
            conn.commit()
            vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
            send_message(peer_id, f"🔨 {get_user_link(user_id)} забанил {get_user_link(target_id)} на {time_str}\n📝 Причина: {reason}")
        add_suspicious_log(target_id, "ban", f"Забанен в чате {peer_id} пользователем {user_id} на {time_str}: {reason}")
    except Exception as e:
        send_message(peer_id, f"❌ Ошибка: {e}")

def handle_kick(peer_id, user_id, args):
    if not has_permission(peer_id, user_id):
        send_message(peer_id, "❌ У вас нет прав для этой команды!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /kick @пользователь [причина]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    reason = " ".join(args[1:]) if len(args) > 1 else "Не указана"
    try:
        vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
        send_message(peer_id, f"👢 {get_user_link(user_id)} кикнул {get_user_link(target_id)}\n📝 Причина: {reason}")
        add_suspicious_log(target_id, "kick", f"Кикнут в чате {peer_id} пользователем {user_id}: {reason}")
    except Exception as e:
        send_message(peer_id, f"❌ Ошибка: {e}")

def handle_mute(peer_id, user_id, args):
    if not has_permission(peer_id, user_id):
        send_message(peer_id, "❌ У вас нет прав для этой команды!")
        return
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /mute @пользователь [время: 1d/2h/30m] [причина]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    time_str = args[1]
    minutes = parse_time(time_str)
    if minutes is None:
        reason = " ".join(args[1:])
        minutes = 60
    else:
        reason = " ".join(args[2:]) if len(args) > 2 else "Не указана"
    until = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO temp_mutes (user_id, peer_id, until, reason) VALUES (?, ?, ?, ?)",
                  (target_id, peer_id, until, reason))
    conn.commit()
    send_message(peer_id, f"🔇 {get_user_link(user_id)} замутил {get_user_link(target_id)} на {time_str}\n📝 Причина: {reason}")
    add_suspicious_log(target_id, "mute", f"Замучен в чате {peer_id} пользователем {user_id} на {time_str}: {reason}")

def handle_warn(peer_id, user_id, args):
    if not has_permission(peer_id, user_id):
        send_message(peer_id, "❌ У вас нет прав для этой команды!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /warn @пользователь [причина]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    reason = " ".join(args[1:]) if len(args) > 1 else "Не указана"
    user_data = get_user_data(target_id)
    cursor.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (target_id,))
    conn.commit()
    new_warns = user_data[11] + 1
    cursor.execute("SELECT max_warns FROM chats WHERE peer_id = ?", (peer_id,))
    max_warns = cursor.fetchone()
    max_warns_val = max_warns[0] if max_warns else 3
    send_message(peer_id, f"⚠ {get_user_link(user_id)} выдал варн {get_user_link(target_id)}\n⚠ Предупреждений: {new_warns}/{max_warns_val}\n📝 Причина: {reason}")
    if new_warns >= max_warns_val:
        try:
            vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
            send_message(peer_id, f"🔨 {get_user_link(target_id)} автоматически забанен за {max_warns_val} варна!")
        except:
            pass

def handle_unmute(peer_id, user_id, args):
    if not has_permission(peer_id, user_id):
        send_message(peer_id, "❌ У вас нет прав для этой команды!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /unmute @пользователь")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    cursor.execute("DELETE FROM temp_mutes WHERE user_id = ? AND peer_id = ?", (target_id, peer_id))
    conn.commit()
    send_message(peer_id, f"🔊 {get_user_link(user_id)} снял мут с {get_user_link(target_id)}")

def handle_stats(peer_id, user_id, args):
    target_id = get_user_from_text(" ".join(args)) if args else user_id
    if not target_id:
        target_id = user_id
    user_data = get_user_data(target_id)
    chat_data = cursor.execute("SELECT max_warns FROM chats WHERE peer_id = ?", (peer_id,)).fetchone()
    max_warns = chat_data[0] if chat_data else 3
    
    # Определяем статус (владелец бота или обычный)
    status = "✨ Пользователь"
    if target_id == OWNER_ID:
        status = "👑 ВЛАДЕЛЕЦ БОТА"
    elif user_data[6] > 0:
        status = f"💎 VIP {user_data[6]}"
    
    agent_text = ""
    if user_data[15]:
        agent_text = f"\n🕵️ Агент поддержки №{user_data[15]}\n⭐ Рейтинг: {user_data[16]:.1f}"
    
    sysban_text = ""
    if user_data[17] == 1:
        sysban_text = "\n🚫 В ЧС БОТА"
    elif user_data[17] == 2:
        sysban_text = "\n💰 Баланс обнулён"
    elif user_data[17] == 3:
        sysban_text = "\n🔒 Команды заблокированы"
    
    text = f"""🔍 *Информация о пользователе:*

👤 *Статус:* {status}
⚠ *Предупреждения:* {user_data[11]}/{max_warns}
📄 *Никнейм:* {user_data[1] or 'Не задан'}

📋 *Глобальная информация:*
💰 *Баланс:* {user_data[2]:.2f}€ | {user_data[3]:.2f}$ | {user_data[4]:.2f}₽ | {user_data[5]:.8f}₿
✍ *Сообщений:* {user_data[7]}
🎨 *Стикеров:* {user_data[8]}
⚡ *Команд:* {user_data[9]}
📅 *В чате с:* {user_data[12]}
🕹 *Активность:* {user_data[14]}{agent_text}{sysban_text}
🆔 *ID:* {target_id}"""
    send_message(peer_id, text)

def handle_vip(peer_id, user_id):
    user_data = get_user_data(user_id)
    if user_data[6] > 0:
        text = f"""💎 *Ваш VIP статус*

Уровень: {user_data[6]}
Действует до: {user_data[7]}

*Привилегии VIP {user_data[6]}:*
• +{user_data[6] * 5}% к заработку
• Доступ к эксклюзивным командам
• Особый статус в /stats"""
        send_message(peer_id, text)
    else:
        text = "💎 *VIP Магазин*\n\nВыберите уровень для покупки:"
        send_message(peer_id, text, keyboard=get_vip_keyboard().get_keyboard())

def handle_balance(peer_id, user_id, args):
    target_id = get_user_from_text(" ".join(args)) if args else user_id
    if not target_id:
        target_id = user_id
    user_data = get_user_data(target_id)
    text = f"""💰 *Баланс {get_user_link(target_id)}*

💶 Евро: {user_data[2]:.2f} €
💵 Доллары: {user_data[3]:.2f} $
💷 Рубли: {user_data[4]:.2f} ₽
🪙 Биткоины: {user_data[5]:.8f} ₿

📈 *Курсы:* 1₿ = {EXCHANGE_RATES['btc_to_dollar']}$ | 1€ = {EXCHANGE_RATES['euro_to_ruble']}₽"""
    send_message(peer_id, text)

def handle_pay(peer_id, user_id, args):
    if len(args) < 3:
        send_message(peer_id, "❌ Использование: /pay @пользователь [euro/dollar/ruble/btc] [сумма]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    currency = args[1].lower()
    if currency not in ['euro', 'dollar', 'ruble', 'btc']:
        send_message(peer_id, "❌ Доступные валюты: euro, dollar, ruble, btc")
        return
    try:
        amount = float(args[2])
    except:
        send_message(peer_id, "❌ Неверная сумма!")
        return
    if amount <= 0:
        send_message(peer_id, "❌ Сумма должна быть положительной!")
        return
    sender_data = get_user_data(user_id)
    sender_balance = sender_data[2 if currency == 'euro' else 3 if currency == 'dollar' else 4 if currency == 'ruble' else 5]
    if sender_balance < amount:
        send_message(peer_id, f"❌ Недостаточно средств! У вас {sender_balance:.2f} {currency}")
        return
    update_balance(user_id, currency, -amount)
    update_balance(target_id, currency, amount)
    send_message(peer_id, f"💸 {get_user_link(user_id)} перевёл {get_user_link(target_id)} {amount:.2f} {currency}")

def handle_course(peer_id):
    text = f"""📊 *Текущие курсы валют*

1 ₿ = {EXCHANGE_RATES['btc_to_dollar']} $
1 ₿ = {EXCHANGE_RATES['btc_to_euro']} €
1 ₿ = {EXCHANGE_RATES['btc_to_ruble']:,.0f} ₽
1 € = {EXCHANGE_RATES['euro_to_ruble']:.2f} ₽
1 $ = {EXCHANGE_RATES['dollar_to_ruble']:.2f} ₽

*Конвертация:* /convert [сумма] [из] [в]"""
    send_message(peer_id, text)

def handle_convert(peer_id, user_id, args):
    if len(args) < 3:
        send_message(peer_id, "❌ Использование: /convert [сумма] [euro/dollar/ruble/btc] [euro/dollar/ruble/btc]")
        return
    try:
        amount = float(args[0])
    except:
        send_message(peer_id, "❌ Неверная сумма!")
        return
    from_curr = args[1].lower()
    to_curr = args[2].lower()
    ruble_amount = 0
    if from_curr == 'euro':
        ruble_amount = amount * EXCHANGE_RATES['euro_to_ruble']
    elif from_curr == 'dollar':
        ruble_amount = amount * EXCHANGE_RATES['dollar_to_ruble']
    elif from_curr == 'ruble':
        ruble_amount = amount
    elif from_curr == 'btc':
        ruble_amount = amount * EXCHANGE_RATES['btc_to_ruble']
    else:
        send_message(peer_id, "❌ Неверная исходная валюта!")
        return
    result = 0
    if to_curr == 'euro':
        result = ruble_amount / EXCHANGE_RATES['euro_to_ruble']
    elif to_curr == 'dollar':
        result = ruble_amount / EXCHANGE_RATES['dollar_to_ruble']
    elif to_curr == 'ruble':
        result = ruble_amount
    elif to_curr == 'btc':
        result = ruble_amount / EXCHANGE_RATES['btc_to_ruble']
    else:
        send_message(peer_id, "❌ Неверная целевая валюта!")
        return
    send_message(peer_id, f"💱 {amount:.2f} {from_curr} = {result:.8f} {to_curr}")

def handle_roulette(peer_id, user_id, args):
    chat_data = cursor.execute("SELECT games_allowed FROM chats WHERE peer_id = ?", (peer_id,)).fetchone()
    if chat_data and chat_data[0] == 0:
        send_message(peer_id, "🎮 Игры запрещены в этой беседе!")
        return
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /рулетка [red/black] [сумма]")
        return
    color = args[0].lower()
    if color not in ['red', 'black']:
        send_message(peer_id, "❌ Ставка только на red или black!")
        return
    try:
        amount = float(args[1])
    except:
        send_message(peer_id, "❌ Неверная сумма!")
        return
    user_data = get_user_data(user_id)
    if user_data[2] < amount:
        send_message(peer_id, f"❌ Недостаточно евро! У вас {user_data[2]:.2f}€")
        return
    result_color = random.choice(['red', 'black'])
    number = random.randint(0, 36)
    if color == result_color:
        win_amount = amount * 2
        update_balance(user_id, 'euro', win_amount)
        send_message(peer_id, f"🎰 *РУЛЕТКА*\n\nВыпало: {number} {result_color}\n✅ {get_user_link(user_id)} выиграл {win_amount:.2f}€!")
    else:
        update_balance(user_id, 'euro', -amount)
        send_message(peer_id, f"🎰 *РУЛЕТКА*\n\nВыпало: {number} {result_color}\n❌ {get_user_link(user_id)} проиграл {amount:.2f}€!")

def handle_work(peer_id, user_id):
    user_data = get_user_data(user_id)
    last_work = user_data[20]
    if last_work:
        last_time = datetime.strptime(last_work, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_time < timedelta(hours=1):
            remaining = 3600 - (datetime.now() - last_time).seconds
            minutes = remaining // 60
            send_message(peer_id, f"⏰ Работать можно раз в час! Подождите {minutes} минут.")
            return
    vip_bonus = 1 + (user_data[6] * 0.05) if user_data[6] > 0 else 1
    earnings = random.randint(50, 200) * vip_bonus
    update_balance(user_id, 'euro', earnings)
    cursor.execute("UPDATE users SET last_work = ? WHERE user_id = ?", 
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    send_message(peer_id, f"💼 {get_user_link(user_id)} поработал и заработал {earnings:.2f}€!")

def handle_bonus(peer_id, user_id):
    user_data = get_user_data(user_id)
    last_bonus = user_data[21]
    if last_bonus:
        last_time = datetime.strptime(last_bonus, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_time < timedelta(days=1):
            remaining = 86400 - (datetime.now() - last_time).seconds
            hours = remaining // 3600
            send_message(peer_id, f"🎁 Бонус можно брать раз в день! Подождите {hours} часов.")
            return
    bonus = random.randint(200, 500)
    update_balance(user_id, 'euro', bonus)
    cursor.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    send_message(peer_id, f"🎁 {get_user_link(user_id)} получил дневной бонус {bonus:.2f}€!")

def handle_snick(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /snick [новый ник]")
        return
    new_nick = " ".join(args)[:32]
    cursor.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (new_nick, user_id))
    conn.commit()
    send_message(peer_id, f"✅ {get_user_link(user_id)} сменил ник на «{new_nick}»")

def handle_rnick(peer_id, user_id):
    cursor.execute("UPDATE users SET nickname = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    send_message(peer_id, f"✅ {get_user_link(user_id)} удалил свой ник")

def handle_nlist(peer_id):
    cursor.execute("SELECT user_id, nickname FROM users WHERE nickname IS NOT NULL LIMIT 50")
    users = cursor.fetchall()
    if not users:
        send_message(peer_id, "📋 Ники не заданы")
        return
    text = "📋 *Список ников:*\n"
    for uid, nickname in users:
        text += f"• {get_user_link(uid)} — {nickname}\n"
    send_message(peer_id, text)

def handle_findnick(peer_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /понику [ник]")
        return
    search_nick = " ".join(args).lower()
    cursor.execute("SELECT user_id, nickname FROM users WHERE LOWER(nickname) LIKE ?", (f"%{search_nick}%",))
    users = cursor.fetchall()
    if not users:
        send_message(peer_id, f"❌ Пользователь с ником «{search_nick}» не найден")
        return
    text = f"🔍 *Результаты поиска «{search_nick}»:*\n"
    for uid, nickname in users:
        text += f"• {get_user_link(uid)} — {nickname}\n"
    send_message(peer_id, text)

def handle_ping(peer_id):
    start = time.time()
    send_message(peer_id, "🏓 Понг!")
    end = time.time()
    latency = round((end - start) * 1000)
    send_message(peer_id, f"⚡ Задержка: {latency} мс")

def handle_settings(peer_id, user_id, args):
    if not has_permission(peer_id, user_id, require_owner=True):
        send_message(peer_id, "❌ Только владелец чата может менять настройки!")
        return
    if len(args) < 2:
        send_message(peer_id, """⚙ *Настройки беседы*
/settings games on/off - разрешить игры
/settings warns [1-10] - макс варнов
/settings links on/off - блокировка ссылок
/settings leave [kick/mute/none] - действие при выходе
/settings welcome [текст] - приветствие (off - удалить)""")
        return
    setting = args[0].lower()
    value = args[1].lower()
    if setting == "games":
        cursor.execute("UPDATE chats SET games_allowed = ? WHERE peer_id = ?", (1 if value == "on" else 0, peer_id))
        send_message(peer_id, f"✅ Игры {'разрешены' if value == 'on' else 'запрещены'}")
    elif setting == "warns":
        try:
            warns = int(value)
            if 1 <= warns <= 10:
                cursor.execute("UPDATE chats SET max_warns = ? WHERE peer_id = ?", (warns, peer_id))
                send_message(peer_id, f"✅ Максимум варнов: {warns}")
            else:
                send_message(peer_id, "❌ Число от 1 до 10")
        except:
            send_message(peer_id, "❌ Введите число")
    elif setting == "links":
        cursor.execute("UPDATE chats SET links_block = ? WHERE peer_id = ?", (1 if value == "on" else 0, peer_id))
        send_message(peer_id, f"✅ Блокировка ссылок {'включена' if value == 'on' else 'выключена'}")
    elif setting == "leave":
        if value in ["kick", "mute", "none"]:
            cursor.execute("UPDATE chats SET on_leave_action = ? WHERE peer_id = ?", (value, peer_id))
            send_message(peer_id, f"✅ При выходе: {value}")
        else:
            send_message(peer_id, "❌ Варианты: kick, mute, none")
    elif setting == "welcome":
        if value == "off":
            cursor.execute("UPDATE chats SET welcome_message = NULL WHERE peer_id = ?", (peer_id,))
            send_message(peer_id, "✅ Приветствие удалено")
        else:
            welcome_text = " ".join(args[1:])
            cursor.execute("UPDATE chats SET welcome_message = ? WHERE peer_id = ?", (welcome_text, peer_id))
            send_message(peer_id, f"✅ Приветствие установлено")
    conn.commit()

def handle_start(peer_id, user_id):
    if user_id != OWNER_ID:
        send_message(peer_id, "❌ Активировать бота может только владелец!")
        return
    cursor.execute("SELECT active FROM chats WHERE peer_id = ?", (peer_id,))
    result = cursor.fetchone()
    if result and result[0] == 1:
        send_message(peer_id, "✅ Бот уже активирован!")
        return
    cursor.execute("INSERT OR REPLACE INTO chats (peer_id, active) VALUES (?, 1)", (peer_id,))
    conn.commit()
    send_message(peer_id, f"""✅ *Беседа активирована!*
Владелец: {get_user_link(user_id)}

📚 /help - список команд
📝 /report [текст] - сообщить о проблеме

Приятного общения!""")

# ============================================================
# СИСТЕМА ОБЪЕДИНЕНИЙ (РАБОЧАЯ)
# ============================================================
def handle_union(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, """🏢 *Объединения*

/union create [название] - создать объединение
/union add [id] - добавить текущую беседу в объединение
/union addchat [union_id] [peer_id] - добавить другую беседу
/union info - информация об объединении
/union list - список объединений
/union delete [union_id] - удалить объединение""")
        return
    
    subcmd = args[0].lower()
    
    if subcmd == "create":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /union create [название]")
            return
        name = " ".join(args[1:])
        cursor.execute("INSERT INTO unions (name, owner_id, created_date) VALUES (?, ?, ?)",
                      (name, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        union_id = cursor.lastrowid
        cursor.execute("INSERT INTO union_roles (union_id, user_id, role_name, priority) VALUES (?, ?, '👑 Владелец', 100)", (union_id, user_id))
        conn.commit()
        send_message(peer_id, f"✅ Объединение «{name}» создано! ID: {union_id}")
    
    elif subcmd == "add":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /union add [union_id]")
            return
        try:
            union_id = int(args[1])
        except:
            send_message(peer_id, "❌ Неверный ID объединения!")
            return
        cursor.execute("SELECT owner_id FROM unions WHERE id = ?", (union_id,))
        union = cursor.fetchone()
        if not union:
            send_message(peer_id, "❌ Объединение не найдено!")
            return
        if union[0] != user_id and user_id != OWNER_ID:
            send_message(peer_id, "❌ Вы не владелец этого объединения!")
            return
        cursor.execute("INSERT OR REPLACE INTO union_chats (union_id, peer_id) VALUES (?, ?)", (union_id, peer_id))
        cursor.execute("UPDATE chats SET union_id = ? WHERE peer_id = ?", (union_id, peer_id))
        conn.commit()
        send_message(peer_id, f"✅ Беседа добавлена в объединение ID: {union_id}")
    
    elif subcmd == "addchat":
        if len(args) < 3:
            send_message(peer_id, "❌ Использование: /union addchat [union_id] [peer_id]")
            return
        try:
            union_id = int(args[1])
            target_peer = int(args[2])
        except:
            send_message(peer_id, "❌ Неверные ID!")
            return
        cursor.execute("SELECT owner_id FROM unions WHERE id = ?", (union_id,))
        union = cursor.fetchone()
        if not union:
            send_message(peer_id, "❌ Объединение не найдено!")
            return
        if union[0] != user_id and user_id != OWNER_ID:
            send_message(peer_id, "❌ Вы не владелец этого объединения!")
            return
        cursor.execute("INSERT OR REPLACE INTO union_chats (union_id, peer_id) VALUES (?, ?)", (union_id, target_peer))
        cursor.execute("UPDATE chats SET union_id = ? WHERE peer_id = ?", (union_id, target_peer))
        conn.commit()
        send_message(peer_id, f"✅ Беседа {target_peer} добавлена в объединение ID: {union_id}")
    
    elif subcmd == "info":
        union_id = None
        cursor.execute("SELECT union_id FROM chats WHERE peer_id = ?", (peer_id,))
        result = cursor.fetchone()
        if result and result[0]:
            union_id = result[0]
        elif len(args) > 1:
            try:
                union_id = int(args[1])
            except:
                pass
        if not union_id:
            send_message(peer_id, "❌ Эта беседа не привязана к объединению или укажите ID")
            return
        cursor.execute("SELECT * FROM unions WHERE id = ?", (union_id,))
        union = cursor.fetchone()
        if not union:
            send_message(peer_id, "❌ Объединение не найдено!")
            return
        cursor.execute("SELECT COUNT(*) FROM union_chats WHERE union_id = ?", (union_id,))
        chats_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM union_roles WHERE union_id = ?", (union_id,))
        members_count = cursor.fetchone()[0]
        text = f"""🏢 *Информация об объединении*

📛 Название: {union[1]}
🆔 ID: {union[0]}
👑 Владелец: {get_user_link(union[2])}
📅 Создано: {union[3]}
💬 Бесед: {chats_count}
👥 Участников: {members_count}"""
        send_message(peer_id, text)
    
    elif subcmd == "list":
        cursor.execute("SELECT id, name FROM unions WHERE owner_id = ?", (user_id,))
        unions = cursor.fetchall()
        if not unions:
            send_message(peer_id, "❌ У вас нет объединений!")
            return
        text = "🏢 *Ваши объединения:*\n\n"
        for uid, name in unions:
            text += f"🆔 {uid} — {name}\n"
        send_message(peer_id, text)
    
    elif subcmd == "delete":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /union delete [union_id]")
            return
        try:
            union_id = int(args[1])
        except:
            send_message(peer_id, "❌ Неверный ID!")
            return
        cursor.execute("SELECT owner_id FROM unions WHERE id = ?", (union_id,))
        union = cursor.fetchone()
        if not union:
            send_message(peer_id, "❌ Объединение не найдено!")
            return
        if union[0] != user_id and user_id != OWNER_ID:
            send_message(peer_id, "❌ Вы не владелец этого объединения!")
            return
        cursor.execute("DELETE FROM unions WHERE id = ?", (union_id,))
        cursor.execute("DELETE FROM union_chats WHERE union_id = ?", (union_id,))
        cursor.execute("DELETE FROM union_roles WHERE union_id = ?", (union_id,))
        cursor.execute("UPDATE chats SET union_id = NULL WHERE union_id = ?", (union_id,))
        conn.commit()
        send_message(peer_id, f"✅ Объединение ID {union_id} удалено!")

def handle_grole(peer_id, user_id, args):
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /grole [@user] [роль]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    role = " ".join(args[1:])
    cursor.execute("SELECT union_id FROM chats WHERE peer_id = ?", (peer_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        send_message(peer_id, "❌ Эта беседа не привязана к объединению!")
        return
    union_id = result[0]
    cursor.execute("SELECT owner_id FROM unions WHERE id = ?", (union_id,))
    union = cursor.fetchone()
    if not union or (union[0] != user_id and user_id != OWNER_ID):
        send_message(peer_id, "❌ Только владелец объединения может выдавать роли!")
        return
    cursor.execute("INSERT OR REPLACE INTO union_roles (union_id, user_id, role_name) VALUES (?, ?, ?)", (union_id, target_id, role))
    conn.commit()
    send_message(peer_id, f"✅ {get_user_link(target_id)} получил роль «{role}» в объединении!")

def handle_gban(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /gban [@user]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    cursor.execute("SELECT union_id FROM chats WHERE peer_id = ?", (peer_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        send_message(peer_id, "❌ Эта беседа не привязана к объединению!")
        return
    union_id = result[0]
    cursor.execute("SELECT owner_id FROM unions WHERE id = ?", (union_id,))
    union = cursor.fetchone()
    if not union or (union[0] != user_id and user_id != OWNER_ID):
        send_message(peer_id, "❌ Только владелец объединения может банить!")
        return
    cursor.execute("SELECT peer_id FROM union_chats WHERE union_id = ?", (union_id,))
    for chat in cursor.fetchall():
        try:
            vk.messages.removeChatUser(chat_id=chat[0] - 2000000000, user_id=target_id)
        except:
            pass
    send_message(peer_id, f"🔨 {get_user_link(target_id)} забанен во всех беседах объединения!")

def handle_gkick(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /gkick [@user]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    cursor.execute("SELECT union_id FROM chats WHERE peer_id = ?", (peer_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        send_message(peer_id, "❌ Эта беседа не привязана к объединению!")
        return
    union_id = result[0]
    cursor.execute("SELECT owner_id FROM unions WHERE id = ?", (union_id,))
    union = cursor.fetchone()
    if not union or (union[0] != user_id and user_id != OWNER_ID):
        send_message(peer_id, "❌ Только владелец объединения может кикать!")
        return
    try:
        vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
        send_message(peer_id, f"👢 {get_user_link(target_id)} кикнут из беседы!")
    except:
        send_message(peer_id, "❌ Ошибка при кике!")

def handle_gmute(peer_id, user_id, args):
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /gmute [@user] [время]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    time_str = args[1]
    minutes = parse_time(time_str)
    if minutes is None:
        minutes = 60
    until = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT union_id FROM chats WHERE peer_id = ?", (peer_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        send_message(peer_id, "❌ Эта беседа не привязана к объединению!")
        return
    cursor.execute("SELECT peer_id FROM union_chats WHERE union_id = ?", (result[0],))
    for chat in cursor.fetchall():
        cursor.execute("INSERT OR REPLACE INTO temp_mutes (user_id, peer_id, until, reason) VALUES (?, ?, ?, ?)",
                      (target_id, chat[0], until, "Мут в объединении"))
    conn.commit()
    send_message(peer_id, f"🔇 {get_user_link(target_id)} замучен во всех беседах объединения на {time_str}!")

def handle_gzov(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /gzov [текст]")
        return
    text = " ".join(args)
    cursor.execute("SELECT union_id FROM chats WHERE peer_id = ?", (peer_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        send_message(peer_id, "❌ Эта беседа не привязана к объединению!")
        return
    union_id = result[0]
    cursor.execute("SELECT peer_id FROM union_chats WHERE union_id = ?", (union_id,))
    for chat in cursor.fetchall():
        try:
            send_message(chat[0], f"📢 *ЗОВ ОБЪЕДИНЕНИЯ* от {get_user_link(user_id)}\n\n{text}")
        except:
            pass
    send_message(peer_id, f"✅ Зов отправлен во все беседы объединения!")

def handle_gnick(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /gnick [@пользователь]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    user_data = get_user_data(target_id)
    send_message(peer_id, f"📝 Ник {get_user_link(target_id)}: {user_data[1] or 'Не задан'}")

# ============================================================
# СИСТЕМА АГЕНТОВ И СЕКРЕТНЫЕ КОМАНДЫ
# ============================================================
def handle_agent(peer_id, user_id, args):
    if user_id != OWNER_ID:
        send_message(peer_id, "❌ Только владелец бота может управлять агентами!")
        return
    if len(args) < 2:
        send_message(peer_id, """🕵️ *Управление агентами*

/agent add [id/ссылка] - добавить агента
/agent del [id] - удалить агента
/agent info [id] - информация об агенте
/agent access [id] - настройка доступов""")
        return
    subcmd = args[0].lower()
    if subcmd == "add":
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        if is_agent(target_id):
            send_message(peer_id, "❌ Пользователь уже является агентом!")
            return
        agent_num = get_next_agent_number()
        cursor.execute("INSERT INTO agents (user_id, agent_number, added_by, added_date, commands_access, tickets_closed) VALUES (?, ?, ?, ?, ?, 0)",
                      (target_id, agent_num, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), json.dumps({})))
        conn.commit()
        cursor.execute("UPDATE users SET agent_number = ? WHERE user_id = ?", (agent_num, target_id))
        conn.commit()
        send_message(peer_id, f"✅ Агент №{agent_num} добавлен! {get_user_link(target_id)}")
    elif subcmd == "del":
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("DELETE FROM agents WHERE user_id = ?", (target_id,))
        conn.commit()
        cursor.execute("UPDATE users SET agent_number = NULL WHERE user_id = ?", (target_id,))
        conn.commit()
        send_message(peer_id, f"❌ Агент удалён: {get_user_link(target_id)}")
    elif subcmd == "info":
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("SELECT * FROM agents WHERE user_id = ?", (target_id,))
        agent = cursor.fetchone()
        if not agent:
            send_message(peer_id, "❌ Пользователь не является агентом!")
            return
        text = f"""🕵️ *Информация об агенте*

👤 {get_user_link(target_id)}
🔢 Номер: #{agent[1]}
📅 Добавлен: {agent[3]}
📊 Закрыто тикетов: {agent[5]}
⭐ Рейтинг: {get_user_data(target_id)[16]:.1f}"""
        send_message(peer_id, text)
    elif subcmd == "access":
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("SELECT commands_access FROM agents WHERE user_id = ?", (target_id,))
        result = cursor.fetchone()
        current_access = json.loads(result[0]) if result and result[0] else {}
        text = f"🔐 *Настройка доступов агента* {get_user_link(target_id)}\n\nАгент №{get_agent_number(target_id)}\n\nНажмите на кнопки для изменения доступа:"
        send_message(peer_id, text, keyboard=get_agent_access_keyboard(target_id, current_access).get_keyboard())

def handle_sysban(peer_id, user_id, args):
    if not has_agent_access(user_id, "sysban") and user_id != OWNER_ID:
        send_message(peer_id, "❌ У вас нет доступа к этой команде!")
        return
    if len(args) < 2:
        send_message(peer_id, """🚫 *Системный бан*

/sysban [@пользователь] [уровень] [причина]

*Уровни:*
1 - Полный ЧС (кик из чатов, обнуление)
2 - Слив денег (обнуление баланса)
3 - Блок команд
4 - Полный снос из БД""")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    try:
        level = int(args[1])
    except:
        send_message(peer_id, "❌ Уровень должен быть числом 1-4!")
        return
    reason = " ".join(args[2:]) if len(args) > 2 else "Не указана"
    
    agent_num = get_agent_number(user_id)
    issuer = f"Агент №{agent_num}" if agent_num else get_user_link(user_id)
    
    if level == 1:
        cursor.execute("SELECT peer_id FROM chats WHERE active = 1")
        for chat in cursor.fetchall():
            try:
                vk.messages.removeChatUser(chat_id=chat[0] - 2000000000, user_id=target_id)
            except:
                pass
        cursor.execute("UPDATE users SET balance_euro = 0, balance_dollar = 0, balance_ruble = 0, balance_btc = 0 WHERE user_id = ?", (target_id,))
    elif level == 2:
        cursor.execute("UPDATE users SET balance_euro = 0, balance_dollar = 0, balance_ruble = 0, balance_btc = 0 WHERE user_id = ?", (target_id,))
    elif level == 3:
        pass
    elif level == 4:
        cursor.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
        cursor.execute("DELETE FROM slaves WHERE slave_id = ? OR owner_id = ?", (target_id, target_id))
        cursor.execute("DELETE FROM marriages WHERE user1_id = ? OR user2_id = ?", (target_id, target_id))
        cursor.execute("DELETE FROM agents WHERE user_id = ?", (target_id,))
        cursor.execute("DELETE FROM union_roles WHERE user_id = ?", (target_id,))
        send_message(peer_id, f"💀 {get_user_link(target_id)} полностью удалён из БД бота!")
        conn.commit()
        return
    cursor.execute("UPDATE users SET sysban_level = ?, sysban_reason = ?, sysban_by = ? WHERE user_id = ?",
                  (level, reason, user_id, target_id))
    conn.commit()
    send_message(peer_id, f"🚫 {issuer} выдал системный бан (ур. {level}) {get_user_link(target_id)}\n📝 Причина: {reason}")
    add_suspicious_log(target_id, "sysban", f"Системный бан уровня {level} от {user_id}: {reason}")

def handle_unsysban(peer_id, user_id, args):
    if not has_agent_access(user_id, "sysban") and user_id != OWNER_ID:
        send_message(peer_id, "❌ У вас нет доступа к этой команде!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /unsysban @пользователь [причина]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    reason = " ".join(args[1:]) if len(args) > 1 else "Не указана"
    cursor.execute("UPDATE users SET sysban_level = 0, sysban_reason = NULL, sysban_by = NULL WHERE user_id = ?", (target_id,))
    conn.commit()
    send_message(peer_id, f"✅ Снят системный бан с {get_user_link(target_id)}\n📝 Причина: {reason}")

def handle_sysinfo(peer_id, user_id, args):
    if not has_agent_access(user_id, "sysinfo") and user_id != OWNER_ID:
        send_message(peer_id, "❌ У вас нет доступа к этой команде!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /sysinfo @пользователь")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    user_data = get_user_data(target_id)
    text = f"""🔍 *Системная информация о {get_user_link(target_id)}*

🆔 ID: {target_id}
🚫 В ЧС бота: {'✅ Да' if user_data[17] == 1 else '❌ Нет'}
📝 Причина ЧС: {user_data[18] or 'Нет'}
👮 Кто выдал: {get_user_link(user_data[19]) if user_data[19] else 'Нет'}

💰 Баланс: {user_data[2]:.2f}€ | {user_data[3]:.2f}$ | {user_data[4]:.2f}₽ | {user_data[5]:.8f}₿
📊 Сообщений: {user_data[7]} | Стикеров: {user_data[8]} | Команд: {user_data[9]}"""
    send_message(peer_id, text)

def handle_botadmins(peer_id, user_id):
    if not is_agent(user_id) and user_id != OWNER_ID:
        send_message(peer_id, "❌ Только для агентов!")
        return
    cursor.execute("SELECT user_id, agent_number, tickets_closed FROM agents ORDER BY agent_number")
    agents = cursor.fetchall()
    if not agents:
        send_message(peer_id, "❌ Агенты не найдены")
        return
    text = "🕵️ *Список агентов поддержки:*\n\n"
    for agent_id, agent_num, tickets in agents:
        user_data = get_user_data(agent_id)
        text += f"#{agent_num} — {get_user_link(agent_id)}\n📊 Тикетов: {tickets} | ⭐ Рейтинг: {user_data[16]:.1f}\n\n"
    send_message(peer_id, text)

def handle_sysrestart(peer_id, user_id):
    if user_id != OWNER_ID:
        send_message(peer_id, "❌ Только владелец бота!")
        return
    send_message(peer_id, "🔄 Перезагрузка бота...")
    add_suspicious_log(user_id, "sysrestart", "Выполнен перезапуск бота")
    os._exit(0)

def handle_syslinks(peer_id, user_id, args):
    if user_id != OWNER_ID:
        send_message(peer_id, "❌ Только владелец бота!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /syslinks [peer_id]")
        return
    target_peer = int(args[0])
    send_message(peer_id, f"🔗 Ссылка на беседу: https://vk.me/join/AQA... (требуется генерация через API)")

def handle_getbotstats(peer_id, user_id):
    if user_id != OWNER_ID:
        send_message(peer_id, "❌ Только владелец бота!")
        return
    cursor.execute("SELECT COUNT(*) FROM chats WHERE active = 1")
    chats_count = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(messages_count) FROM users")
    total_messages = cursor.fetchone()[0] or 0
    text = f"""📊 *Статистика бота*

💬 Активных чатов: {chats_count}
✍ Всего сообщений: {total_messages}
👥 Пользователей: {cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]}
🕵️ Агентов: {cursor.execute("SELECT COUNT(*) FROM agents").fetchone()[0]}
📋 Репортов: {cursor.execute("SELECT COUNT(*) FROM reports").fetchone()[0]}"""
    send_message(peer_id, text)

def handle_givevip(peer_id, user_id, args):
    if not is_agent(user_id) and user_id != OWNER_ID:
        send_message(peer_id, "❌ Только для агентов и владельца!")
        return
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /givevip [@user] [уровень 1-3] [дней]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    try:
        level = int(args[1])
        days = int(args[2]) if len(args) > 2 else 30
    except:
        send_message(peer_id, "❌ Неверные параметры!")
        return
    if level not in [1, 2, 3]:
        send_message(peer_id, "❌ Уровень VIP должен быть 1, 2 или 3!")
        return
    vip_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users SET vip_level = ?, vip_until = ? WHERE user_id = ?", (level, vip_until, target_id))
    conn.commit()
    send_message(peer_id, f"✅ {get_user_link(target_id)} получил VIP {level} уровень на {days} дней!")

def handle_givemoney(peer_id, user_id, args):
    if not is_agent(user_id) and user_id != OWNER_ID:
        send_message(peer_id, "❌ Только для агентов и владельца!")
        return
    if len(args) < 3:
        send_message(peer_id, "❌ Использование: /givemoney [@user] [euro/dollar/ruble/btc] [сумма]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    currency = args[1].lower()
    if currency not in ['euro', 'dollar', 'ruble', 'btc']:
        send_message(peer_id, "❌ Доступные валюты: euro, dollar, ruble, btc")
        return
    try:
        amount = float(args[2])
    except:
        send_message(peer_id, "❌ Неверная сумма!")
        return
    update_balance(target_id, currency, amount)
    send_message(peer_id, f"✅ {get_user_link(target_id)} получил {amount:.2f} {currency}!")

# ============================================================
# СИСТЕМА РАБОВ
# ============================================================
def handle_slaves(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, """⛓ *Система рабов*

/рабы купить [@user] - купить раба
/рабы выкупить [@раб] - выкупить раба
/рабы выкупитьсебя - выкупить себя
/рабы прокачать [@раб] - прокачать раба
/рабы цепи [@раб] - надеть/снять цепи
/рабы собрать - собрать прибыль
/рабы инфо [@раб] - информация
/рабы список - список рабов""")
        return
    subcmd = args[0].lower()
    if subcmd == "купить":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /рабы купить [@пользователь]")
            return
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        if target_id == user_id:
            send_message(peer_id, "❌ Нельзя купить самого себя!")
            return
        cursor.execute("SELECT * FROM slaves WHERE slave_id = ?", (target_id,))
        if cursor.fetchone():
            send_message(peer_id, "❌ Этот пользователь уже чей-то раб!")
            return
        price = 500
        user_data = get_user_data(user_id)
        if user_data[2] < price:
            send_message(peer_id, f"❌ Недостаточно средств! Нужно {price}€")
            return
        max_slaves = 3 + (user_data[6] * 2) if user_data[6] > 0 else 3
        cursor.execute("SELECT COUNT(*) FROM slaves WHERE owner_id = ?", (user_id,))
        if cursor.fetchone()[0] >= max_slaves:
            send_message(peer_id, f"❌ У вас максимум рабов: {max_slaves}")
            return
        update_balance(user_id, 'euro', -price)
        cursor.execute("INSERT INTO slaves (slave_id, owner_id, level, chains, profit_today, last_collect) VALUES (?, ?, 1, 0, 0, ?)",
                      (target_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        send_message(peer_id, f"⛓ {get_user_link(user_id)} купил раба {get_user_link(target_id)} за {price}€!")
    elif subcmd == "выкупить":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /рабы выкупить [@раб]")
            return
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("SELECT * FROM slaves WHERE slave_id = ? AND owner_id = ?", (target_id, user_id))
        slave = cursor.fetchone()
        if not slave:
            send_message(peer_id, "❌ Этот пользователь не ваш раб!")
            return
        level = slave[3]
        price = 500 + (level - 1) * 200
        user_data = get_user_data(user_id)
        if user_data[2] < price:
            send_message(peer_id, f"❌ Недостаточно средств! Нужно {price}€")
            return
        update_balance(user_id, 'euro', -price)
        cursor.execute("DELETE FROM slaves WHERE slave_id = ?", (target_id,))
        conn.commit()
        send_message(peer_id, f"🎉 {get_user_link(user_id)} выкупил раба {get_user_link(target_id)} за {price}€!")
    elif subcmd == "выкупитьсебя":
        cursor.execute("SELECT * FROM slaves WHERE slave_id = ?", (user_id,))
        slave = cursor.fetchone()
        if not slave:
            send_message(peer_id, "❌ Вы не раб!")
            return
        owner_id = slave[1]
        level = slave[3]
        chains = slave[2]
        if chains == 1:
            send_message(peer_id, "⛓ Вы в цепях и не можете выкупиться!")
            return
        price = 600 + (level - 1) * 250
        user_data = get_user_data(user_id)
        if user_data[2] < price:
            send_message(peer_id, f"❌ Недостаточно средств! Нужно {price}€")
            return
        update_balance(user_id, 'euro', -price)
        update_balance(owner_id, 'euro', price // 2)
        cursor.execute("DELETE FROM slaves WHERE slave_id = ?", (user_id,))
        conn.commit()
        send_message(peer_id, f"🎉 {get_user_link(user_id)} выкупился из рабства за {price}€!")
    elif subcmd == "прокачать":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /рабы прокачать [@раб]")
            return
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("SELECT * FROM slaves WHERE slave_id = ? AND owner_id = ?", (target_id, user_id))
        slave = cursor.fetchone()
        if not slave:
            send_message(peer_id, "❌ Этот пользователь не ваш раб!")
            return
        level = slave[3]
        if level >= 10:
            send_message(peer_id, "❌ Максимальный уровень 10!")
            return
        price = level * 200 + 300
        user_data = get_user_data(user_id)
        if user_data[2] < price:
            send_message(peer_id, f"❌ Недостаточно средств! Нужно {price}€")
            return
        update_balance(user_id, 'euro', -price)
        cursor.execute("UPDATE slaves SET level = level + 1 WHERE slave_id = ?", (target_id,))
        conn.commit()
        send_message(peer_id, f"📈 {get_user_link(user_id)} прокачал раба до {level+1} уровня за {price}€!")
    elif subcmd == "цепи":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /рабы цепи [@раб]")
            return
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("SELECT * FROM slaves WHERE slave_id = ? AND owner_id = ?", (target_id, user_id))
        slave = cursor.fetchone()
        if not slave:
            send_message(peer_id, "❌ Этот пользователь не ваш раб!")
            return
        current_chains = slave[2]
        price = 500
        user_data = get_user_data(user_id)
        if user_data[2] < price:
            send_message(peer_id, f"❌ Недостаточно средств! Нужно {price}€")
            return
        update_balance(user_id, 'euro', -price)
        if current_chains == 0:
            cursor.execute("UPDATE slaves SET chains = 1 WHERE slave_id = ?", (target_id,))
            send_message(peer_id, f"⛓ {get_user_link(user_id)} надел цепи на {get_user_link(target_id)}!")
        else:
            cursor.execute("UPDATE slaves SET chains = 0 WHERE slave_id = ?", (target_id,))
            send_message(peer_id, f"🔓 {get_user_link(user_id)} снял цепи с {get_user_link(target_id)}!")
        conn.commit()
    elif subcmd == "собрать":
        cursor.execute("SELECT * FROM slaves WHERE owner_id = ?", (user_id,))
        slaves = cursor.fetchall()
        if not slaves:
            send_message(peer_id, "❌ У вас нет рабов!")
            return
        total_profit = 0
        for slave in slaves:
            level = slave[3]
            profit = level * 5
            total_profit += profit
        update_balance(user_id, 'euro', total_profit)
        send_message(peer_id, f"💰 {get_user_link(user_id)} собрал {total_profit}€ с {len(slaves)} рабов!")
    elif subcmd == "инфо":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /рабы инфо [@раб]")
            return
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("SELECT * FROM slaves WHERE slave_id = ?", (target_id,))
        slave = cursor.fetchone()
        if not slave:
            send_message(peer_id, "❌ Этот пользователь не раб!")
            return
        chains_text = "🔗 Надеты" if slave[2] == 1 else "🔓 Сняты"
        text = f"""⛓ *Информация о рабе*

👤 Раб: {get_user_link(target_id)}
👑 Владелец: {get_user_link(slave[1])}
📊 Уровень: {slave[3]}
⛓ Цепи: {chains_text}
💰 Прибыль в час: {slave[3] * 5}€"""
        send_message(peer_id, text)
    elif subcmd == "список":
        cursor.execute("SELECT slave_id, level FROM slaves WHERE owner_id = ?", (user_id,))
        slaves = cursor.fetchall()
        if not slaves:
            send_message(peer_id, "❌ У вас нет рабов!")
            return
        text = f"⛓ *Ваши рабы ({len(slaves)}):*\n\n"
        for sid, level in slaves:
            text += f"• {get_user_link(sid)} — Уровень {level}\n"
        send_message(peer_id, text)

# ============================================================
# СИСТЕМА БРАКОВ
# ============================================================
def handle_marriage(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, """💍 *Система браков*

/брак предложить [@user] - предложить брак
/брак принять [id] - принять предложение
/брак развод - развестись
/поцеловать [@user] - поцеловать""")
        return
    subcmd = args[0].lower()
    if subcmd == "предложить":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /брак предложить [@пользователь]")
            return
        target_id = get_user_from_text(args[1])
        if not target_id:
            send_message(peer_id, "❌ Пользователь не найден!")
            return
        cursor.execute("INSERT OR REPLACE INTO marriage_proposals (from_id, to_id, date) VALUES (?, ?, ?)",
                      (user_id, target_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        send_message(peer_id, f"💍 {get_user_link(user_id)} предложил(а) брак {get_user_link(target_id)}!\n/брак принять {user_id}")
    elif subcmd == "принять":
        if len(args) < 2:
            send_message(peer_id, "❌ Использование: /брак принять [id]")
            return
        try:
            proposer_id = int(args[1])
        except:
            send_message(peer_id, "❌ Неверный ID!")
            return
        cursor.execute("SELECT * FROM marriage_proposals WHERE from_id = ? AND to_id = ?", (proposer_id, user_id))
        if not cursor.fetchone():
            send_message(peer_id, "❌ Предложение не найдено!")
            return
        cursor.execute("INSERT INTO marriages (user1_id, user2_id, date) VALUES (?, ?, ?)",
                      (proposer_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        cursor.execute("DELETE FROM marriage_proposals WHERE from_id = ? AND to_id = ?", (proposer_id, user_id))
        conn.commit()
        send_message(peer_id, f"💍💕 Поздравляем! {get_user_link(proposer_id)} и {get_user_link(user_id)} теперь муж и жена!")
    elif subcmd == "развод":
        cursor.execute("DELETE FROM marriages WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        conn.commit()
        send_message(peer_id, f"💔 {get_user_link(user_id)} развёлся/развелась!")

def handle_kiss(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /поцеловать [@пользователь]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    cursor.execute("SELECT * FROM marriages WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
                  (user_id, target_id, target_id, user_id))
    married = cursor.fetchone()
    if married:
        cursor.execute("UPDATE marriages SET love_points = love_points + 1 WHERE id = ?", (married[0],))
        conn.commit()
        send_message(peer_id, f"💋 {get_user_link(user_id)} поцеловал(а) {get_user_link(target_id)}! +1 ❤️")
    else:
        send_message(peer_id, f"💋 {get_user_link(user_id)} поцеловал(а) {get_user_link(target_id)}! 😘")

# ============================================================
# СИСТЕМА РЕПОРТОВ
# ============================================================
def handle_report(peer_id, user_id, args):
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /report [текст жалобы]")
        return
    cursor.execute("SELECT muted_until FROM muted_in_reports WHERE user_id = ?", (user_id,))
    muted = cursor.fetchone()
    if muted and muted[0] and datetime.now() < datetime.strptime(muted[0], "%Y-%m-%d %H:%M:%S"):
        send_message(peer_id, "❌ Вы не можете отправлять репорты до " + muted[0])
        return
    message = " ".join(args)
    cursor.execute("INSERT INTO reports (user_id, peer_id, message, created_date, status) VALUES (?, ?, ?, ?, 'open')",
                  (user_id, peer_id, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    report_id = cursor.lastrowid
    cursor.execute("SELECT user_id FROM agents")
    for agent in cursor.fetchall():
        try:
            send_message(agent[0], f"📋 *Новый репорт #{report_id}*\n\n👤 От: {get_user_link(user_id)}\n💬 Чат: {peer_id}\n📝 {message}\n\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}", keyboard=get_report_keyboard(report_id).get_keyboard())
        except:
            pass
    send_message(peer_id, f"✅ Репорт #{report_id} отправлен!")

def handle_mutereport(peer_id, user_id, args):
    if not is_agent(user_id) and user_id != OWNER_ID:
        send_message(peer_id, "❌ Только для агентов!")
        return
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /mutereport @user [время]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    minutes = parse_time(args[1]) or 60
    until = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO muted_in_reports (user_id, muted_until) VALUES (?, ?)", (target_id, until))
    conn.commit()
    send_message(peer_id, f"🔇 {get_user_link(target_id)} замучен в репортах на {args[1]}")

def handle_unmutereport(peer_id, user_id, args):
    if not is_agent(user_id) and user_id != OWNER_ID:
        send_message(peer_id, "❌ Только для агентов!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /unmutereport @user")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    cursor.execute("DELETE FROM muted_in_reports WHERE user_id = ?", (target_id,))
    conn.commit()
    send_message(peer_id, f"🔊 Мут в репортах снят с {get_user_link(target_id)}")

# ============================================================
# ТОП И СТАФФ
# ============================================================
def handle_top(peer_id, category="messages"):
    if category == "messages":
        cursor.execute("SELECT user_id, messages_count FROM users ORDER BY messages_count DESC LIMIT 10")
    elif category == "commands":
        cursor.execute("SELECT user_id, commands_count FROM users ORDER BY commands_count DESC LIMIT 10")
    elif category == "money":
        cursor.execute("SELECT user_id, balance_euro FROM users ORDER BY balance_euro DESC LIMIT 10")
    else:
        cursor.execute("SELECT user_id, stickers_count FROM users ORDER BY stickers_count DESC LIMIT 10")
    users = cursor.fetchall()
    if not users:
        send_message(peer_id, "❌ Нет данных")
        return
    text = f"📊 *ТОП {category.upper()}*\n\n"
    for i, (uid, count) in enumerate(users, 1):
        text += f"{i}. {get_user_link(uid)} — {count}\n"
    send_message(peer_id, text)

def handle_staff(peer_id):
    try:
        members = vk.messages.getConversationMembers(peer_id=peer_id)
        text = "👮 *Администрация беседы:*\n\n"
        for member in members['items']:
            if member.get('is_owner') or member.get('is_admin'):
                uid = member['member_id']
                role = '👑 Владелец' if member.get('is_owner') else '👮 Администратор'
                text += f"• {get_user_link(uid)} — {role}\n"
        send_message(peer_id, text, keyboard=get_staff_nick_keyboard(peer_id).get_keyboard())
    except Exception as e:
        send_message(peer_id, f"❌ Ошибка: {e}")

def handle_staff_with_nicks(peer_id):
    try:
        members = vk.messages.getConversationMembers(peer_id=peer_id)
        text = "👥 *Администрация с никами:*\n\n"
        for member in members['items']:
            if member.get('is_owner') or member.get('is_admin'):
                uid = member['member_id']
                role = '👑 Владелец' if member.get('is_owner') else '👮 Администратор'
                user_data = get_user_data(uid)
                nick = user_data[1] or get_user_link(uid)
                text += f"• {nick} — {role}\n"
        send_message(peer_id, text)
    except Exception as e:
        send_message(peer_id, f"❌ Ошибка: {e}")

def handle_newrole(peer_id, user_id, args):
    if not has_permission(peer_id, user_id, require_owner=True):
        send_message(peer_id, "❌ Только владелец чата!")
        return
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /newrole [приоритет] [название]")
        return
    try:
        priority = int(args[0])
    except:
        send_message(peer_id, "❌ Приоритет должен быть числом!")
        return
    role_name = " ".join(args[1:])[:32]
    cursor.execute("INSERT OR REPLACE INTO chat_roles (peer_id, role_name, priority) VALUES (?, ?, ?)",
                  (peer_id, role_name, priority))
    conn.commit()
    send_message(peer_id, f"✅ Роль «{role_name}» с приоритетом {priority} создана!")

def handle_delrole(peer_id, user_id, args):
    if not has_permission(peer_id, user_id, require_owner=True):
        send_message(peer_id, "❌ Только владелец чата!")
        return
    if len(args) < 1:
        send_message(peer_id, "❌ Использование: /delrole [название]")
        return
    role_name = " ".join(args)
    cursor.execute("DELETE FROM chat_roles WHERE peer_id = ? AND role_name = ?", (peer_id, role_name))
    conn.commit()
    send_message(peer_id, f"❌ Роль «{role_name}» удалена!")

def handle_sysrole(peer_id, user_id, args):
    if user_id != OWNER_ID:
        send_message(peer_id, "❌ Только системный администратор!")
        return
    if len(args) < 2:
        send_message(peer_id, "❌ Использование: /sysrole [@user] [роль]")
        return
    target_id = get_user_from_text(args[0])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    role = " ".join(args[1:])
    send_message(peer_id, f"✅ {get_user_link(target_id)} получил роль «{role}» от системного администратора!")

def handle_gsysrole(peer_id, user_id, args):
    if user_id != OWNER_ID:
        send_message(peer_id, "❌ Только системный администратор!")
        return
    if len(args) < 3:
        send_message(peer_id, "❌ Использование: /gsysrole [union_id] [@user] [роль]")
        return
    try:
        union_id = int(args[0])
    except:
        send_message(peer_id, "❌ Неверный ID объединения!")
        return
    target_id = get_user_from_text(args[1])
    if not target_id:
        send_message(peer_id, "❌ Пользователь не найден!")
        return
    role = " ".join(args[2:])
    cursor.execute("INSERT OR REPLACE INTO union_roles (union_id, user_id, role_name) VALUES (?, ?, ?)", (union_id, target_id, role))
    conn.commit()
    send_message(peer_id, f"✅ {get_user_link(target_id)} получил роль «{role}» в объединении {union_id}!")

# ============================================================
# ОБРАБОТЧИКИ CALLBACK
# ============================================================
def handle_callback(event):
    try:
        peer_id = event.obj.peer_id
        user_id = event.obj.user_id
        payload = json.loads(event.obj.payload) if isinstance(event.obj.payload, str) else event.obj.payload
        action = payload.get("action")
        
        if action == "buy_vip":
            level = payload.get("level")
            prices = {1: 1000, 2: 5000, 3: 15000}
            user_data = get_user_data(user_id)
            if user_data[2] >= prices[level]:
                update_balance(user_id, 'euro', -prices[level])
                cursor.execute("UPDATE users SET vip_level = ?, vip_until = ? WHERE user_id = ?",
                              (level, (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"), user_id))
                conn.commit()
                send_message(peer_id, f"🎉 {get_user_link(user_id)} купил VIP {level} уровень!")
            else:
                send_message(peer_id, f"❌ Нужно {prices[level]}€")
        
        elif action == "close":
            send_message(peer_id, "❌ Закрыто")
        
        elif action == "admin_warn":
            target_id = payload.get("target_id")
            if has_permission(peer_id, user_id):
                handle_warn(peer_id, user_id, [str(target_id), "Нарушение"])
        
        elif action == "admin_mute":
            target_id = payload.get("target_id")
            if has_permission(peer_id, user_id):
                handle_mute(peer_id, user_id, [str(target_id), "1h", "Нарушение"])
        
        elif action == "admin_kick":
            target_id = payload.get("target_id")
            if has_permission(peer_id, user_id):
                handle_kick(peer_id, user_id, [str(target_id), "Нарушение"])
        
        elif action == "admin_ban":
            target_id = payload.get("target_id")
            if has_permission(peer_id, user_id):
                handle_ban(peer_id, user_id, [str(target_id), "-1", "Нарушение"])
        
        elif action == "admin_unmute":
            target_id = payload.get("target_id")
            if has_permission(peer_id, user_id):
                handle_unmute(peer_id, user_id, [str(target_id)])
        
        elif action == "take_report":
            report_id = payload.get("report_id")
            cursor.execute("UPDATE reports SET status = 'in_progress', agent_id = ? WHERE id = ?", (user_id, report_id))
            conn.commit()
            send_message(peer_id, f"✅ Вы взяли репорт #{report_id}!")
        
        elif action in ["top_messages", "top_stickers", "top_commands", "top_money"]:
            handle_top(peer_id, action.replace("top_", ""))
        
        elif action == "toggle_access":
            target_id = payload.get("target_id")
            command = payload.get("command")
            cursor.execute("SELECT commands_access FROM agents WHERE user_id = ?", (target_id,))
            result = cursor.fetchone()
            current_access = json.loads(result[0]) if result and result[0] else {}
            current_access[command] = not current_access.get(command, False)
            cursor.execute("UPDATE agents SET commands_access = ? WHERE user_id = ?", (json.dumps(current_access), target_id))
            conn.commit()
            text = f"🔐 *Настройка доступов агента* {get_user_link(target_id)}\n\nАгент №{get_agent_number(target_id)}\n\n✅ Доступ {'ВКЛЮЧЕН' if current_access[command] else 'ВЫКЛЮЧЕН'} для {command}"
            send_message(peer_id, text, keyboard=get_agent_access_keyboard(target_id, current_access).get_keyboard())
        
        elif action == "staff_with_nicks":
            handle_staff_with_nicks(peer_id)
        
        elif action == "report_info":
            report_id = payload.get("report_id")
            cursor.execute("SELECT user_id, message, status, created_date FROM reports WHERE id = ?", (report_id,))
            report = cursor.fetchone()
            if report:
                text = f"📋 *Репорт #{report_id}*\n\n👤 От: {get_user_link(report[0])}\n📝 {report[1]}\n📅 {report[3]}\n📊 Статус: {report[2]}"
                send_message(peer_id, text)
        
        try:
            vk.messages.sendMessageEventAnswer(
                event_id=event.obj.event_id,
                user_id=user_id,
                peer_id=peer_id,
                event_data=json.dumps({"type": "show_snackbar", "text": "✅ Готово!"})
            )
        except:
            pass
        
    except Exception as e:
        print(f"Callback ошибка: {e}")
        traceback.print_exc()

# ============================================================
# ОСНОВНОЙ ЦИКЛ
# ============================================================
def main():
    print(f"🤖 Бот запущен! Владелец: {OWNER_ID}")
    
    for event in longpoll.listen():
        try:
            check_temp_bans_and_mutes()
            
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.obj.message
                peer_id = msg['peer_id']
                user_id = msg['from_id']
                text = msg.get('text', '') or ''
                
                if user_id < 0:
                    continue
                
                user_data = get_user_data(user_id)
                if user_data[17] == 3:
                    continue
                
                cursor.execute("SELECT until FROM temp_mutes WHERE user_id = ? AND peer_id = ?", (user_id, peer_id))
                if cursor.fetchone():
                    continue
                
                if re.search(r'vk\.(com|ru)|https?://', text):
                    chat_data = cursor.execute("SELECT links_block FROM chats WHERE peer_id = ?", (peer_id,)).fetchone()
                    if chat_data and chat_data[0] == 1:
                        send_message(peer_id, f"❌ {get_user_link(user_id)}, ссылки запрещены!")
                        continue
                
                if msg.get('payload'):
                    cursor.execute("UPDATE users SET commands_count = commands_count + 1 WHERE user_id = ?", (user_id,))
                elif msg.get('sticker_id'):
                    cursor.execute("UPDATE users SET stickers_count = stickers_count + 1 WHERE user_id = ?", (user_id,))
                else:
                    cursor.execute("UPDATE users SET messages_count = messages_count + 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                
                for prefix in PREFIXES:
                    if text.startswith(prefix):
                        cmd_text = text[len(prefix):].lower().strip()
                        parts = cmd_text.split()
                        if not parts:
                            continue
                        
                        cmd = parts[0]
                        args = parts[1:]
                        
                        # ОСНОВНЫЕ КОМАНДЫ
                        if cmd in ['ban', 'бан']:
                            handle_ban(peer_id, user_id, args)
                        elif cmd in ['kick', 'кик']:
                            handle_kick(peer_id, user_id, args)
                        elif cmd in ['mute', 'мут']:
                            handle_mute(peer_id, user_id, args)
                        elif cmd in ['warn', 'варн']:
                            handle_warn(peer_id, user_id, args)
                        elif cmd in ['unmute', 'снятьмут']:
                            handle_unmute(peer_id, user_id, args)
                        elif cmd in ['stats', 'стата', 'статистика']:
                            handle_stats(peer_id, user_id, args)
                        elif cmd in ['vip', 'вип']:
                            handle_vip(peer_id, user_id)
                        elif cmd in ['balance', 'баланс', 'bal']:
                            handle_balance(peer_id, user_id, args)
                        elif cmd in ['pay', 'перевод']:
                            handle_pay(peer_id, user_id, args)
                        elif cmd in ['course', 'курс']:
                            handle_course(peer_id)
                        elif cmd in ['convert', 'конверт']:
                            handle_convert(peer_id, user_id, args)
                        elif cmd in ['рулетка', 'casino']:
                            handle_roulette(peer_id, user_id, args)
                        elif cmd in ['work', 'работа']:
                            handle_work(peer_id, user_id)
                        elif cmd in ['bonus', 'бонус']:
                            handle_bonus(peer_id, user_id)
                        elif cmd in ['snick', 'сник']:
                            handle_snick(peer_id, user_id, args)
                        elif cmd in ['rnick', 'рник']:
                            handle_rnick(peer_id, user_id)
                        elif cmd in ['nlist', 'списокников']:
                            handle_nlist(peer_id)
                        elif cmd in ['понику', 'findnick']:
                            handle_findnick(peer_id, args)
                        elif cmd in ['ping']:
                            handle_ping(peer_id)
                        elif cmd in ['settings', 'настройки']:
                            handle_settings(peer_id, user_id, args)
                        elif cmd in ['start', 'старт']:
                            handle_start(peer_id, user_id)
                        elif cmd in ['report', 'репорт']:
                            handle_report(peer_id, user_id, args)
                        elif cmd in ['mutereport']:
                            handle_mutereport(peer_id, user_id, args)
                        elif cmd in ['unmutereport']:
                            handle_unmutereport(peer_id, user_id, args)
                        elif cmd in ['agent']:
                            handle_agent(peer_id, user_id, args)
                        elif cmd in ['sysban']:
                            handle_sysban(peer_id, user_id, args)
                        elif cmd in ['unsysban']:
                            handle_unsysban(peer_id, user_id, args)
                        elif cmd in ['sysinfo']:
                            handle_sysinfo(peer_id, user_id, args)
                        elif cmd in ['botadmins']:
                            handle_botadmins(peer_id, user_id)
                        elif cmd in ['sysrestart']:
                            handle_sysrestart(peer_id, user_id)
                        elif cmd in ['syslinks']:
                            handle_syslinks(peer_id, user_id, args)
                        elif cmd in ['getbotstats']:
                            handle_getbotstats(peer_id, user_id)
                        elif cmd in ['givevip']:
                            handle_givevip(peer_id, user_id, args)
                        elif cmd in ['givemoney']:
                            handle_givemoney(peer_id, user_id, args)
                        # ОБЪЕДИНЕНИЯ
                        elif cmd in ['union']:
                            handle_union(peer_id, user_id, args)
                        elif cmd in ['grole']:
                            handle_grole(peer_id, user_id, args)
                        elif cmd in ['gban']:
                            handle_gban(peer_id, user_id, args)
                        elif cmd in ['gkick']:
                            handle_gkick(peer_id, user_id, args)
                        elif cmd in ['gmute']:
                            handle_gmute(peer_id, user_id, args)
                        elif cmd in ['gzov']:
                            handle_gzov(peer_id, user_id, args)
                        elif cmd in ['gnick']:
                            handle_gnick(peer_id, user_id, args)
                        # РАБЫ
                        elif cmd in ['рабы', 'slaves']:
                            handle_slaves(peer_id, user_id, args)
                        # БРАКИ
                        elif cmd in ['брак', 'marriage']:
                            handle_marriage(peer_id, user_id, args)
                        elif cmd in ['поцеловать', 'kiss']:
                            handle_kiss(peer_id, user_id, args)
                        # РОЛИ
                        elif cmd in ['newrole']:
                            handle_newrole(peer_id, user_id, args)
                        elif cmd in ['delrole']:
                            handle_delrole(peer_id, user_id, args)
                        elif cmd in ['sysrole']:
                            handle_sysrole(peer_id, user_id, args)
                        elif cmd in ['gsysrole']:
                            handle_gsysrole(peer_id, user_id, args)
                        # ТОП И СТАФФ
                        elif cmd in ['top', 'топ']:
                            send_message(peer_id, "📊 Выберите категорию:", keyboard=get_top_keyboard().get_keyboard())
                        elif cmd in ['staff', 'админы']:
                            handle_staff(peer_id)
                        elif cmd in ['help', 'помощь']:
                            send_message(peer_id, "📚 *Справка*\n\n/stats - статистика\n/balance - баланс\n/work - работа\n/рулетка - казино\n/report - жалоба\n/рабы - рабы\n/брак - брак\n/vip - VIP\n/top - топы\n/staff - админы")
                        break
                
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                handle_callback(event)
                
            elif event.type == VkBotEventType.GROUP_JOIN:
                peer_id = event.obj.peer_id
                user_id = event.obj.user_id
                cursor.execute("SELECT welcome_message FROM chats WHERE peer_id = ?", (peer_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    send_message(peer_id, result[0].replace("{user}", get_user_link(user_id)))
                    
        except Exception as e:
            print(f"Ошибка: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
