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
        print("🤖 Бот успешно запущен!"
def init_database(self):
        self.conn = sqlite3.connect('vk_bot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
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
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_name TEXT PRIMARY KEY,
                permissions TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_permissions (
                command TEXT PRIMARY KEY,
                required_role TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        
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
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item TEXT,
                quantity INTEGER DEFAULT 1,
                purchased_at TEXT
            )
        ''')
        
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
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_permissions (
                user_id INTEGER PRIMARY KEY,
                permissions TEXT DEFAULT '{}'
            )
        ''')
        
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
    
    def add_balance(self, user_id, currency, amount):
        user = self.get_user(user_id)
        currency_map = {'rub': (7, 'rubles'), 'usd': (8, 'dollars'), 'eur': (9, 'euros'), 'btc': (6, 'bitcoin')}
        if currency in currency_map:
            idx, name = currency_map[currency]
            new_amount = (user[idx] or 0) + amount
            self.cursor.execute(f'UPDATE users SET {name} = ? WHERE user_id = ?', (new_amount, user_id))
            self.conn.commit()
            return True
        return False
    
    def daily_bonus(self, user_id):
        user = self.get_user(user_id)
        if user[15]:
            try:
                last_bonus = datetime.fromisoformat(user[15])
                if datetime.now() - last_bonus < timedelta(days=1):
                    return False, "🎁 Бонус можно получить раз в 24 часа!"
            except:
                pass
        bonus = random.randint(*self.config['bonus_reward'])
        self.add_balance(user_id, 'rub', bonus)
        self.cursor.execute('UPDATE users SET last_bonus = ? WHERE user_id = ?', (datetime.now().isoformat(), user_id))
        self.conn.commit()
        return True, f"🎉 Вы получили бонус: {bonus} ₽"
    
    def mine_bitcoin(self, user_id):
        user = self.get_user(user_id)
        miners_count = user[30] or 0
        if miners_count == 0:
            return False, "❌ У вас нет майнеров! Купите их в магазине: /shop"
        if user[14]:
            try:
                last_mine = datetime.fromisoformat(user[14])
                if datetime.now() - last_mine < timedelta(hours=1):
                    return False, "⛏️ Майнинг доступен раз в час!"
            except:
                pass
        reward = random.uniform(*self.config['mine_reward']) * miners_count
        self.add_balance(user_id, 'btc', reward)
        self.cursor.execute('UPDATE users SET mine_cooldown = ? WHERE user_id = ?', (datetime.now().isoformat(), user_id))
        self.conn.commit()
        return True, f"⛏️ Вы намайнили {reward:.8f} BTC (Майнеров: {miners_count})"
    
    def work(self, user_id):
        user = self.get_user(user_id)
        if user[13]:
            try:
                last_work = datetime.fromisoformat(user[13])
                if datetime.now() - last_work < timedelta(minutes=30):
                    return False, "💼 Работа доступна раз в 30 минут!"
            except:
                pass
        reward = random.randint(*self.config['work_reward'])
        self.add_balance(user_id, 'rub', reward)
        self.cursor.execute('UPDATE users SET work_cooldown = ? WHERE user_id = ?', (datetime.now().isoformat(), user_id))
        self.conn.commit()
        return True, f"💼 Вы заработали {reward} ₽"
    
    def buy_vip(self, user_id, level=1):
        user = self.get_user(user_id)
        price = self.shop_items[f'vip{level}']['price']
        if user[7] >= price:
            self.cursor.execute('UPDATE users SET rubles = rubles - ? WHERE user_id = ?', (price, user_id))
            vip_until = (datetime.now() + timedelta(days=30)).isoformat()
            self.cursor.execute('UPDATE users SET vip_level = ?, vip_until = ?, role = ? WHERE user_id = ?', (level, vip_until, f'vip{level}', user_id))
            self.conn.commit()
            return True, f"✅ Поздравляем! Вы приобрели VIP {level} уровня на 30 дней!"
        return False, f"❌ Недостаточно средств! Нужно {price} ₽"
    
    def buy_miner(self, user_id):
        user = self.get_user(user_id)
        price = self.shop_items['bitcoin_miner']['price']
        if user[8] >= price:
            self.cursor.execute('UPDATE users SET dollars = dollars - ? WHERE user_id = ?', (price, user_id))
            self.cursor.execute('UPDATE users SET miners_count = miners_count + 1 WHERE user_id = ?', (user_id,))
            self.conn.commit()
            return True, f"✅ Вы купили майнер за {price}$! Теперь у вас {user[30] + 1} майнер(ов)."
        return False, f"❌ Недостаточно средств! Нужно {price}$"
    
    def buy_item(self, user_id, item_name, price=None):
        user = self.get_user(user_id)
        if price is None:
            for category in self.inline_shop.values():
                if item_name in category:
                    price = category[item_name]
                    break
        if price is None:
            return False, "❌ Товар не найден!"
        if user[8] >= price:
            self.cursor.execute('UPDATE users SET dollars = dollars - ? WHERE user_id = ?', (price, user_id))
            self.cursor.execute('INSERT INTO inventory (user_id, item, quantity, purchased_at) VALUES (?, ?, 1, ?)', (user_id, item_name, datetime.now().isoformat()))
            self.conn.commit()
            return True, f"✅ Вы купили {item_name} за {price}$!"
        return False, f"❌ Недостаточно средств! Нужно {price}$"
    
    def transfer_money(self, user_id, target_id, currency, amount):
        user = self.get_user(user_id)
        target = self.get_user(target_id)
        currency_map = {'rub': (7, 'rubles'), 'usd': (8, 'dollars'), 'eur': (9, 'euros'), 'btc': (6, 'bitcoin')}
        if currency not in currency_map:
            return False, "❌ Неверная валюта!"
        idx, name = currency_map[currency]
        if user[idx] < amount:
            return False, "❌ Недостаточно средств!"
        self.cursor.execute(f'UPDATE users SET {name} = {name} - ? WHERE user_id = ?', (amount, user_id))
        self.cursor.execute(f'UPDATE users SET {name} = {name} + ? WHERE user_id = ?', (amount, target_id))
        self.conn.commit()
        return True, f"✅ Переведено {amount} {currency.upper()} пользователю {self.get_user_link(target_id)}"
    
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
    
    def add_warn(self, user_id, admin_id, chat_id, reason=None):
        user = self.get_user(user_id)
        warns = user[10] + 1
        self.cursor.execute('UPDATE users SET warns = ? WHERE user_id = ?', (warns, user_id))
        self.conn.commit()
        admin_name = self.get_user_link(admin_id) if admin_id != 0 else "Система"
        self.send_message(f"⚠️ Пользователю {self.get_user_link(user_id)} выдан варн ({warns}/{self.config['warning_limit']}) от {admin_name}", chat_id)
        if reason:
            self.send_message(f"📝 Причина: {reason}", chat_id)
        if warns >= self.config['warning_limit']:
            self.mute_user(user_id, admin_id, chat_id, 30)
            self.cursor.execute('UPDATE users SET warns = 0 WHERE user_id = ?', (user_id,))
            self.conn.commit()
def is_agent(self, user_id):
        self.cursor.execute('SELECT is_agent FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result and result[0] == 1
    
    def get_agent_number(self, user_id):
        self.cursor.execute('SELECT agent_number FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def has_agent_permission(self, user_id, permission):
        if not self.is_agent(user_id):
            return False
        if self.is_super_admin(user_id):
            return True
        self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        if result:
            perms = json.loads(result[0])
            return perms.get(permission, False)
        return permission == 'reports'
    
    def can_manage_agents(self, user_id):
        if self.is_super_admin(user_id):
            return True
        return self.has_agent_permission(user_id, 'agent')
    
    def get_all_agents(self):
        self.cursor.execute('SELECT user_id, name, agent_number, tickets_processed, avg_rating FROM users WHERE is_agent = 1 ORDER BY agent_number ASC')
        return self.cursor.fetchall()
    
    def add_report(self, user_id, reporter_id, message, chat_id=None):
        current_time = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO reports (user_id, reporter_id, message, chat_id, created_at) VALUES (?, ?, ?, ?, ?)',
                           (user_id, reporter_id, message, chat_id or 0, current_time))
        self.conn.commit()
        report_id = self.cursor.lastrowid
        self.notify_agents(report_id, user_id, message, chat_id)
        return True, f"✅ Репорт #{report_id} отправлен!"
    
    def notify_agents(self, report_id, user_id, message, chat_id):
        self.cursor.execute('SELECT user_id FROM users WHERE is_agent = 1 AND reports_muted = 0')
        agents = self.cursor.fetchall()
        report_text = f"📝 **Новый репорт #{report_id}**\n👤 От пользователя: {self.get_user_link(user_id)}\n💬 Сообщение: {message[:200]}\n💬 Беседа: {chat_id}"
        for agent in agents:
            self.send_message(report_text, user_id=agent[0])
    
    def get_bot_admins(self, admin_id):
        if not self.is_agent(admin_id):
            return "❌ Вы не являетесь агентом!"
        agents = self.get_all_agents()
        if not agents:
            return "📋 Список агентов пуст."
        info = "👑 **Список агентов поддержки**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for agent_id, name, agent_number, tickets, rating in agents:
            info += f"**#{agent_number}** | {self.get_user_link(agent_id)}\n📊 Тикетов: {tickets} | Рейтинг: {rating:.1f}⭐\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        return info
    
    def activate_chat(self, chat_id, user_id):
        try:
            self.cursor.execute('SELECT is_active FROM chats WHERE chat_id = ?', (chat_id,))
            result = self.cursor.fetchone()
            if result and result[0] == 1:
                self.send_message("❌ Беседа уже активирована!", chat_id)
                return False, "❌ Беседа уже активирована!"
            current_time = datetime.now().isoformat()
            self.cursor.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
            chat = self.cursor.fetchone()
            if chat:
                self.cursor.execute('UPDATE chats SET is_active = 1, activated_at = ?, owner_id = ? WHERE chat_id = ?', (current_time, user_id, chat_id))
            else:
                self.cursor.execute('INSERT INTO chats (chat_id, chat_name, owner_id, is_active, activated_at, created_at, settings) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                   (chat_id, f"Chat_{chat_id}", user_id, 1, current_time, current_time, json.dumps(self.default_chat_settings)))
            self.cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', ('Владелец', user_id))
            self.conn.commit()
            welcome_msg = f"✅ **Беседа активирована!**\n👑 Владелец беседы: {self.get_user_link(user_id)}\n🎉 Удачного использования бота!\n\n📋 **Список команд:** /help\n⚙️ **Настройки чата:** /settings\n❓ **Вопросы по боту:** /report"
            self.send_message(welcome_msg, chat_id)
            return True, "✅ Беседа успешно активирована!"
        except Exception as e:
            print(f"❌ Ошибка активации: {e}")
            self.send_message(f"❌ Ошибка активации: {str(e)[:100]}", chat_id)
            return False, f"❌ Ошибка активации: {str(e)[:100]}"
    
    def get_user_stats_detailed(self, user_id, chat_id=None):
        user = self.get_user(user_id)
        stats = f"🔍 Информация о пользователе:\n━━━━━━━━━━━━━━━━━━━━━━\n"
        stats += f"👤 Статус: {user[2]}\n⚠ Предупреждений: {user[10]}/{self.config['warning_limit']}\n📄 Никнейм: {user[24] or user[1]}\n"
        stats += f"🚧 Блокировка чата: {'✅ Да' if user[11]==1 else '❌ Нет'}\n"
        stats += f"📅 Дата появления: {user[16][:16] if user[16] else 'Неизвестно'}\n\n"
        stats += f"📋 Глобальная информация:\n"
        if user[3] > 0:
            stats += f"💎 VIP статус: VIP {user[3]} уровня\n"
        stats += f"✍ Сообщений отправлено: {user[17]}\n⛏️ Майнеров: {user[30] or 0}\n⚙ ID: {user_id}\n"
        return stats
def handle_message(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            chat_id = None
            if message.get('peer_id', 0) > 2000000000:
                chat_id = message['peer_id'] - 2000000000
            else:
                return
            
            if chat_id:
                self.get_or_create_chat(chat_id)
            
            if 'text' in message:
                text = message['text'].lower()
                user_id = message['from_id']
                
                if text in self.commands['start']:
                    self.activate_chat(chat_id, user_id)
                    return
                
                self.cursor.execute('SELECT is_active FROM chats WHERE chat_id = ?', (chat_id,))
                result = self.cursor.fetchone()
                if not result or result[0] == 0:
                    if text not in self.commands['start']:
                        self.send_message("❌ Беседа не активирована! Введите /start", chat_id)
                    return
                
                if text in self.commands['ping']:
                    start_time = time.time()
                    response_time = (time.time() - start_time) * 1000
                    self.send_message(f"🏓 Понг! {response_time:.2f} мс", chat_id)
                    return
                
                if text in self.commands['help']:
                    self.send_message("📖 **Список команд:**\nhttps://vk.com/@your_article", chat_id)
                    return
                
                if text in self.commands['stats']:
                    self.send_message(self.get_user_stats_detailed(user_id, chat_id), chat_id)
                    return
                
                if text in self.commands['balance']:
                    user = self.get_user(user_id)
                    self.send_message(f"💰 Баланс:\n🇷🇺 Рубли: {user[7]:.2f} ₽\n🇺🇸 Доллары: {user[8]:.2f} $\n🇪🇺 Евро: {user[9]:.2f} €\n₿ Биткойны: {user[6]:.8f} BTC", chat_id)
                    return
                
                if text in self.commands['bonus']:
                    success, msg = self.daily_bonus(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['mine']:
                    success, msg = self.mine_bitcoin(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['work']:
                    success, msg = self.work(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['shop']:
                    self.send_message("🛒 Магазин: /buy [vip1/vip2/vip3/miner]", chat_id)
                    return
                
                if text in self.commands['buy']:
                    parts = text.split()
                    if len(parts) >= 2:
                        if parts[1] == 'miner':
                            success, msg = self.buy_miner(user_id)
                            self.send_message(msg, chat_id)
                        elif parts[1] in ['vip1', 'vip2', 'vip3']:
                            level = int(parts[1][3])
                            success, msg = self.buy_vip(user_id, level)
                            self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['staff']:
                    staff = self.get_staff_list()
                    if staff:
                        staff_text = "👥 **Персонал:**\n━━━━━━━━━━━━━━━━━━\n"
                        for member in staff:
                            staff_text += f"👤 {self.get_user_link(member['id'])} - {member['role']}\n"
                        self.send_message(staff_text, chat_id)
                    else:
                        self.send_message("👥 Персонал отсутствует.", chat_id)
                    return
                
                if text in self.commands['botadmins']:
                    self.send_message(self.get_bot_admins(user_id), chat_id)
                    return
                
                if text in self.commands['report']:
                    parts = text.split(maxsplit=1)
                    if len(parts) > 1:
                        success, msg = self.add_report(user_id, user_id, parts[1], chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ /report [текст]", chat_id)
                    return
                
                if text in self.commands['union']:
                    msg = ("🏢 **Объединения:**\n/union_create [название]\n/union_join [код]\n/union_leave\n/union_info\n/union_invite\n/union_ban [user]\n/union_mute [user] [мин]\n/union_kick [user]\n/union_role [user] [роль]")
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_create']:
                    parts = text.split(maxsplit=1)
                    if len(parts) < 2:
                        self.send_message("❌ /union_create [название]", chat_id)
                        return
                    success, msg = self.create_union(user_id, parts[1])
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_join']:
                    parts = text.split()
                    if len(parts) < 2:
                        self.send_message("❌ /union_join [код]", chat_id)
                        return
                    success, msg = self.join_union(user_id, parts[1])
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_leave']:
                    success, msg = self.leave_union(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_info']:
                    info = self.get_union_info(user_id)
                    self.send_message(info, chat_id)
                    return
                
                if text in self.commands['union_invite']:
                    success, msg = self.generate_union_invite(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_ban']:
                    parts = text.split(maxsplit=2)
                    if len(parts) < 2:
                        self.send_message("❌ /union_ban [пользователь] [причина]", chat_id)
                        return
                    target_id = self.extract_user_id(parts[1])
                    if not target_id:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                        return
                    reason = parts[2] if len(parts) > 2 else None
                    success, msg = self.union_ban(user_id, target_id, reason)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_mute']:
                    parts = text.split()
                    if len(parts) < 3:
                        self.send_message("❌ /union_mute [пользователь] [минуты]", chat_id)
                        return
                    target_id = self.extract_user_id(parts[1])
                    if not target_id:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                        return
                    try:
                        minutes = int(parts[2])
                    except:
                        self.send_message("❌ Минуты - число!", chat_id)
                        return
                    reason = ' '.join(parts[3:]) if len(parts) > 3 else None
                    success, msg = self.union_mute(user_id, target_id, minutes, reason)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_kick']:
                    parts = text.split(maxsplit=2)
                    if len(parts) < 2:
                        self.send_message("❌ /union_kick [пользователь] [причина]", chat_id)
                        return
                    target_id = self.extract_user_id(parts[1])
                    if not target_id:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                        return
                    reason = parts[2] if len(parts) > 2 else None
                    success, msg = self.union_kick(user_id, target_id, reason)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['union_role']:
                    parts = text.split()
                    if len(parts) < 3:
                        self.send_message("❌ /union_role [пользователь] [роль]", chat_id)
                        return
                    target_id = self.extract_user_id(parts[1])
                    if not target_id:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                        return
                    role = parts[2]
                    success, msg = self.union_role(user_id, target_id, role)
                    self.send_message(msg, chat_id)
                    return
    
    def get_staff_list(self):
        staff_roles = ['Модератор', 'Администратор', 'Владелец']
        staff_list = []
        for role in staff_roles:
            self.cursor.execute('SELECT user_id, name FROM users WHERE role = ?', (role,))
            for user_id, name in self.cursor.fetchall():
                staff_list.append({'id': user_id, 'name': name, 'role': role})
        return staff_list
    
    def run(self):
        print("🤖 Бот начал работу. Ожидание сообщений...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for event in self.longpoll.listen():
            try:
                self.handle_message(event)
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    GROUP_TOKEN = os.getenv("VK_TOKEN")
    GROUP_ID = os.getenv("VK_GROUP_ID")
    
    if not GROUP_TOKEN or not GROUP_ID:
        print("❌ Ошибка: переменные окружения не заданы!")
        exit(1)
    
    GROUP_ID = int(GROUP_ID)
    print(f"✅ Запуск с ID группы: {GROUP_ID}")
    
    bot = VKChatManager(GROUP_TOKEN, GROUP_ID)
    bot.run()
