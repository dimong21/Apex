import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import random
import time
import threading
import re
from datetime import datetime, timedelta
import json
import os
import secrets
import string

class VKChatManager:
    def __init__(self, group_token, group_id):
        self.group_token = group_token
        self.group_id = group_id
        self.vk = vk_api.VkApi(token=group_token)
        self.longpoll = VkBotLongPoll(self.vk, group_id)
        self.vk_api = self.vk.get_api()
        
        self.super_admins = [771565937]
        
        self.exchange_rates = {
            'usd_to_rub': 90.0,
            'eur_to_rub': 98.0,
            'btc_to_usd': 60000,
            'btc_to_rub': 5400000,
        }
        
        self.default_chat_settings = {
            'kick_on_leave': False,
            'who_can_add': 'all',
            'games_enabled': True,
            'welcome_message': True,
            'anti_flood': False,
            'max_messages_per_second': 5
        }
        
        self.init_database()
        self.config = self.load_config()
        self.load_exchange_rates()
        
        self.prefixes = ['/', '!', '.']
        
        self.waiting_for_agent_id = {}
        self.waiting_for_agent_expiry = {}
        self.waiting_for_syslinks = {}
        self.sysinfo_target = {}
        self.waiting_for_union_id = {}
        self.waiting_for_wipe_user = None
        self.waiting_for_newrole = {}
        self.waiting_for_report_answer = {}
        self.pending_reports = {}
        
        # Словарь команд
        self.commands = {
            'ban': ['/ban', '/бан', '!ban', '!бан'],
            'unban': ['/unban', '/разбан', '!unban', '!разбан'],
            'mute': ['/mute', '/мут', '!mute', '!мут'],
            'unmute': ['/unmute', '/размут', '!unmute', '!размут'],
            'warn': ['/warn', '/варн', '!warn', '!варн'],
            'kick': ['/kick', '/кик', '!kick', '!кик'],
            'ping': ['/ping', '/пинг', '!ping', '!пинг'],
            'stats': ['/stats', '/статистика', '!stats', '!статистика'],
            'balance': ['/balance', '/баланс', '!balance', '!баланс'],
            'bonus': ['/bonus', '/бонус', '!bonus', '!бонус'],
            'transfer': ['/transfer', '/перевод', '!transfer', '!перевод'],
            'mine': ['/mine', '/майнинг', '!mine', '!майнинг'],
            'work': ['/work', '/работа', '!work', '!работа'],
            'shop': ['/shop', '/магазин', '!shop', '!магазин'],
            'buy': ['/buy', '/купить', '!buy', '!купить'],
            'vip': ['/vip', '/вип', '!vip', '!вип'],
            'staff': ['/staff', '/персонал', '!staff', '!персонал'],
            'say': ['/say', '/скажи', '!say', '!скажи'],
            'start': ['/start', '/старт', '!start', '!старт'],
            'help': ['/help', '/помощь', '!help', '!помощь'],
            'report': ['/report', '/репорт', '!report', '!репорт'],
            'slaves': ['/slaves', '/рабы', '!slaves', '!рабы'],
            'rates': ['/rates', '/курсы', '!rates', '!курсы'],
            'settings': ['/settings', '/настройки', '!settings', '!настройки'],
            'roleslist': ['/roleslist', '/списокролей', '!roleslist', '!списокролей'],
            'setrole': ['/setrole', '/выдатьроль', '!setrole', '!выдатьроль'],
            'addrole': ['/addrole', '/добавитьроль', '!addrole', '!добавитьроль'],
            'newrole': ['/newrole', '/новаяроль', '!newrole', '!новаяроль'],
            'filter': ['/filter', '/фильтр', '!filter', '!фильтр'],
            'invite': ['/invite', '/пригласить', '!invite', '!пригласить'],
            'chat_info': ['/chatinfo', '/инфобеседы', '!chatinfo', '!инфобеседы'],
            'agent': ['/agent', '/агент', '!agent', '!агент'],
            'reports': ['/reports', '/репорты', '!reports', '!репорты'],
            'botadmins': ['/botadmins', '/ботадмины', '!botadmins', '!ботадмины'],
            'mutereports': ['/mutereports', '/мутрепорты', '!mutereports', '!мутрепорты'],
            'unmutereports': ['/unmutereports', '/размутрепорты', '!unmutereports', '!размутрепорты'],
            'givemoney': ['/givemoney', '/выдатьденьги', '!givemoney', '!выдатьденьги'],
            'givevip': ['/givevip', '/выдатьвип', '!givevip', '!выдатьвип'],
            'sysban': ['/sysban', '/системныйбан', '!sysban', '!системныйбан'],
            'sysunban': ['/sysunban', '/системныйразбан', '!sysunban', '!системныйразбан'],
            'sysrole': ['/sysrole', '/системнаяроль', '!sysrole', '!системнаяроль'],
            'sysinfo': ['/sysinfo', '/системнаяинформация', '!sysinfo', '!системнаяинформация'],
            'snick': ['/snick', '/сетник', '!snick', '!сетник'],
            'rnick': ['/rnick', '/делник', '!rnick', '!делник'],
            'delkick': ['/delkick', '/делкик', '!delkick', '!делкик'],
            'nonames': ['/nonames', '/безников', '!nonames', '!безников'],
            'ponicku': ['/ponicku', '/понику', '!ponicku', '!понику'],
            'bhelp': ['/bhelp', '/бхелп', '!bhelp', '!бхелп'],
            'sysrestart': ['/sysrestart', '/системныйрестарт', '!sysrestart', '!системныйрестарт'],
            'syslinks': ['/syslinks', '/ссылки', '!syslinks', '!ссылки'],
            'logs': ['/logs', '/логи', '!logs', '!логи'],
            'wipe': ['/wipe', '/вайп', '!wipe', '!вайп'],
            'wipeuser': ['/wipeuser', '/вайпюзера', '!wipeuser', '!вайпюзера'],
            'editcmd': ['/editcmd', '/редактироватькоманду', '!editcmd', '!редактироватькоманду'],
            'setrate': ['/setrate', '/установитькурс', '!setrate', '!установитькурс'],
            'probivtiket': ['/probivtiket', '/пробивтикет', '!probivtiket', '!пробивтикет'],
            'sysadmin': ['/sysadmin', '/системныйадмин', '!sysadmin', '!системныйадмин'],
            'union': ['/union', '/объединение', '!union', '!объединение'],
            'union_create': ['/union_create', '/создатьобъединение'],
            'union_join': ['/union_join', '/вступитьвобъединение'],
            'union_leave': ['/union_leave', '/выйтизобъединения'],
            'union_info': ['/union_info', '/инфообъединения'],
            'union_invite': ['/union_invite', '/кодобъединения'],
            'union_ban': ['/union_ban', '/объединениебан'],
            'union_mute': ['/union_mute', '/объединениемут'],
            'union_kick': ['/union_kick', '/объединениекик'],
            'union_role': ['/union_role', '/объединениероль'],
        }
        
        self.shop_items = {
            'vip1': {'name': '🌟 VIP I уровня', 'price': 5000, 'type': 'vip', 'level': 1,
                     'benefits': {'max_chats': 50, 'max_unions': 30, 'daily_say': 50}},
            'vip2': {'name': '💎 VIP II уровня', 'price': 15000, 'type': 'vip', 'level': 2,
                     'benefits': {'max_chats': 120, 'max_unions': 70, 'daily_say': 120}},
            'vip3': {'name': '👑 VIP III уровня', 'price': 35000, 'type': 'vip', 'level': 3,
                     'benefits': {'max_chats': 250, 'max_unions': 150, 'daily_say': 300}},
            'bitcoin_miner': {'name': '⛏️ Майнер биткойнов', 'price': 5000, 'type': 'item', 'value': 'miner', 'hourly': 0.5},
        }
        
        self.inline_shop = {
            'phones': {'iPhone 15 Pro': 999, 'iPhone 15 Pro Max': 1199, 'Samsung Galaxy S24 Ultra': 1299,
                       'Samsung Galaxy S24': 899, 'Google Pixel 8 Pro': 999, 'Google Pixel 8': 699,
                       'Xiaomi 14 Ultra': 899, 'Xiaomi 14 Pro': 699, 'OnePlus 12': 749, 'Nothing Phone 2': 599},
            'houses': {'🏠 Квартира-студия': 50000, '🏡 1-комнатная квартира': 100000, '🏘️ 2-комнатная квартира': 200000,
                       '🏠 Загородный дом': 500000, '🏢 Пентхаус': 1000000, '🏰 Особняк': 5000000, '🏝️ Вилла на острове': 10000000},
            'clothes': {'👕 Футболка': 50, '👖 Джинсы': 100, '👔 Костюм': 500, '👟 Кроссовки': 150,
                        '🧥 Пальто': 300, '🧢 Кепка': 30, '🧣 Шарф': 40, '🧤 Перчатки': 35,
                        '👗 Платье': 250, '👘 Халат': 80},
            'items': {'💍 Кольцо': 200, '⌚ Часы': 500, '💎 Бриллиант': 1000, '🎮 Игровая приставка': 400,
                      '📚 Книга': 30, '💻 Ноутбук': 800, '📱 Смартфон': 600, '🎧 Наушники': 100,
                      '📷 Фотоаппарат': 450, '🚗 Машина': 5000}
        }
        
        self.status_emojis = {'user': '👤', 'moderator': '🛡️', 'admin': '⚡', 'owner': '👑'}
        self.suspicious_logs = []
        print("🤖 Бот успешно запущен!")
    
    def init_database(self):
        self.conn = sqlite3.connect('vk_bot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                role TEXT DEFAULT 'Пользователь',
                vip_level INTEGER DEFAULT 0,
                vip_until TEXT,
                balance REAL DEFAULT 0,
                bitcoin REAL DEFAULT 0,
                rubles REAL DEFAULT 0,
                dollars REAL DEFAULT 0,
                euros REAL DEFAULT 0,
                warns INTEGER DEFAULT 0,
                is_muted INTEGER DEFAULT 0,
                mute_until TEXT,
                work_cooldown TEXT,
                mine_cooldown TEXT,
                last_bonus TEXT,
                join_date TEXT,
                messages_count INTEGER DEFAULT 0,
                say_used_today INTEGER DEFAULT 0,
                last_say_reset TEXT,
                is_agent INTEGER DEFAULT 0,
                agent_number INTEGER DEFAULT 0,
                tickets_processed INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0,
                reports_muted INTEGER DEFAULT 0,
                nickname TEXT DEFAULT '',
                sysban_level INTEGER DEFAULT 0,
                sysban_by INTEGER DEFAULT 0,
                sysban_reason TEXT DEFAULT '',
                sysban_date TEXT DEFAULT '',
                miners_count INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица бесед
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                chat_name TEXT,
                creator_id INTEGER DEFAULT 0,
                owner_id INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 0,
                activated_at TEXT,
                created_at TEXT,
                settings TEXT DEFAULT '{}'
            )
        ''')
        
        # Таблица объединений
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                name TEXT,
                invite_code TEXT UNIQUE,
                created_at TEXT,
                settings TEXT DEFAULT '{}'
            )
        ''')
        
        # Таблица участников объединений
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS union_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                union_id INTEGER,
                chat_id INTEGER,
                added_by INTEGER,
                added_at TEXT,
                FOREIGN KEY (union_id) REFERENCES unions (id)
            )
        ''')
        
        # Таблица приглашений в объединения
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS union_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                union_id INTEGER,
                code TEXT UNIQUE,
                created_by INTEGER,
                expires_at TEXT,
                max_uses INTEGER DEFAULT 1,
                uses INTEGER DEFAULT 0,
                FOREIGN KEY (union_id) REFERENCES unions (id)
            )
        ''')
        
        # Таблица приглашений
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                inviter_id INTEGER,
                invited_at TEXT,
                FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (inviter_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица для ролей и прав
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_name TEXT PRIMARY KEY,
                permissions TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица для команды с приоритетами
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_permissions (
                command TEXT PRIMARY KEY,
                required_role TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица для фильтров слов по беседам
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                word TEXT,
                action TEXT DEFAULT 'warn',
                added_by INTEGER,
                added_at TEXT,
                UNIQUE(chat_id, word)
            )
        ''')
        
        # Таблица для инвентаря
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item TEXT,
                quantity INTEGER DEFAULT 1,
                purchased_at TEXT
            )
        ''')
        
        # Таблица для логов действий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                action TEXT,
                target_id INTEGER,
                reason TEXT,
                created_at TEXT
            )
        ''')
        
        # Таблица для прав агентов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_permissions (
                user_id INTEGER PRIMARY KEY,
                permissions TEXT DEFAULT '{}'
            )
        ''')
        
        # Таблица для репортов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reporter_id INTEGER,
                message TEXT,
                chat_id INTEGER,
                status TEXT DEFAULT 'open',
                created_at TEXT,
                closed_at TEXT,
                closed_by INTEGER,
                rating INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица для рабов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS slaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                slave_id INTEGER,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                chains INTEGER DEFAULT 0,
                last_collect TEXT,
                bought_at TEXT,
                UNIQUE(owner_id, slave_id)
            )
        ''')
        
        # Добавление базовых ролей
        default_roles = [
            ('Пользователь', '{}', 0),
            ('Модератор', '{"ban": true, "mute": true, "warn": true, "kick": true, "filter": true}', 40),
            ('Администратор', '{"ban": true, "mute": true, "warn": true, "kick": true, "setrole": true, "filter": true, "addrole": true}', 50),
            ('Владелец', '{"*": true}', 100)
        ]
        
        for role in default_roles:
            self.cursor.execute('INSERT OR IGNORE INTO roles (role_name, permissions, priority) VALUES (?, ?, ?)', role)
        
        self.conn.commit()
    
    def load_config(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            default_config = {
                'chat_id': 0, 'mute_time': 5, 'warning_limit': 3,
                'work_reward': [50, 200], 'mine_reward': [0.1, 0.5], 'bonus_reward': [100, 500],
                'filter_action': 'warn',
                'vip_benefits': {
                    1: {'max_chats': 50, 'max_unions': 30, 'daily_say': 50},
                    2: {'max_chats': 120, 'max_unions': 70, 'daily_say': 120},
                    3: {'max_chats': 250, 'max_unions': 150, 'daily_say': 300}
                }
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            return default_config
    
    def load_exchange_rates(self):
        try:
            with open('exchange_rates.json', 'r', encoding='utf-8') as f:
                saved_rates = json.load(f)
                self.exchange_rates.update(saved_rates)
        except:
            self.save_exchange_rates()
    
    def save_exchange_rates(self):
        try:
            with open('exchange_rates.json', 'w', encoding='utf-8') as f:
                json.dump(self.exchange_rates, f, ensure_ascii=False, indent=4)
        except:
            pass
    
    def generate_invite_code(self, length=8):
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # ========== МЕТОДЫ ОБЪЕДИНЕНИЙ ==========
    
    def create_union(self, user_id, name):
        user = self.get_user(user_id)
        self.cursor.execute('SELECT id FROM unions WHERE owner_id = ?', (user_id,))
        if self.cursor.fetchone():
            return False, "❌ У вас уже есть объединение!"
        
        invite_code = self.generate_invite_code()
        current_time = datetime.now().isoformat()
        
        self.cursor.execute('''
            INSERT INTO unions (owner_id, name, invite_code, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, invite_code, current_time))
        self.conn.commit()
        union_id = self.cursor.lastrowid
        
        self.cursor.execute('''
            INSERT INTO union_invites (union_id, code, created_by, expires_at, max_uses)
            VALUES (?, ?, ?, ?, ?)
        ''', (union_id, invite_code, user_id, (datetime.now() + timedelta(days=30)).isoformat(), 100))
        self.conn.commit()
        
        return True, f"✅ Объединение **{name}** создано!\n🔑 Код: `{invite_code}`"
    
    def join_union(self, user_id, invite_code):
        self.cursor.execute('''
            SELECT u.id, u.name, u.owner_id, ui.expires_at, ui.max_uses, ui.uses
            FROM unions u
            JOIN union_invites ui ON u.id = ui.union_id
            WHERE ui.code = ? AND ui.expires_at > ?
        ''', (invite_code, datetime.now().isoformat()))
        union = self.cursor.fetchone()
        if not union:
            return False, "❌ Неверный или просроченный код!"
        
        union_id, union_name, owner_id, expires_at, max_uses, uses = union
        if uses >= max_uses:
            return False, "❌ Код использован максимальное количество раз!"
        
        self.cursor.execute('SELECT id FROM union_members WHERE union_id = ? AND chat_id = ?', (union_id, user_id))
        if self.cursor.fetchone():
            return False, "❌ Беседа уже в объединении!"
        
        current_time = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO union_members (union_id, chat_id, added_by, added_at) VALUES (?, ?, ?, ?)',
                           (union_id, user_id, owner_id, current_time))
        self.cursor.execute('UPDATE union_invites SET uses = uses + 1 WHERE code = ?', (invite_code,))
        self.conn.commit()
        return True, f"✅ Беседа присоединилась к **{union_name}**!"
    
    def leave_union(self, user_id):
        self.cursor.execute('''
            SELECT u.id, u.name, u.owner_id FROM unions u
            JOIN union_members um ON u.id = um.union_id
            WHERE um.chat_id = ?
        ''', (user_id,))
        union = self.cursor.fetchone()
        if not union:
            return False, "❌ Беседа не в объединении!"
        
        union_id, union_name, owner_id = union
        if owner_id == user_id:
            self.cursor.execute('DELETE FROM union_members WHERE union_id = ?', (union_id,))
            self.cursor.execute('DELETE FROM union_invites WHERE union_id = ?', (union_id,))
            self.cursor.execute('DELETE FROM unions WHERE id = ?', (union_id,))
            self.conn.commit()
            return True, f"✅ Объединение **{union_name}** удалено!"
        else:
            self.cursor.execute('DELETE FROM union_members WHERE union_id = ? AND chat_id = ?', (union_id, user_id))
            self.conn.commit()
            return True, f"✅ Беседа покинула **{union_name}**!"
    
    def get_union_info(self, user_id):
        self.cursor.execute('''
            SELECT u.id, u.name, u.owner_id, u.created_at, u.invite_code, COUNT(um.id) as members_count
            FROM unions u
            LEFT JOIN union_members um ON u.id = um.union_id
            WHERE um.chat_id = ?
            GROUP BY u.id
        ''', (user_id,))
        union = self.cursor.fetchone()
        if not union:
            return "❌ Беседа не в объединении!"
        
        union_id, name, owner_id, created_at, invite_code, members_count = union
        info = f"🏢 **Объединение: {name}**\n━━━━━━━━━━━━━━━━━━━━━━\n"
        info += f"👑 Владелец: {self.get_user_link(owner_id)}\n📅 Создано: {created_at[:16]}\n"
        info += f"👥 Бесед: {members_count}\n🔑 Код: `{invite_code}`\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        self.cursor.execute('SELECT um.chat_id, um.added_at FROM union_members um WHERE um.union_id = ?', (union_id,))
        members = self.cursor.fetchall()
        if members:
            info += "📋 **Беседы в объединении:**\n"
            for chat_id, added_at in members:
                info += f"├─ Беседа {chat_id} - добавлена {added_at[:16]}\n"
        return info
    
    def generate_union_invite(self, user_id):
        self.cursor.execute('SELECT id, name FROM unions WHERE owner_id = ?', (user_id,))
        union = self.cursor.fetchone()
        if not union:
            return False, "❌ У вас нет объединения!"
        
        union_id, name = union
        new_code = self.generate_invite_code()
        self.cursor.execute('''
            INSERT INTO union_invites (union_id, code, created_by, expires_at, max_uses)
            VALUES (?, ?, ?, ?, ?)
        ''', (union_id, new_code, user_id, (datetime.now() + timedelta(days=30)).isoformat(), 100))
        self.conn.commit()
        return True, f"✅ Новый код: `{new_code}`"
    
    def union_ban(self, admin_id, target_id, reason=None):
        self.cursor.execute('''
            SELECT u.id, u.name FROM unions u
            JOIN union_members um ON u.id = um.union_id
            WHERE u.owner_id = ?
        ''', (admin_id,))
        union = self.cursor.fetchone()
        if not union:
            return False, "❌ Вы не владелец объединения!"
        
        union_id, name = union
        self.cursor.execute('SELECT chat_id FROM union_members WHERE union_id = ?', (union_id,))
        chats = self.cursor.fetchall()
        results = []
        for chat in chats:
            try:
                self.ban_user(target_id, admin_id, chat[0], reason)
                results.append(f"Беседа {chat[0]}: ✅")
            except:
                results.append(f"Беседа {chat[0]}: ❌")
        success_count = len([r for r in results if '✅' in r])
        return True, f"✅ Бан выполнен в {success_count}/{len(chats)} беседах"
    
    def union_mute(self, admin_id, target_id, minutes, reason=None):
        self.cursor.execute('''
            SELECT u.id, u.name FROM unions u
            JOIN union_members um ON u.id = um.union_id
            WHERE u.owner_id = ?
        ''', (admin_id,))
        union = self.cursor.fetchone()
        if not union:
            return False, "❌ Вы не владелец объединения!"
        
        union_id, name = union
        self.cursor.execute('SELECT chat_id FROM union_members WHERE union_id = ?', (union_id,))
        chats = self.cursor.fetchall()
        results = []
        for chat in chats:
            try:
                self.mute_user(target_id, admin_id, chat[0], minutes)
                results.append(f"Беседа {chat[0]}: ✅")
            except:
                results.append(f"Беседа {chat[0]}: ❌")
        success_count = len([r for r in results if '✅' in r])
        return True, f"✅ Мут выполнен в {success_count}/{len(chats)} беседах"
    
    def union_kick(self, admin_id, target_id, reason=None):
        self.cursor.execute('''
            SELECT u.id, u.name FROM unions u
            JOIN union_members um ON u.id = um.union_id
            WHERE u.owner_id = ?
        ''', (admin_id,))
        union = self.cursor.fetchone()
        if not union:
            return False, "❌ Вы не владелец объединения!"
        
        union_id, name = union
        self.cursor.execute('SELECT chat_id FROM union_members WHERE union_id = ?', (union_id,))
        chats = self.cursor.fetchall()
        results = []
        for chat in chats:
            try:
                self.kick_user(admin_id, target_id, chat[0], reason)
                results.append(f"Беседа {chat[0]}: ✅")
            except:
                results.append(f"Беседа {chat[0]}: ❌")
        success_count = len([r for r in results if '✅' in r])
        return True, f"✅ Кик выполнен в {success_count}/{len(chats)} беседах"
    
    def union_role(self, admin_id, target_id, role, reason=None):
        self.cursor.execute('''
            SELECT u.id, u.name FROM unions u
            JOIN union_members um ON u.id = um.union_id
            WHERE u.owner_id = ?
        ''', (admin_id,))
        union = self.cursor.fetchone()
        if not union:
            return False, "❌ Вы не владелец объединения!"
        
        union_id, name = union
        self.cursor.execute('SELECT chat_id FROM union_members WHERE union_id = ?', (union_id,))
        chats = self.cursor.fetchall()
        results = []
        for chat in chats:
            try:
                self.sysrole_user(admin_id, target_id, role, chat[0])
                results.append(f"Беседа {chat[0]}: ✅")
            except:
                results.append(f"Беседа {chat[0]}: ❌")
        success_count = len([r for r in results if '✅' in r])
        return True, f"✅ Роль выдана в {success_count}/{len(chats)} беседах"
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def is_super_admin(self, user_id):
        return user_id in self.super_admins
    
    def get_user_link(self, user_id):
        user = self.get_user(user_id)
        nickname = user[24] or user[1]
        return f"[id{user_id}|{nickname}]"
    
    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = self.cursor.fetchone()
        if not user:
            try:
                user_info = self.vk_api.users.get(user_ids=user_id)[0]
                name = f"{user_info['first_name']} {user_info['last_name']}"
            except:
                name = f"User_{user_id}"
            current_time = datetime.now().isoformat()
            self.cursor.execute('INSERT INTO users (user_id, name, join_date, messages_count, say_used_today, last_say_reset, miners_count) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (user_id, name, current_time, 0, 0, current_time, 0))
            self.conn.commit()
            return self.get_user(user_id)
        return user
    
    def send_message(self, message, chat_id=None, user_id=None, keyboard=None):
        try:
            params = {'random_id': random.randint(1, 1000000), 'message': message}
            if user_id:
                params['user_id'] = user_id
            elif chat_id:
                params['chat_id'] = chat_id
            if keyboard:
                params['keyboard'] = keyboard
            self.vk_api.messages.send(**params)
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False
    
    def get_or_create_chat(self, chat_id):
        self.cursor.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
        chat = self.cursor.fetchone()
        if not chat:
            try:
                current_time = datetime.now().isoformat()
                self.cursor.execute('INSERT INTO chats (chat_id, chat_name, owner_id, is_active, created_at, settings) VALUES (?, ?, ?, ?, ?, ?)',
                                   (chat_id, f"Chat_{chat_id}", 0, 0, current_time, json.dumps(self.default_chat_settings)))
                self.conn.commit()
            except Exception as e:
                print(f"⚠️ Ошибка создания беседы: {e}")
            return self.get_or_create_chat(chat_id)
        return chat
    
    def extract_user_id(self, text, reply_message=None):
        if reply_message and reply_message.get('from_id'):
            return reply_message['from_id']
        match = re.search(r'\[id(\d+)[^\]]*\]', text)
        if match:
            return int(match.group(1))
        match = re.search(r'@id(\d+)', text)
        if match:
            return int(match.group(1))
        match = re.search(r'id(\d+)', text)
        if match:
            return int(match.group(1))
        match = re.search(r'vk\.(com|ru)/id(\d+)', text)
        if match:
            return int(match.group(2))
        words = text.split()
        for word in words:
            if word.isdigit():
                return int(word)
        return None
    
    # ========== МЕТОДЫ МОДЕРАЦИИ ==========
    
    def ban_user(self, user_id, admin_id, chat_id, reason=None):
        try:
            self.vk_api.messages.removeChatUser(chat_id=chat_id, user_id=user_id)
            self.cursor.execute('UPDATE users SET role = "banned" WHERE user_id = ?', (user_id,))
            self.conn.commit()
            msg = f"⛔ Пользователь {self.get_user_link(user_id)} забанен администратором {self.get_user_link(admin_id)}"
            if reason:
                msg += f"\n📝 Причина: {reason}"
            self.send_message(msg, chat_id)
            return True
        except Exception as e:
            print(f"Ошибка бана: {e}")
            return False
    
    def mute_user(self, user_id, admin_id, chat_id, minutes=None):
        if not minutes:
            minutes = 5
        mute_until = datetime.now() + timedelta(minutes=minutes)
        self.cursor.execute('UPDATE users SET is_muted = 1, mute_until = ? WHERE user_id = ?', (mute_until.isoformat(), user_id))
        self.conn.commit()
        self.send_message(f"🔇 Пользователю {self.get_user_link(user_id)} выдан мут на {minutes} минут от {self.get_user_link(admin_id)}", chat_id)
        threading.Timer(minutes * 60, self.unmute_user, args=[user_id]).start()
    
    def unmute_user(self, user_id):
        self.cursor.execute('UPDATE users SET is_muted = 0, mute_until = NULL WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def kick_user(self, admin_id, user_id, chat_id, reason=None):
        try:
            self.vk_api.messages.removeChatUser(chat_id=chat_id, user_id=user_id)
            msg = f"🚪 Пользователь {self.get_user_link(user_id)} кикнут администратором {self.get_user_link(admin_id)}"
            if reason:
                msg += f"\n📝 Причина: {reason}"
            self.send_message(msg, chat_id)
            return True
        except Exception as e:
            print(f"Ошибка кика: {e}")
            return False
    
    def sysrole_user(self, admin_id, user_id, role, chat_id):
        try:
            self.vk_api.messages.editChat(chat_id=chat_id, member_id=user_id, role=role)
            return True, f"✅ Пользователю {self.get_user_link(user_id)} выдана роль {role} в беседе!"
        except Exception as e:
            return False, f"❌ Ошибка выдачи роли: {str(e)}"
    
    # ========== ЗАПУСК БОТА ==========
    
    def run(self):
        print("🤖 Бот начал работу. Ожидание сообщений...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("💡 Бот готов к работе!")
        print("💬 Добавьте бота в беседу и введите /start")
        
        for event in self.longpoll.listen():
            try:
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.handle_message(event)
                elif event.type == VkBotEventType.MESSAGE_EVENT:
                    self.handle_callback_query(event)
            except Exception as e:
                print(f"❌ Ошибка обработки события: {e}")
                import traceback
                traceback.print_exc()
    
    def handle_message(self, event):
        # Этот метод должен быть полностью реализован
        # Включите сюда всю логику обработки команд
        pass
    
    def handle_callback_query(self, event):
        # Обработка нажатий на кнопки
        pass


if __name__ == "__main__":
    GROUP_TOKEN = os.getenv("VK_TOKEN")
    GROUP_ID = os.getenv("VK_GROUP_ID")
    
    if not GROUP_TOKEN or not GROUP_ID:
        print("❌ Ошибка: переменные окружения не заданы!")
        print("💡 Добавьте VK_TOKEN и VK_GROUP_ID в настройках Bothost")
        exit(1)
    
    GROUP_ID = int(GROUP_ID)
    print(f"✅ Бот запускается с ID группы: {GROUP_ID}")
    
    bot = VKChatManager(GROUP_TOKEN, GROUP_ID)
    bot.run()
