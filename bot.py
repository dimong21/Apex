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
        print("🤖 Бот успешно запущен!")
    
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
        self.cursor.execute('SELECT id FROM unions WHERE owner_id = ?', (user_id,))
        if self.cursor.fetchone():
            return False, "❌ У вас уже есть объединение!"
        invite_code = self.generate_invite_code()
        current_time = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO unions (owner_id, name, invite_code, created_at) VALUES (?, ?, ?, ?)',
                           (user_id, name, invite_code, current_time))
        self.conn.commit()
        union_id = self.cursor.lastrowid
        self.cursor.execute('INSERT INTO union_invites (union_id, code, created_by, expires_at, max_uses) VALUES (?, ?, ?, ?, ?)',
                           (union_id, invite_code, user_id, (datetime.now() + timedelta(days=30)).isoformat(), 100))
        self.conn.commit()
        return True, f"✅ Объединение **{name}** создано!\n🔑 Код: `{invite_code}`"
    
    def join_union(self, user_id, invite_code):
        self.cursor.execute('''
            SELECT u.id, u.name, u.owner_id, ui.expires_at, ui.max_uses, ui.uses
            FROM unions u JOIN union_invites ui ON u.id = ui.union_id
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
            FROM unions u LEFT JOIN union_members um ON u.id = um.union_id
            WHERE um.chat_id = ? GROUP BY u.id
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
        self.cursor.execute('INSERT INTO union_invites (union_id, code, created_by, expires_at, max_uses) VALUES (?, ?, ?, ?, ?)',
                           (union_id, new_code, user_id, (datetime.now() + timedelta(days=30)).isoformat(), 100))
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
    
    def union_role(self, admin_id, target_id, role):
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
            self.cursor.execute('UPDATE users SET vip_level = ?, vip_until = ?, role = ? WHERE user_id = ?',
                               (level, vip_until, f'vip{level}', user_id))
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
            self.cursor.execute('INSERT INTO inventory (user_id, item, quantity, purchased_at) VALUES (?, ?, 1, ?)',
                               (user_id, item_name, datetime.now().isoformat()))
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
            minutes = self.config['mute_time']
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
                self.cursor.execute('UPDATE chats SET is_active = 1, activated_at = ?, owner_id = ? WHERE chat_id = ?',
                                   (current_time, user_id, chat_id))
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
        if user[11] == 1 and user[12]:
            try:
                mute_until = datetime.fromisoformat(user[12])
                if mute_until > datetime.now():
                    stats += f"🚧 Блокировка чата: до {mute_until.strftime('%d.%m.%Y %H:%M')}\n"
                else:
                    stats += f"🚧 Блокировка чата: нет\n"
            except:
                stats += f"🚧 Блокировка чата: нет\n"
        else:
            stats += f"🚧 Блокировка чата: нет\n"
        if user[16]:
            try:
                join_date = datetime.fromisoformat(user[16])
                stats += f"📅 Дата появления: {join_date.strftime('%d.%m.%Y %H:%M')}\n\n"
            except:
                stats += f"📅 Дата появления: Неизвестно\n\n"
        else:
            stats += f"📅 Дата появления: Неизвестно\n\n"
        stats += f"📋 Глобальная информация:\n"
        if user[3] > 0:
            stats += f"💎 VIP статус: VIP {user[3]} уровня\n"
            if user[4]:
                try:
                    vip_until = datetime.fromisoformat(user[4])
                    stats += f"💎 Действует до: {vip_until.strftime('%d.%m.%Y %H:%M')}\n"
                except:
                    pass
        stats += f"✍ Сообщений отправлено: {user[17]}\n⛏️ Майнеров: {user[30] or 0}\n⚙ ID: {user_id}\n"
        return stats
    
    def get_staff_list(self):
        staff_roles = ['Модератор', 'Администратор', 'Владелец']
        staff_list = []
        for role in staff_roles:
            self.cursor.execute('SELECT user_id, name FROM users WHERE role = ?', (role,))
            for user_id, name in self.cursor.fetchall():
                staff_list.append({'id': user_id, 'name': name, 'role': role})
        return staff_list
    
    def get_roles_list(self):
        self.cursor.execute('SELECT role_name, priority FROM roles ORDER BY priority DESC')
        return self.cursor.fetchall()
    
    def add_custom_role(self, admin_id, role_name, priority):
        if not self.has_command_access(admin_id, 'addrole'):
            return False, "❌ У вас нет прав для создания ролей!"
        try:
            self.cursor.execute('INSERT INTO roles (role_name, permissions, priority) VALUES (?, ?, ?)',
                               (role_name, json.dumps({}), int(priority)))
            self.conn.commit()
            self.status_emojis[role_name] = '👤'
            return True, f"✅ Роль '{role_name}' создана! Приоритет: {priority}"
        except sqlite3.IntegrityError:
            return False, f"❌ Роль '{role_name}' уже существует!"
    
    def new_role(self, admin_id, priority, role_name):
        if not self.has_command_access(admin_id, 'addrole'):
            return False, "❌ У вас нет прав для создания/изменения ролей!"
        try:
            priority = int(priority)
            if priority < 0 or priority > 100:
                return False, "❌ Приоритет должен быть от 0 до 100!"
            self.cursor.execute('SELECT role_name FROM roles WHERE role_name = ?', (role_name,))
            if self.cursor.fetchone():
                self.cursor.execute('UPDATE roles SET priority = ? WHERE role_name = ?', (priority, role_name))
                self.conn.commit()
                return True, f"✅ Роль '{role_name}' обновлена! Приоритет: {priority}"
            else:
                self.cursor.execute('INSERT INTO roles (role_name, permissions, priority) VALUES (?, ?, ?)',
                                   (role_name, json.dumps({}), priority))
                self.conn.commit()
                self.status_emojis[role_name] = '👤'
                return True, f"✅ Роль '{role_name}' создана! Приоритет: {priority}"
        except ValueError:
            return False, "❌ Приоритет должен быть числом!"
    
    def set_user_role(self, admin_id, user_id, role, chat_id):
        if not self.has_command_access(admin_id, 'setrole'):
            return False, "❌ У вас нет прав для выдачи ролей!"
        self.cursor.execute('SELECT * FROM roles WHERE role_name = ?', (role,))
        if not self.cursor.fetchone():
            return False, f"❌ Роли '{role}' не существует! Доступные роли: /roleslist"
        self.cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
        self.conn.commit()
        return True, f"✅ Пользователю {self.get_user_link(user_id)} выдана роль {role}"
    
    def check_permission(self, user_id, command):
        user = self.get_user(user_id)
        role = user[2]
        self.cursor.execute('SELECT required_role, priority FROM command_permissions WHERE command = ?', (command,))
        cmd_config = self.cursor.fetchone()
        if cmd_config:
            required_role = cmd_config[0]
            required_priority = cmd_config[1]
        else:
            mod_commands = ['ban', 'mute', 'warn', 'kick', 'setrole', 'filter', 'addrole']
            if command in mod_commands:
                required_role = 'Модератор'
                required_priority = 40
            else:
                required_role = 'Пользователь'
                required_priority = 0
        self.cursor.execute('SELECT priority FROM roles WHERE role_name = ?', (role,))
        user_priority = self.cursor.fetchone()
        if not user_priority:
            return False
        return user_priority[0] >= required_priority
    
    def has_command_access(self, user_id, command, chat_id=None):
        if self.is_super_admin(user_id):
            return True
        return self.check_permission(user_id, command)
    
    def get_exchange_rates_info(self):
        return (f"💱 **Текущие курсы валют:**\n━━━━━━━━━━━━━━━━━━━━━━\n🇺🇸 1 USD = {self.exchange_rates['usd_to_rub']:.2f} RUB\n"
                f"🇪🇺 1 EUR = {self.exchange_rates['eur_to_rub']:.2f} RUB\n₿ 1 BTC = {self.exchange_rates['btc_to_usd']:.0f} USD\n"
                f"₿ 1 BTC = {self.exchange_rates['btc_to_rub']:.0f} RUB")
    
    def set_exchange_rate(self, admin_id, currency, rate):
        if not self.is_agent(admin_id):
            return False, "❌ Вы не являетесь агентом!"
        if currency == 'usd':
            self.exchange_rates['usd_to_rub'] = float(rate)
            self.exchange_rates['btc_to_rub'] = self.exchange_rates['btc_to_usd'] * float(rate)
        elif currency == 'eur':
            self.exchange_rates['eur_to_rub'] = float(rate)
        elif currency == 'btc_usd':
            self.exchange_rates['btc_to_usd'] = float(rate)
            self.exchange_rates['btc_to_rub'] = float(rate) * self.exchange_rates['usd_to_rub']
        elif currency == 'btc_rub':
            self.exchange_rates['btc_to_rub'] = float(rate)
            self.exchange_rates['btc_to_usd'] = float(rate) / self.exchange_rates['usd_to_rub']
        else:
            return False, "❌ Неверная валюта!"
        self.save_exchange_rates()
        self.log_action(admin_id, 'set_rate', 0, f"{currency} = {rate}")
        return True, f"✅ Курс {currency} установлен: {rate}"
    
    def get_role_display_name(self, role_name):
        self.cursor.execute('SELECT role_name FROM roles WHERE role_name = ?', (role_name,))
        role = self.cursor.fetchone()
        if role:
            return role[0]
        default_names = {'user': 'Пользователь', 'moderator': 'Модератор', 'admin': 'Администратор', 'owner': 'Владелец'}
        return default_names.get(role_name, role_name)
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
    
    def add_agent(self, admin_id, user_id):
        if not self.can_manage_agents(admin_id):
            return False, "❌ У вас нет прав для добавления агентов!"
        if self.is_agent(user_id):
            return False, "❌ Пользователь уже является агентом!"
        self.cursor.execute('SELECT MAX(agent_number) FROM users WHERE is_agent = 1')
        result = self.cursor.fetchone()
        next_number = (result[0] or 0) + 1
        self.cursor.execute('UPDATE users SET is_agent = 1, agent_number = ?, tickets_processed = 0, avg_rating = 0, reports_muted = 0 WHERE user_id = ?', (next_number, user_id))
        self.cursor.execute('INSERT OR IGNORE INTO agent_permissions (user_id, permissions) VALUES (?, ?)', (user_id, json.dumps({
            'reports': True, 'agent': False, 'givemoney': False, 'givevip': False, 'sysban': False, 'sysrole': False,
            'sysinfo': False, 'botadmins': False, 'snick': False, 'rnick': False, 'delkick': False,
            'mutereports': False, 'unmutereports': False, 'bhelp': False, 'sysrestart': False,
            'syslinks': False, 'logs': False
        })))
        self.conn.commit()
        self.log_action(admin_id, 'add_agent', user_id, f"Добавлен агент #{next_number}")
        return True, f"✅ Агент #{next_number} добавлен!"
    
    def del_agent(self, admin_id, user_id):
        if not self.can_manage_agents(admin_id):
            return False, "❌ У вас нет прав для удаления агентов!"
        if not self.is_agent(user_id):
            return False, "❌ Пользователь не является агентом!"
        self.cursor.execute('UPDATE users SET is_agent = 0, agent_number = 0 WHERE user_id = ?', (user_id,))
        self.cursor.execute('DELETE FROM agent_permissions WHERE user_id = ?', (user_id,))
        self.conn.commit()
        self.log_action(admin_id, 'del_agent', user_id, "Удален агент")
        return True, f"✅ Агент удален!"
    
    def update_agent_permissions(self, admin_id, target_id, permission, value):
        if not self.can_manage_agents(admin_id):
            return False, "❌ У вас нет прав для изменения прав агентов!"
        if not self.is_agent(target_id):
            return False, "❌ Пользователь не является агентом!"
        self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (target_id,))
        result = self.cursor.fetchone()
        perms = json.loads(result[0]) if result else {}
        perms[permission] = value
        self.cursor.execute('INSERT OR REPLACE INTO agent_permissions (user_id, permissions) VALUES (?, ?)', (target_id, json.dumps(perms)))
        self.conn.commit()
        status = "включен" if value else "отключен"
        return True, f"✅ Доступ к {permission} {status} для агента #{self.get_agent_number(target_id)}!"
    
    def get_all_agents(self):
        self.cursor.execute('SELECT user_id, name, agent_number, tickets_processed, avg_rating FROM users WHERE is_agent = 1 ORDER BY agent_number ASC')
        return self.cursor.fetchall()
    
    def get_bot_admins(self, admin_id):
        if not self.is_agent(admin_id):
            return "❌ Вы не являетесь агентом!"
        agents = self.get_all_agents()
        if not agents:
            return "📋 Список агентов пуст."
        info = "👑 **Список агентов поддержки**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for agent_id, name, agent_number, tickets, rating in agents:
            self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (agent_id,))
            result = self.cursor.fetchone()
            perms = json.loads(result[0]) if result else {}
            rank = "🏆 Элитный" if tickets >= 100 else "⭐ Опытный" if tickets >= 50 else "📈 Развивающийся" if tickets >= 20 else "🆕 Новичок"
            info += f"**#{agent_number}** {rank}\n👤 {self.get_user_link(agent_id)}\n📊 Тикетов: {tickets} | Рейтинг: {rating:.1f}⭐\n"
            has_reports = "📝" if perms.get('reports', False) else "🔇"
            has_sysban = "🔨" if perms.get('sysban', False) else "⚙️"
            has_givemoney = "💰" if perms.get('givemoney', False) else "💵"
            info += f"Права: {has_reports} {has_sysban} {has_givemoney}\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        return info
    
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
    
    def get_report_info(self, report_id):
        self.cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
        report = self.cursor.fetchone()
        if not report:
            return "❌ Репорт не найден!"
        info = (f"📋 **Репорт #{report[0]}**\n━━━━━━━━━━━━━━━━━━━━━━\n👤 Пользователь: {self.get_user_link(report[1])}\n"
                f"📝 Репорт от: {self.get_user_link(report[2])}\n💬 Сообщение: {report[3]}\n📅 Создан: {report[5]}\n🔘 Статус: {'✅ Открыт' if report[6] == 'open' else '❌ Закрыт'}\n")
        if report[6] == 'closed':
            info += f"🔒 Закрыт: {report[7]}\n👨‍💼 Кем: {self.get_user_link(report[8])}\n⭐ Оценка: {report[9]}/5\n"
        if report[4] and report[4] != 0:
            info += f"💬 Беседа: {report[4]}\n"
        return info
    
    def close_report(self, agent_id, report_id, user_id, rating=5):
        if not self.is_agent(agent_id):
            return False, "❌ Вы не являетесь агентом!"
        self.cursor.execute('SELECT * FROM reports WHERE id = ? AND status = "open"', (report_id,))
        report = self.cursor.fetchone()
        if not report:
            return False, "❌ Репорт не найден или уже закрыт!"
        current_time = datetime.now().isoformat()
        self.cursor.execute('UPDATE reports SET status = "closed", closed_at = ?, closed_by = ?, rating = ? WHERE id = ?',
                           (current_time, agent_id, rating, report_id))
        self.cursor.execute('UPDATE users SET tickets_processed = tickets_processed + 1, avg_rating = (avg_rating * tickets_processed + ?) / (tickets_processed + 1) WHERE user_id = ?', (rating, agent_id))
        self.conn.commit()
        self.log_action(agent_id, 'close_report', report[1], f"Репорт #{report_id}, оценка {rating}")
        return True, f"✅ Репорт #{report_id} закрыт!"
    
    def set_rating(self, user_id, report_id, rating):
        self.cursor.execute('SELECT status FROM reports WHERE id = ?', (report_id,))
        report = self.cursor.fetchone()
        if not report:
            return False, "❌ Репорт не найден!"
        if report[0] != 'closed':
            return False, "❌ Репорт еще не закрыт!"
        self.cursor.execute('UPDATE reports SET rating = ? WHERE id = ?', (rating, report_id))
        self.conn.commit()
        return True, f"✅ Спасибо за оценку {rating}/5 ⭐!"
    
    def handle_reports_in_dm(self, user_id, text):
        if not self.is_agent(user_id):
            self.send_message("❌ У вас нет доступа к этой команде!", user_id=user_id)
            return
        parts = text.lower().split()
        if len(parts) >= 2:
            if parts[1] == 'list':
                self.cursor.execute('SELECT * FROM reports WHERE status = "open" ORDER BY created_at DESC')
                reports = self.cursor.fetchall()
                if reports:
                    msg = "📋 **Открытые репорты:**\n━━━━━━━━━━━━━━━━━━\n"
                    for r in reports[:10]:
                        msg += f"**#{r[0]}** | от {self.get_user_link(r[1])}\n💬 {r[3][:50]}...\n📅 {r[5][:16]}\n➡️ /reports close {r[0]} [оценка]\n━━━━━━━━━━━━━━━━━━\n"
                    if len(reports) > 10:
                        msg += f"\n... и еще {len(reports)-10} репортов"
                    self.send_message(msg, user_id=user_id)
                else:
                    self.send_message("✅ Нет открытых репортов!", user_id=user_id)
            elif parts[1] == 'close' and len(parts) >= 3:
                try:
                    report_id = int(parts[2])
                    rating = int(parts[3]) if len(parts) > 3 else 5
                    rating = max(1, min(5, rating))
                    success, msg = self.close_report(user_id, report_id, 0, rating)
                    self.send_message(msg, user_id=user_id)
                except ValueError:
                    self.send_message("❌ Использование: /reports close [id] [оценка 1-5]", user_id=user_id)
            elif parts[1] == 'info' and len(parts) >= 3:
                try:
                    report_id = int(parts[2])
                    info = self.get_report_info(report_id)
                    self.send_message(info, user_id=user_id)
                except ValueError:
                    self.send_message("❌ Использование: /reports info [id]", user_id=user_id)
            elif parts[1] == 'stats':
                stats = self.get_agent_stats(user_id)
                self.send_message(stats, user_id=user_id)
        else:
            self.send_message("📋 **Система репортов**\n━━━━━━━━━━━━━━━━━━━━━━\nДоступные команды:\n\n• /reports list - Список открытых репортов\n• /reports close [id] [оценка] - Закрыть репорт\n• /reports info [id] - Информация о репорте\n• /reports stats - Моя статистика\n\nОценка: 1-5 ⭐ (по умолчанию 5)", user_id=user_id)
    
    def get_agent_stats(self, agent_id):
        user = self.get_user(agent_id)
        self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (agent_id,))
        result = self.cursor.fetchone()
        perms = json.loads(result[0]) if result else {}
        self.cursor.execute('SELECT COUNT(*) FROM reports WHERE closed_by = ?', (agent_id,))
        closed_by_me = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT AVG(rating) FROM reports WHERE closed_by = ? AND rating > 0', (agent_id,))
        my_avg_rating = self.cursor.fetchone()[0] or 0
        self.cursor.execute('SELECT COUNT(*) FROM reports WHERE status = "open"')
        open_reports = self.cursor.fetchone()[0]
        stats = (f"👑 **Статистика агента #{user[21]}**\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Всего обработано: {user[22]}\n⭐ Средний рейтинг: {user[23]:.1f}/5\n"
                 f"🔧 Закрыто мной: {closed_by_me}\n🎯 Мой средний рейтинг: {my_avg_rating:.1f}/5\n📋 Открытых репортов: {open_reports}\n\n🔐 **Мои права:**\n")
        perm_names = {'reports': 'Доступ к репортам', 'agent': 'Управление агентами', 'givemoney': 'Выдача денег',
                     'givevip': 'Выдача VIP', 'sysban': 'Системный бан', 'sysrole': 'Системная роль',
                     'sysinfo': 'Системная информация', 'botadmins': 'Список агентов', 'bhelp': 'Скрытые команды',
                     'sysrestart': 'Рестарт бота', 'syslinks': 'Ссылки на беседы', 'logs': 'Подозрительные логи'}
        for perm_key, perm_name in perm_names.items():
            stats += f"{'✅' if perms.get(perm_key, False) else '❌'} {perm_name}\n"
        return stats
    
    def log_action(self, user_id, action, target_id=None, reason=None):
        current_time = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO logs (chat_id, user_id, action, target_id, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                           (0, user_id, action, target_id, reason, current_time))
        self.conn.commit()
        suspicious_actions = ['sysban', 'sysunban', 'sysrole', 'givemoney', 'givevip', 'add_agent', 'del_agent', 'set_rate', 'wipe']
        if action in suspicious_actions:
            self.suspicious_logs.append({'time': current_time, 'user': user_id, 'action': action, 'target': target_id, 'reason': reason})
            self.save_suspicious_logs()
    
    def save_suspicious_logs(self):
        try:
            with open('suspicious_logs.json', 'w', encoding='utf-8') as f:
                json.dump(self.suspicious_logs[-100:], f, ensure_ascii=False, indent=4)
        except:
            pass
    def sysban_user(self, admin_id, user_id, level, reason=None):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return False, "❌ У вас нет доступа к команде /sysban!"
        level = int(level)
        if level not in [1, 2, 3, 4]:
            return False, "❌ Неверная стадия бана! Доступны: 1, 2, 3, 4"
        current_time = datetime.now().isoformat()
        if level == 4:
            self.cursor.execute('UPDATE users SET role = "Пользователь", vip_level = 0, bitcoin = 0, rubles = 0, dollars = 0, euros = 0, is_agent = 0, agent_number = 0, nickname = "", sysban_level = ? WHERE user_id = ?', (level, user_id))
            self.cursor.execute('DELETE FROM agent_permissions WHERE user_id = ?', (user_id,))
        elif level == 3:
            self.cursor.execute('UPDATE users SET bitcoin = 0, rubles = 0, dollars = 0, euros = 0, sysban_level = ? WHERE user_id = ?', (level, user_id))
        else:
            self.cursor.execute('UPDATE users SET sysban_level = ?, sysban_by = ?, sysban_reason = ?, sysban_date = ? WHERE user_id = ?', (level, admin_id, reason or "Не указана", current_time, user_id))
        self.conn.commit()
        self.log_action(admin_id, 'sysban', user_id, f"Стадия {level}: {reason}")
        level_names = {1: "1️⃣ Полный ЧС бота", 2: "2️⃣ Запрет доступа к командам", 3: "3️⃣ Слив денег", 4: "4️⃣ Анулировать аккаунт"}
        return True, f"✅ Пользователь {self.get_user_link(user_id)} забанен!\n{level_names[level]}\nПричина: {reason or 'Не указана'}"
    
    def sysunban_user(self, admin_id, user_id):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return False, "❌ У вас нет доступа к команде /sysunban!"
        self.cursor.execute('UPDATE users SET sysban_level = 0, sysban_by = 0, sysban_reason = "", sysban_date = "" WHERE user_id = ?', (user_id,))
        self.conn.commit()
        self.log_action(admin_id, 'sysunban', user_id, "Разбан")
        return True, f"✅ Пользователь {self.get_user_link(user_id)} разбанен!"
    
    def sysinfo_user(self, admin_id, user_id):
        if not self.has_agent_permission(admin_id, 'sysinfo'):
            return "❌ У вас нет доступа к команде /sysinfo!"
        user = self.get_user(user_id)
        in_blacklist = user[25] > 0
        info = f"📋 **Системная информация о {self.get_user_link(user_id)}**\n━━━━━━━━━━━━━━━━━━━━━━\n🔒 В ЧС бота: {'✅ Да' if in_blacklist else '❌ Нет'}\n"
        if in_blacklist:
            level_names = {1: "Полный ЧС бота", 2: "Запрет доступа к командам", 3: "Слив денег", 4: "Анулирование аккаунта"}
            info += f"├─ Стадия: {level_names.get(user[25], user[25])}\n├─ Кто занёс: {self.get_user_link(user[26])}\n└─ Причина: {user[27] or 'Не указана'}\n"
        self.cursor.execute('SELECT chat_id FROM chats WHERE owner_id = ?', (user_id,))
        owner_chats = self.cursor.fetchall()
        self.cursor.execute('SELECT DISTINCT chat_id FROM invites WHERE user_id = ?', (user_id,))
        user_chats = self.cursor.fetchall()
        info += f"\n🏢 В каких чатах пользователь: {len(user_chats)}\n"
        for chat in user_chats[:5]:
            info += f"├─ Беседа {chat[0]}\n"
        if len(user_chats) > 5:
            info += f"└─ и еще {len(user_chats)-5} чатов...\n"
        info += f"\n👑 В каких чатах владелец: {len(owner_chats)}\n"
        for chat in owner_chats[:5]:
            info += f"├─ Беседа {chat[0]}\n"
        if len(owner_chats) > 5:
            info += f"└─ и еще {len(owner_chats)-5} чатов...\n"
        return info
    
    def get_sysinfo_help(self):
        return ("ℹ️ **Что означают цифры в sysinfo:**\n━━━━━━━━━━━━━━━━━━━━━━\n1️⃣ - Информация о пользователе\n2️⃣ - В каких чатах пользователь\n3️⃣ - В каких чатах владелец\n4️⃣ - Эта справка")
    
    def get_user_chats(self, admin_id, user_id):
        if not self.has_agent_permission(admin_id, 'sysinfo'):
            return "❌ У вас нет доступа к этой информации!"
        self.cursor.execute('SELECT DISTINCT chat_id FROM invites WHERE user_id = ?', (user_id,))
        chats = self.cursor.fetchall()
        if not chats:
            return f"📋 Пользователь {self.get_user_link(user_id)} не состоит ни в одной беседе бота."
        info = f"📋 **Чаты, где состоит {self.get_user_link(user_id)}:**\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for chat in chats:
            info += f"├─ Беседа {chat[0]}\n"
        return info
    
    def get_owner_chats(self, admin_id, user_id):
        if not self.has_agent_permission(admin_id, 'sysinfo'):
            return "❌ У вас нет доступа к этой информации!"
        self.cursor.execute('SELECT chat_id FROM chats WHERE owner_id = ?', (user_id,))
        chats = self.cursor.fetchall()
        if not chats:
            return f"📋 Пользователь {self.get_user_link(user_id)} не является владельцем ни одной беседы."
        info = f"👑 **Чаты, где {self.get_user_link(user_id)} владелец:**\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for chat in chats:
            info += f"├─ Беседа {chat[0]}\n"
        return info
    
    def get_syslinks(self, admin_id, chat_id):
        if not self.has_agent_permission(admin_id, 'syslinks'):
            return "❌ У вас нет доступа к этой команде!"
        try:
            invite_link = self.vk_api.messages.getInviteLink(peer_id=2000000000 + chat_id)
            return f"🔗 Ссылка на беседу {chat_id}:\n{invite_link['link']}"
        except Exception as e:
            return f"❌ Ошибка получения ссылки: {str(e)}"
    
    def get_suspicious_logs(self, admin_id):
        if not self.has_agent_permission(admin_id, 'logs'):
            return "❌ У вас нет доступа к этой команде!"
        if not self.suspicious_logs:
            return "📋 Подозрительные логи отсутствуют."
        info = "📜 **Подозрительные логи:**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for log in self.suspicious_logs[-20:]:
            info += f"🕐 {log.get('time', '')}\n👤 Пользователь: {self.get_user_link(log.get('user',0))}\n🔧 Действие: {log.get('action', '')}\n"
            if log.get('target'):
                info += f"🎯 Цель: {self.get_user_link(log.get('target'))}\n"
            if log.get('reason'):
                info += f"📝 Причина: {log.get('reason')}\n"
            info += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        return info
    
    def sysrestart(self, admin_id):
        if not self.has_agent_permission(admin_id, 'sysrestart'):
            return False, "❌ У вас нет доступа к этой команде!"
        self.log_action(admin_id, 'sysrestart', 0, "Рестарт бота")
        return True, "🔄 Бот перезапускается..."
    
    def get_bhelp(self, admin_id):
        if not self.has_agent_permission(admin_id, 'bhelp'):
            return "❌ У вас нет доступа к этой команде!"
        return ("🔐 **Скрытые команды (доступ через /agent):**\n━━━━━━━━━━━━━━━━━━━━━━\n"
                "• /bhelp - Этот список\n• /sysrestart - Перезапуск бота\n• /syslinks [id] - Ссылка на беседу\n"
                "• /logs - Подозрительные логи\n• /wipe - Вайп денег\n• /wipeuser [id] - Вайп пользователя\n"
                "• /gkick [id] - Глобальный кик\n• /gban [id] - Глобальный бан\n• /gmute [id] [минуты] - Глобальный мут\n"
                "• /grole [id] [роль] - Глобальная роль\n\n⚙️ **Система объединений:**\n"
                "• /гкопировать [название] - Создать объединение\n• /гкик [id] [причина] - Кик во всех беседах\n"
                "• /гбан [id] [причина] - Бан во всех беседах\n• /гмут [id] [минуты] - Мут во всех беседах\n"
                "• /гроль [id] [роль] - Выдать роль во всех беседах")
    
    def wipe_money(self, admin_id, user_id=None):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return "❌ У вас нет доступа!"
        if user_id:
            self.cursor.execute('UPDATE users SET rubles = 0, dollars = 0, euros = 0, bitcoin = 0 WHERE user_id = ?', (user_id,))
            msg = f"💰 Деньги пользователя {self.get_user_link(user_id)} обнулены!"
        else:
            self.cursor.execute('UPDATE users SET rubles = 0, dollars = 0, euros = 0, bitcoin = 0')
            msg = "💰 Деньги всех пользователей обнулены!"
        self.conn.commit()
        self.log_action(0, admin_id, 'wipe_money', user_id or 0, "Вайп денег")
        return msg
    
    def wipe_warns(self, admin_id, user_id=None):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return "❌ У вас нет доступа!"
        if user_id:
            self.cursor.execute('UPDATE users SET warns = 0 WHERE user_id = ?', (user_id,))
            msg = f"⚠️ Варны пользователя {self.get_user_link(user_id)} обнулены!"
        else:
            self.cursor.execute('UPDATE users SET warns = 0')
            msg = "⚠️ Варны всех пользователей обнулены!"
        self.conn.commit()
        self.log_action(0, admin_id, 'wipe_warns', user_id or 0, "Вайп варнов")
        return msg
    
    def wipe_mutes(self, admin_id, user_id=None):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return "❌ У вас нет доступа!"
        if user_id:
            self.cursor.execute('UPDATE users SET is_muted = 0, mute_until = NULL WHERE user_id = ?', (user_id,))
            msg = f"🔇 Муты пользователя {self.get_user_link(user_id)} сняты!"
        else:
            self.cursor.execute('UPDATE users SET is_muted = 0, mute_until = NULL')
            msg = "🔇 Муты всех пользователей сняты!"
        self.conn.commit()
        self.log_action(0, admin_id, 'wipe_mutes', user_id or 0, "Вайп мутов")
        return msg
    
    def wipe_bans(self, admin_id, user_id=None):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return "❌ У вас нет доступа!"
        if user_id:
            self.cursor.execute('UPDATE users SET role = "Пользователь", sysban_level = 0 WHERE user_id = ?', (user_id,))
            msg = f"⛔ Бан пользователя {self.get_user_link(user_id)} снят!"
        else:
            self.cursor.execute('UPDATE users SET role = "Пользователь", sysban_level = 0 WHERE role = "banned" OR sysban_level > 0')
            msg = "⛔ Баны всех пользователей сняты!"
        self.conn.commit()
        self.log_action(0, admin_id, 'wipe_bans', user_id or 0, "Вайп банов")
        return msg
    
    def wipe_vip(self, admin_id, user_id=None):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return "❌ У вас нет доступа!"
        if user_id:
            self.cursor.execute('UPDATE users SET vip_level = 0, vip_until = NULL, role = "Пользователь" WHERE user_id = ?', (user_id,))
            msg = f"💎 VIP статус пользователя {self.get_user_link(user_id)} снят!"
        else:
            self.cursor.execute('UPDATE users SET vip_level = 0, vip_until = NULL, role = "Пользователь" WHERE vip_level > 0')
            msg = "💎 VIP статусы всех пользователей сняты!"
        self.conn.commit()
        self.log_action(0, admin_id, 'wipe_vip', user_id or 0, "Вайп VIP")
        return msg
    
    def snick_command(self, admin_id, target_id, nickname, chat_id=None):
        if not self.has_agent_permission(admin_id, 'snick'):
            return False, "❌ У вас нет доступа к команде /snick!"
        self.cursor.execute('UPDATE users SET nickname = ? WHERE user_id = ?', (nickname, target_id))
        self.conn.commit()
        self.log_action(admin_id, 'set_nickname', target_id, nickname)
        msg = f"✅ Пользователю {self.get_user_link(target_id)} установлен ник: {nickname}"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def rnick_command(self, admin_id, target_id, chat_id=None):
        if not self.has_agent_permission(admin_id, 'rnick'):
            return False, "❌ У вас нет доступа к команде /rnick!"
        self.cursor.execute('UPDATE users SET nickname = "" WHERE user_id = ?', (target_id,))
        self.conn.commit()
        self.log_action(admin_id, 'remove_nickname', target_id, "Удален ник")
        msg = f"✅ Ник пользователя {self.get_user_link(target_id)} удален!"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def nonames_command(self, admin_id, chat_id=None):
        if not self.has_agent_permission(admin_id, 'snick'):
            return False, "❌ У вас нет доступа к команде /nonames!"
        self.cursor.execute('SELECT user_id, name FROM users WHERE (nickname = "" OR nickname IS NULL) AND is_agent = 0')
        users = self.cursor.fetchall()
        if users:
            msg = "📋 **Список пользователей без ников:**\n━━━━━━━━━━━━━━━━━━\n"
            for uid, name in users[:20]:
                msg += f"• {self.get_user_link(uid)}\n"
            if len(users) > 20:
                msg += f"\n... и еще {len(users)-20} пользователей"
        else:
            msg = "✅ Все пользователи имеют ники!"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def ponicku_command(self, admin_id, search_part, chat_id=None):
        if not self.has_agent_permission(admin_id, 'snick'):
            return False, "❌ У вас нет доступа к команде /ponicku!"
        self.cursor.execute('SELECT user_id, name, nickname FROM users WHERE nickname LIKE ? AND nickname != "" AND is_agent = 0', (f'%{search_part}%',))
        users = self.cursor.fetchall()
        if users:
            msg = f"📋 **Пользователи с частью '{search_part}' в нике:**\n━━━━━━━━━━━━━━━━━━\n"
            for uid, name, nickname in users[:20]:
                msg += f"• {self.get_user_link(uid)} - ник: {nickname}\n"
            if len(users) > 20:
                msg += f"\n... и еще {len(users)-20} пользователей"
        else:
            msg = f"❌ Пользователи с частью '{search_part}' в нике не найдены."
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def delkick_command(self, admin_id, chat_id=None):
        if not self.has_agent_permission(admin_id, 'delkick'):
            return False, "❌ У вас нет доступа к команде /delkick!"
        self.cursor.execute('SELECT user_id FROM users WHERE sysban_level = 1 OR sysban_level = 3')
        banned_users = self.cursor.fetchall()
        kicked_count = 0
        for user in banned_users:
            try:
                self.cursor.execute('SELECT chat_id FROM chats WHERE is_active = 1')
                for chat in self.cursor.fetchall():
                    try:
                        self.vk_api.messages.removeChatUser(chat_id=chat[0], user_id=user[0])
                        kicked_count += 1
                    except:
                        pass
            except:
                pass
        self.log_action(admin_id, 'kick_banned', 0, f"Кикнуто {kicked_count} аккаунтов")
        msg = f"✅ Кикнуто заблокированных аккаунтов: {kicked_count}"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def mutereports_command(self, admin_id, target_id, chat_id=None):
        if not self.has_agent_permission(admin_id, 'mutereports'):
            return False, "❌ У вас нет доступа к команде /mutereports!"
        self.cursor.execute('UPDATE users SET reports_muted = 1 WHERE user_id = ?', (target_id,))
        self.conn.commit()
        self.log_action(admin_id, 'mute_reports', target_id, "Мут репортов")
        msg = f"✅ Пользователь {self.get_user_link(target_id)} замучен на репорты!"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def unmutereports_command(self, admin_id, target_id, chat_id=None):
        if not self.has_agent_permission(admin_id, 'unmutereports'):
            return False, "❌ У вас нет доступа к команде /unmutereports!"
        self.cursor.execute('UPDATE users SET reports_muted = 0 WHERE user_id = ?', (target_id,))
        self.conn.commit()
        self.log_action(admin_id, 'unmute_reports', target_id, "Размут репортов")
        msg = f"✅ Пользователь {self.get_user_link(target_id)} размучен на репорты!"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def give_money_command(self, admin_id, target_id, currency, amount, chat_id=None):
        if not self.has_agent_permission(admin_id, 'givemoney'):
            return False, "❌ У вас нет доступа к команде /givemoney!"
        currency_map = {'rub': 'rubles', 'usd': 'dollars', 'eur': 'euros', 'btc': 'bitcoin'}
        if currency not in currency_map:
            return False, "❌ Неверная валюта!"
        self.cursor.execute(f'UPDATE users SET {currency_map[currency]} = {currency_map[currency]} + ? WHERE user_id = ?', (amount, target_id))
        self.conn.commit()
        self.log_action(admin_id, 'give_money', target_id, f"{amount} {currency.upper()}")
        msg = f"✅ Пользователю {self.get_user_link(target_id)} выдано {amount} {currency.upper()}"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def give_vip_command(self, admin_id, target_id, level, chat_id=None):
        if not self.has_agent_permission(admin_id, 'givevip'):
            return False, "❌ У вас нет доступа к команде /givevip!"
        if level not in [1, 2, 3]:
            return False, "❌ Неверный уровень VIP! Доступны: 1, 2, 3"
        vip_until = (datetime.now() + timedelta(days=30)).isoformat()
        self.cursor.execute('UPDATE users SET vip_level = ?, vip_until = ?, role = ? WHERE user_id = ?', (level, vip_until, f'vip{level}', target_id))
        self.conn.commit()
        self.log_action(admin_id, 'give_vip', target_id, f"VIP {level}")
        msg = f"✅ Пользователю {self.get_user_link(target_id)} выдан VIP {level} уровня на 30 дней!"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    def handle_message(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            chat_id = None
            if message.get('peer_id', 0) > 2000000000:
                chat_id = message['peer_id'] - 2000000000
            else:
                user_id = message['from_id']
                text = message.get('text', '')
                if text.lower() in self.commands['reports']:
                    self.handle_reports_in_dm(user_id, text)
                return
            
            if chat_id:
                self.get_or_create_chat(chat_id)
            
            if 'text' in message:
                text = message['text'].lower()
                user_id = message['from_id']
                
                user = self.get_user(user_id)
                if user[25] in [1, 2, 3]:
                    if user[25] == 1 or user[25] == 3:
                        if text not in self.commands['report']:
                            self.send_message("❌ Вы находитесь в ЧС бота. Обратитесь в поддержку.", chat_id, user_id)
                            return
                    elif user[25] == 2:
                        if text not in self.commands['report'] and not any(text in cmd_list for cmd_list in self.commands.values()):
                            self.send_message("❌ Вам запрещен доступ к командам.", chat_id, user_id)
                            return
                
                if text in self.commands['start']:
                    self.activate_chat(chat_id, user_id)
                    return
                
                self.cursor.execute('SELECT is_active FROM chats WHERE chat_id = ?', (chat_id,))
                result = self.cursor.fetchone()
                if not result or result[0] == 0:
                    if text not in self.commands['start']:
                        self.send_message("❌ Беседа не активирована! Введите /start для активации.", chat_id)
                    return
                
                # ========== СЕКРЕТНЫЕ КОМАНДЫ (через /agent) ==========
                
                if text in self.commands['bhelp']:
                    self.send_message(self.get_bhelp(user_id), chat_id)
                    return
                
                if text in self.commands['sysrestart']:
                    success, msg = self.sysrestart(user_id)
                    self.send_message(msg, chat_id)
                    if success:
                        threading.Timer(2, lambda: os._exit(0)).start()
                    return
                
                if text in self.commands['syslinks']:
                    if self.has_agent_permission(user_id, 'syslinks'):
                        self.send_message("🔗 Введите ID беседы:", chat_id)
                        self.waiting_for_syslinks[user_id] = True
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                if text in self.commands['logs']:
                    self.send_message(self.get_suspicious_logs(user_id), chat_id)
                    return
                
                if text in self.commands['wipe']:
                    if self.has_agent_permission(user_id, 'sysban'):
                        keyboard = self.create_wipe_keyboard()
                        self.send_message("⚠️ **Вайп система**\n\nВыберите что обнулить:", chat_id, keyboard=keyboard)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                if text in self.commands['wipeuser']:
                    if self.has_agent_permission(user_id, 'sysban'):
                        parts = text.split()
                        if len(parts) >= 2:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            if target_id:
                                self.waiting_for_wipe_user = target_id
                                self.send_message(f"⚠️ **Вайп пользователя {self.get_user_link(target_id)}**\n\nВыберите что обнулить:", chat_id, keyboard=self.create_wipe_keyboard())
                            else:
                                self.send_message("❌ Пользователь не найден!", chat_id)
                        else:
                            self.send_message("❌ Использование: /wipeuser [пользователь]", chat_id)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                # ========== СИСТЕМА ОБЪЕДИНЕНИЙ ==========
                
                if text in self.commands['union']:
                    msg = ("🏢 **Система объединений**\n━━━━━━━━━━━━━━━━━━━━━━\n"
                           "• /union_create [название] - Создать объединение\n"
                           "• /union_join [код] - Вступить в объединение\n"
                           "• /union_leave - Выйти из объединения\n"
                           "• /union_info - Информация об объединении\n"
                           "• /union_invite - Создать новый код (владелец)\n"
                           "• /union_ban [пользователь] - Бан во всех беседах (владелец)\n"
                           "• /union_mute [пользователь] [минуты] - Мут везде (владелец)\n"
                           "• /union_kick [пользователь] - Кик везде (владелец)\n"
                           "• /union_role [пользователь] [роль] - Роль везде (владелец)")
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
                    target_id = self.extract_user_id(parts[1], message.get('reply_message'))
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
                        self.send_message("❌ /union_mute [пользователь] [минуты] [причина]", chat_id)
                        return
                    target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    if not target_id:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                        return
                    try:
                        minutes = int(parts[2])
                    except ValueError:
                        self.send_message("❌ Минуты должны быть числом!", chat_id)
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
                    target_id = self.extract_user_id(parts[1], message.get('reply_message'))
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
                    target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    if not target_id:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                        return
                    role = parts[2]
                    success, msg = self.union_role(user_id, target_id, role)
                    self.send_message(msg, chat_id)
                    return
                
                # ========== КОМАНДЫ ДЛЯ АГЕНТОВ ==========
                
                if text in self.commands['rates']:
                    self.send_message(self.get_exchange_rates_info(), chat_id)
                    return
                
                if text in self.commands['setrate'] and self.is_agent(user_id):
                    parts = text.split()
                    if len(parts) >= 3:
                        currency = parts[1]
                        try:
                            rate = float(parts[2])
                            success, msg = self.set_exchange_rate(user_id, currency, rate)
                            self.send_message(msg, chat_id)
                        except ValueError:
                            self.send_message("❌ Курс должен быть числом!", chat_id)
                    else:
                        self.send_message("❌ Использование: /setrate [валюта] [курс]\nДоступные валюты: usd, eur, btc_usd, btc_rub", chat_id)
                    return
                
                if text in self.commands['agent']:
                    if not self.can_manage_agents(user_id):
                        self.send_message("❌ У вас нет доступа к команде /agent!", chat_id)
                        return
                    keyboard = self.create_inline_keyboard([
                        {'text': '❌ Отмена', 'payload': json.dumps({'action': 'agent_cancel'}), 'color': 'negative'}
                    ])
                    self.send_message("🔧 **Управление правами агентов**\n\nВведите ID агента для настройки (или нажмите Отмена):", chat_id, keyboard=keyboard)
                    self.waiting_for_agent_id[user_id] = True
                    self.waiting_for_agent_expiry[user_id] = time.time() + 60
                    return
                
                if text in self.commands['botadmins']:
                    if not self.is_agent(user_id):
                        self.send_message("❌ Вы не являетесь агентом!", chat_id)
                        return
                    agents = self.get_all_agents()
                    if agents:
                        info = "👑 **Список агентов поддержки**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        for agent_id, name, agent_number, tickets, rating in agents:
                            info += f"**#{agent_number}** | {self.get_user_link(agent_id)}\n📊 Тикетов: {tickets} | Рейтинг: {rating:.1f}⭐\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        keyboard = self.create_botadmins_keyboard()
                        self.send_message(info, chat_id, keyboard=keyboard)
                    else:
                        self.send_message("📋 Список агентов пуст.", chat_id)
                    return
                
                if text in self.commands['givemoney']:
                    if not self.has_agent_permission(user_id, 'givemoney'):
                        self.send_message("❌ У вас нет доступа к команде /givemoney!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 4:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            currency = parts[2]
                            try:
                                amount = float(parts[3])
                                success, msg = self.give_money_command(user_id, target_id, currency, amount, chat_id)
                                self.send_message(msg, chat_id)
                            except ValueError:
                                self.send_message("❌ Сумма должна быть числом!", chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /givemoney [пользователь] [валюта] [сумма]\nВалюты: rub, usd, eur, btc", chat_id)
                    return
                
                if text in self.commands['givevip']:
                    if not self.has_agent_permission(user_id, 'givevip'):
                        self.send_message("❌ У вас нет доступа к команде /givevip!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 3:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            try:
                                level = int(parts[2])
                                success, msg = self.give_vip_command(user_id, target_id, level, chat_id)
                                self.send_message(msg, chat_id)
                            except ValueError:
                                self.send_message("❌ Уровень VIP должен быть числом (1-3)!", chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /givevip [пользователь] [уровень]\nУровни: 1, 2, 3", chat_id)
                    return
                
                if text in self.commands['sysban']:
                    if not self.has_agent_permission(user_id, 'sysban'):
                        self.send_message("❌ У вас нет доступа к команде /sysban!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 3:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            try:
                                level = int(parts[2])
                                reason = ' '.join(parts[3:]) if len(parts) > 3 else None
                                success, msg = self.sysban_user(user_id, target_id, level, reason)
                                self.send_message(msg, chat_id)
                            except ValueError:
                                self.send_message("❌ Стадия должна быть числом (1-4)!", chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("Выберите стадию бана:", chat_id, keyboard=self.create_sysban_keyboard())
                    return
                
                if text in self.commands['sysunban']:
                    if not self.has_agent_permission(user_id, 'sysban'):
                        self.send_message("❌ У вас нет доступа к команде /sysunban!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            success, msg = self.sysunban_user(user_id, target_id)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /sysunban [пользователь]", chat_id)
                    return
                
                if text in self.commands['sysinfo']:
                    if not self.has_agent_permission(user_id, 'sysinfo'):
                        self.send_message("❌ У вас нет доступа к команде /sysinfo!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            keyboard = self.create_sysinfo_keyboard(target_id)
                            self.send_message(f"📋 **Системная информация о {self.get_user_link(target_id)}**\n\nВыберите опцию:", chat_id, keyboard=keyboard)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /sysinfo [пользователь]", chat_id)
                    return
                
                if text in self.commands['snick']:
                    if not self.has_agent_permission(user_id, 'snick'):
                        self.send_message("❌ У вас нет доступа к команде /snick!", chat_id)
                        return
                    parts = text.split(maxsplit=2)
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            nickname = parts[2] if len(parts) > 2 else ""
                            if nickname:
                                success, msg = self.snick_command(user_id, target_id, nickname, chat_id)
                                self.send_message(msg, chat_id)
                            else:
                                self.send_message("❌ Использование: /snick [пользователь] [ник]", chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /snick [пользователь] [ник]", chat_id)
                    return
                
                if text in self.commands['rnick']:
                    if not self.has_agent_permission(user_id, 'rnick'):
                        self.send_message("❌ У вас нет доступа к команде /rnick!", chat_id)
                        return
                    parts = text.split(maxsplit=1)
                    target_id = self.extract_user_id(parts[1] if len(parts) > 1 else '', message.get('reply_message'))
                    if target_id:
                        success, msg = self.rnick_command(user_id, target_id, chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                if text in self.commands['nonames']:
                    if not self.has_agent_permission(user_id, 'snick'):
                        self.send_message("❌ У вас нет доступа к команде /nonames!", chat_id)
                        return
                    success, msg = self.nonames_command(user_id, chat_id)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['ponicku']:
                    if not self.has_agent_permission(user_id, 'snick'):
                        self.send_message("❌ У вас нет доступа к команде /ponicku!", chat_id)
                        return
                    parts = text.split(maxsplit=1)
                    if len(parts) > 1:
                        success, msg = self.ponicku_command(user_id, parts[1], chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Использование: /ponicku [часть ника]", chat_id)
                    return
                
                if text in self.commands['delkick']:
                    if not self.has_agent_permission(user_id, 'delkick'):
                        self.send_message("❌ У вас нет доступа к команде /delkick!", chat_id)
                        return
                    success, msg = self.delkick_command(user_id, chat_id)
                    self.send_message(msg, chat_id)
                    return
                
                if text in self.commands['mutereports']:
                    if not self.has_agent_permission(user_id, 'mutereports'):
                        self.send_message("❌ У вас нет доступа к команде /mutereports!", chat_id)
                        return
                    parts = text.split(maxsplit=1)
                    target_id = self.extract_user_id(parts[1] if len(parts) > 1 else '', message.get('reply_message'))
                    if target_id:
                        success, msg = self.mutereports_command(user_id, target_id, chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                if text in self.commands['unmutereports']:
                    if not self.has_agent_permission(user_id, 'unmutereports'):
                        self.send_message("❌ У вас нет доступа к команде /unmutereports!", chat_id)
                        return
                    parts = text.split(maxsplit=1)
                    target_id = self.extract_user_id(parts[1] if len(parts) > 1 else '', message.get('reply_message'))
                    if target_id:
                        success, msg = self.unmutereports_command(user_id, target_id, chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                # ========== ОБЫЧНЫЕ КОМАНДЫ ==========
                
                if text in self.commands['settings']:
                    settings = self.get_chat_settings(chat_id)
                    keyboard = self.create_settings_keyboard(settings)
                    self.send_message("⚙️ **Настройки чата**\n\nВыберите параметр для изменения:", chat_id, keyboard=keyboard)
                    return
                
                if text in self.commands['ping']:
                    start_time = time.time()
                    response_time = (time.time() - start_time) * 1000
                    self.send_message(f"🏓 **Бот работает!**\n━━━━━━━━━━━━━━━━━━━━━━\n⏱️ Пинг: {response_time:.2f} мс\n🔄 Статус: ✅ Активен", chat_id, keyboard=self.create_ping_keyboard())
                    return
                
                if text in self.commands['shop']:
                    self.send_message("🛒 **Магазин**\n━━━━━━━━━━━━━━━━━━\n💰 Валюта: Доллары ($)\n\nВыберите категорию:", chat_id, keyboard=self.create_shop_category_keyboard())
                    return
                
                if text in self.commands['help']:
                    self.send_message("📖 **Список команд:**\nhttps://vk.com/@your_article", chat_id)
                    return
                
                if text in self.commands['report']:
                    parts = text.split(maxsplit=1)
                    if len(parts) > 1:
                        success, msg = self.add_report(user_id, user_id, parts[1], chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Использование: /report [текст вопроса/проблемы]", chat_id)
                    return
                
                if text in self.commands['transfer']:
                    parts = text.split()
                    if len(parts) >= 4:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            try:
                                success, msg = self.transfer_money(user_id, target_id, parts[2], float(parts[3]))
                                self.send_message(msg, chat_id)
                            except ValueError:
                                self.send_message("❌ Сумма должна быть числом!", chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /transfer [пользователь] [валюта] [сумма]\nДоступные валюты: rub, usd, eur, btc", chat_id)
                    return
                
                if text in self.commands['slaves']:
                    self.send_message("🔄 **Система рабов**\n\nВыберите действие:", chat_id, keyboard=self.create_slave_keyboard())
                    return
                
                if text in self.commands['stats']:
                    self.send_message(self.get_user_stats_detailed(user_id, chat_id), chat_id)
                    return
                
                if text in self.commands['vip']:
                    self.send_message(self.get_vip_info(user_id), chat_id)
                    return
                
                if text in self.commands['staff']:
                    staff = self.get_staff_list()
                    if staff:
                        staff_text = "👥 **Персонал:**\n━━━━━━━━━━━━━━━━━━\n"
                        for member in staff:
                            role_emoji = self.status_emojis.get(member['role'], '👤')
                            staff_text += f"{role_emoji} {self.get_user_link(member['id'])} - {member['role']}\n"
                        self.send_message(staff_text, chat_id, keyboard=self.create_staff_keyboard())
                    else:
                        self.send_message("👥 Персонал отсутствует.", chat_id)
                    return
                
                if text in self.commands['roleslist']:
                    roles = self.get_roles_list()
                    if roles:
                        roles_text = "📋 **Список ролей:**\n━━━━━━━━━━━━━━━━━━\n"
                        for role_name, priority in roles:
                            roles_text += f"• {role_name} - приоритет: {priority}\n"
                        self.send_message(roles_text, chat_id)
                    else:
                        self.send_message("📋 Роли не найдены.", chat_id)
                    return
                
                if text in self.commands['addrole']:
                    parts = text.split()
                    if len(parts) >= 3:
                        try:
                            success, msg = self.add_custom_role(user_id, parts[1], int(parts[2]))
                            self.send_message(msg, chat_id)
                        except ValueError:
                            self.send_message("❌ Приоритет должен быть числом!", chat_id)
                    else:
                        self.send_message("❌ Использование: /addrole [название] [приоритет]", chat_id)
                    return
                
                if text in self.commands['newrole']:
                    if self.has_command_access(user_id, 'addrole'):
                        self.send_message("🔄 **Создание/изменение роли**\n\nВведите в формате:\n[приоритет] [название роли]\n\nПример: 75 Премиум пользователь", chat_id)
                        self.waiting_for_newrole[user_id] = True
                    else:
                        self.send_message("❌ У вас нет прав для создания/изменения ролей!", chat_id)
                    return
                
                if text in self.commands['setrole']:
                    parts = text.split()
                    if len(parts) >= 3:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            success, msg = self.set_user_role(user_id, target_id, parts[2], chat_id)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /setrole [пользователь] [роль]", chat_id)
                    return
                
                # Модерация
                if text in self.commands['ban']:
                    if not self.has_command_access(user_id, 'ban'):
                        self.send_message("❌ У вас нет прав для бана!", chat_id)
                        return
                    parts = text.split(maxsplit=2)
                    target_id = self.extract_user_id(parts[1] if len(parts) > 1 else '', message.get('reply_message'))
                    if target_id:
                        reason = parts[2] if len(parts) > 2 else None
                        self.ban_user(target_id, user_id, chat_id, reason)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                if text in self.commands['mute']:
                    if not self.has_command_access(user_id, 'mute'):
                        self.send_message("❌ У вас нет прав для мута!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            minutes = int(parts[2]) if len(parts) > 2 else None
                            self.mute_user(target_id, user_id, chat_id, minutes)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /mute [пользователь] [минуты]", chat_id)
                    return
                
                if text in self.commands['warn']:
                    if not self.has_command_access(user_id, 'warn'):
                        self.send_message("❌ У вас нет прав для выдачи варнов!", chat_id)
                        return
                    parts = text.split(maxsplit=2)
                    target_id = self.extract_user_id(parts[1] if len(parts) > 1 else '', message.get('reply_message'))
                    if target_id:
                        reason = parts[2] if len(parts) > 2 else None
                        self.add_warn(target_id, user_id, chat_id, reason)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                if text in self.commands['kick']:
                    if not self.has_command_access(user_id, 'kick'):
                        self.send_message("❌ У вас нет прав для кика!", chat_id)
                        return
                    parts = text.split(maxsplit=2)
                    target_id = self.extract_user_id(parts[1] if len(parts) > 1 else '', message.get('reply_message'))
                    if target_id:
                        reason = parts[2] if len(parts) > 2 else None
                        self.kick_user(user_id, target_id, chat_id, reason)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                if text in self.commands['balance']:
                    user = self.get_user(user_id)
                    self.send_message(f"💰 **Ваш баланс:**\n━━━━━━━━━━━━━━━━━━\n🇷🇺 Рубли: {user[7]:.2f} ₽\n🇺🇸 Доллары: {user[8]:.2f} $\n🇪🇺 Евро: {user[9]:.2f} €\n₿ Биткойны: {user[6]:.8f} BTC", chat_id)
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
                
                if text in self.commands['buy']:
                    parts = text.split()
                    if len(parts) >= 2:
                        item = parts[1]
                        if item == 'vip1':
                            success, msg = self.buy_vip(user_id, 1)
                        elif item == 'vip2':
                            success, msg = self.buy_vip(user_id, 2)
                        elif item == 'vip3':
                            success, msg = self.buy_vip(user_id, 3)
                        elif item == 'miner':
                            success, msg = self.buy_miner(user_id)
                        else:
                            self.send_message("❌ Неизвестный товар! Используйте /shop", chat_id)
                            return
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Использование: /buy [товар]", chat_id)
                    return
                
                if text in self.commands['chat_info']:
                    chat = self.get_or_create_chat(chat_id)
                    self.send_message(f"📊 **Информация о беседе**\n━━━━━━━━━━━━━━━━━━\n💬 Название: {chat[1]}\n🆔 ID: {chat[0]}\n🔘 Статус: {'✅ Активна' if chat[3] == 1 else '❌ Не активирована'}", chat_id)
                    return
                
                if text in self.commands['filter']:
                    parts = text.split()
                    if len(parts) >= 3:
                        action = parts[1]
                        word = parts[2]
                        filter_action = parts[3] if len(parts) > 3 else self.config['filter_action']
                        if action in ['add', 'добавить']:
                            if not self.has_command_access(user_id, 'filter'):
                                self.send_message("❌ У вас нет прав для добавления фильтров!", chat_id)
                                return
                            self.add_chat_filter(chat_id, word, filter_action, user_id)
                            self.send_message(f"✅ Слово '{word}' добавлено в фильтр!", chat_id)
                        elif action in ['remove', 'удалить']:
                            if not self.has_command_access(user_id, 'filter'):
                                self.send_message("❌ У вас нет прав для удаления фильтров!", chat_id)
                                return
                            self.remove_chat_filter(chat_id, word, user_id)
                            self.send_message(f"✅ Слово '{word}' удалено из фильтра!", chat_id)
                        elif action in ['list', 'список']:
                            filters = self.get_chat_filters(chat_id)
                            if filters:
                                filter_list = "📋 **Список фильтров:**\n━━━━━━━━━━━━━━━━━━\n"
                                for w, a in filters:
                                    action_emoji = {'warn': '⚠️', 'mute': '🔇', 'ban': '⛔'}.get(a, '⚠️')
                                    filter_list += f"{action_emoji} {w} → {a}\n"
                                self.send_message(filter_list, chat_id)
                            else:
                                self.send_message("📋 Фильтров нет.", chat_id)
                    else:
                        self.send_message("❌ Использование: /filter [add/remove/list] [слово] [действие]", chat_id)
                    return
                
                if text in self.commands['invite']:
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            self.record_invite(chat_id, target_id, user_id)
                            self.send_message(f"✅ Пользователь {self.get_user_link(target_id)} приглашен!", chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /invite [пользователь]", chat_id)
                    return
                
                if text in self.commands['probivtiket']:
                    if self.has_agent_permission(user_id, 'reports'):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            if target_id:
                                reports = self.get_closed_reports_today(target_id)
                                if reports:
                                    msg = f"📋 **Закрытые тикеты пользователя {self.get_user_link(target_id)} за сегодня:**\n━━━━━━━━━━━━━━━━━━━━━━\n"
                                    for report in reports:
                                        msg += f"**#{report[0]}** | Оценка: {report[2]}/5⭐ | Закрыл: {self.get_user_link(report[3])} | {report[4][:16]}\n💬 {report[1][:100]}\n━━━━━━━━━━━━━━━━━━━━━━\n"
                                    self.send_message(msg, chat_id)
                                else:
                                    self.send_message(f"📋 У пользователя {self.get_user_link(target_id)} нет закрытых тикетов за сегодня.", chat_id)
                            else:
                                self.send_message("❌ Пользователь не найден!", chat_id)
                        else:
                            self.send_message("❌ Использование: /probivtiket [пользователь]", chat_id)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                if text in self.commands['sysadmin']:
                    if not self.is_super_admin(user_id):
                        self.send_message("❌ У вас нет прав для выдачи супер-админа!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            if target_id in self.super_admins:
                                self.send_message(f"❌ Пользователь {self.get_user_link(target_id)} уже является супер-админом!", chat_id)
                                return
                            self.super_admins.append(target_id)
                            self.send_message(f"✅ Пользователь {self.get_user_link(target_id)} добавлен в список супер-админов!\nТеперь он имеет доступ ко всем командам.", chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /sysadmin [пользователь]", chat_id)
                    return
    
    def add_chat_filter(self, chat_id, word, action, admin_id):
        try:
            self.cursor.execute('INSERT INTO chat_filters (chat_id, word, action, added_by, added_at) VALUES (?, ?, ?, ?, ?)',
                               (chat_id, word.lower(), action, admin_id, datetime.now().isoformat()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_chat_filter(self, chat_id, word, admin_id):
        self.cursor.execute('DELETE FROM chat_filters WHERE chat_id = ? AND word = ?', (chat_id, word.lower()))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_chat_filters(self, chat_id):
        self.cursor.execute('SELECT word, action FROM chat_filters WHERE chat_id = ?', (chat_id,))
        return self.cursor.fetchall()
    
    def record_invite(self, chat_id, user_id, inviter_id):
        self.cursor.execute('INSERT INTO invites (chat_id, user_id, inviter_id, invited_at) VALUES (?, ?, ?, ?)',
                           (chat_id, user_id, inviter_id, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_chat_settings(self, chat_id):
        self.cursor.execute('SELECT settings FROM chats WHERE chat_id = ?', (chat_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            try:
                return json.loads(result[0])
            except:
                pass
        return self.default_chat_settings.copy()
    
    def save_chat_settings(self, chat_id, settings):
        self.cursor.execute('UPDATE chats SET settings = ? WHERE chat_id = ?', 
                           (json.dumps(settings, ensure_ascii=False), chat_id))
        self.conn.commit()
    
    def get_closed_reports_today(self, user_id):
        today = datetime.now().date().isoformat()
        self.cursor.execute('SELECT id, message, rating, closed_by, closed_at FROM reports WHERE user_id = ? AND status = "closed" AND date(closed_at) = ?', (user_id, today))
        return self.cursor.fetchall()
    
    def get_vip_info(self, user_id):
        user = self.get_user(user_id)
        if user[3] == 0:
            return "❌ У вас нет VIP статуса! Используйте /shop для покупки."
        benefits = self.config['vip_benefits'].get(user[3], {})
        info = f"✨ **VIP {user[3]} уровня**\n💎 Уровень: {user[3]}\n\n📊 **Ваши возможности:**\n━━━━━━━━━━━━━━━━━━\n"
        info += f"🏢 Можно создать объединений: {benefits.get('max_unions',0)}\n"
        info += f"💬 В каждое объединение можно добавить: {benefits.get('max_chats',0)} бесед\n"
        if user[4]:
            try:
                vip_until = datetime.fromisoformat(user[4])
                info += f"\n⏰ Статус действует до: {vip_until.strftime('%d.%m.%Y %H:%M')}"
            except:
                pass
        return info
    
    def get_agent_stats_for_user(self, agent_id):
        user = self.get_user(agent_id)
        return (f"👑 **Статистика агента #{user[21]}**\n━━━━━━━━━━━━━━━━━━━━━━\n👤 {self.get_user_link(agent_id)}\n📊 Всего обработано: {user[22]}\n⭐ Средний рейтинг: {user[23]:.1f}/5\n")
    
    # ========== КЛАВИАТУРЫ ==========
    
    def create_inline_keyboard(self, buttons):
        keyboard = {"inline": True, "buttons": []}
        row = []
        for button in buttons:
            row.append({
                "action": {"type": "callback", "label": button['text'], "payload": button.get('payload', {})},
                "color": button.get('color', 'primary')
            })
            if len(row) == 2 or button == buttons[-1]:
                keyboard['buttons'].append(row)
                row = []
        return json.dumps(keyboard, ensure_ascii=False)
    
    def create_callback_keyboard(self, buttons):
        return self.create_inline_keyboard(buttons)
    
    def create_shop_category_keyboard(self):
        return self.create_inline_keyboard([
            {'text': '📱 Телефоны', 'payload': json.dumps({'action': 'shop_category', 'category': 'phones'}), 'color': 'primary'},
            {'text': '🏠 Дома', 'payload': json.dumps({'action': 'shop_category', 'category': 'houses'}), 'color': 'primary'},
            {'text': '👕 Одежда', 'payload': json.dumps({'action': 'shop_category', 'category': 'clothes'}), 'color': 'primary'},
            {'text': '🎁 Вещи', 'payload': json.dumps({'action': 'shop_category', 'category': 'items'}), 'color': 'primary'},
            {'text': '💎 VIP Статусы', 'payload': json.dumps({'action': 'shop_category', 'category': 'vip'}), 'color': 'positive'},
            {'text': '⛏️ Майнер BTC', 'payload': json.dumps({'action': 'buy_miner'}), 'color': 'primary'}
        ])
    
    def create_shop_items_keyboard(self, category, items):
        buttons = []
        for item_name, price in items.items():
            buttons.append({'text': f"{item_name} - {price}$", 'payload': json.dumps({'action': 'buy_item', 'item': item_name}), 'color': 'primary'})
        buttons.append({'text': '🔙 Назад', 'payload': json.dumps({'action': 'shop_back'}), 'color': 'secondary'})
        return self.create_inline_keyboard(buttons)
    
    def create_vip_keyboard(self):
        return self.create_inline_keyboard([
            {'text': '🌟 VIP I - 5000₽', 'payload': json.dumps({'action': 'buy_vip', 'level': 1}), 'color': 'positive'},
            {'text': '💎 VIP II - 15000₽', 'payload': json.dumps({'action': 'buy_vip', 'level': 2}), 'color': 'positive'},
            {'text': '👑 VIP III - 35000₽', 'payload': json.dumps({'action': 'buy_vip', 'level': 3}), 'color': 'positive'},
            {'text': '🔙 Назад', 'payload': json.dumps({'action': 'shop_back'}), 'color': 'secondary'}
        ])
    
    def create_vip_info_keyboard(self, level, price):
        return self.create_inline_keyboard([
            {'text': '💎 Купить', 'payload': json.dumps({'action': 'confirm_buy_vip', 'level': level}), 'color': 'positive'},
            {'text': '🔙 Назад', 'payload': json.dumps({'action': 'vip_back'}), 'color': 'secondary'}
        ])
    
    def create_ping_keyboard(self):
        return self.create_inline_keyboard([{'text': '🔄 Обновить', 'payload': json.dumps({'action': 'ping_refresh'}), 'color': 'primary'}])
    
    def create_botadmins_keyboard(self):
        agents = self.get_all_agents()
        buttons = []
        for agent_id, name, agent_number, tickets, rating in agents:
            buttons.append({'text': f"#{agent_number} - {self.get_user_name(agent_id)}", 'payload': json.dumps({'action': 'show_agent_stats', 'agent_id': agent_id}), 'color': 'primary'})
        return self.create_inline_keyboard(buttons)
    
    def create_wipe_keyboard(self):
        return self.create_inline_keyboard([
            {'text': '💰 Вайп денег', 'payload': json.dumps({'action': 'wipe_money'}), 'color': 'negative'},
            {'text': '⚠️ Вайп варнов', 'payload': json.dumps({'action': 'wipe_warns'}), 'color': 'negative'},
            {'text': '🔇 Вайп мутов', 'payload': json.dumps({'action': 'wipe_mutes'}), 'color': 'negative'},
            {'text': '⛔ Вайп банов', 'payload': json.dumps({'action': 'wipe_bans'}), 'color': 'negative'},
            {'text': '💎 Вайп VIP', 'payload': json.dumps({'action': 'wipe_vip'}), 'color': 'negative'},
            {'text': '🔙 Назад', 'payload': json.dumps({'action': 'wipe_back'}), 'color': 'secondary'}
        ])
    
    def create_sysban_keyboard(self):
        return self.create_inline_keyboard([
            {'text': '1️⃣ Стадия 1', 'payload': json.dumps({'action': 'sysban_stage', 'stage': 1}), 'color': 'negative'},
            {'text': '2️⃣ Стадия 2', 'payload': json.dumps({'action': 'sysban_stage', 'stage': 2}), 'color': 'negative'},
            {'text': '3️⃣ Стадия 3', 'payload': json.dumps({'action': 'sysban_stage', 'stage': 3}), 'color': 'negative'},
            {'text': '4️⃣ Стадия 4', 'payload': json.dumps({'action': 'sysban_stage', 'stage': 4}), 'color': 'negative'},
        ])
    
    def create_sysinfo_keyboard(self, target_id):
        self.sysinfo_target[target_id] = target_id
        return self.create_inline_keyboard([
            {'text': '1️⃣ Информация', 'payload': json.dumps({'action': 'sysinfo_opt', 'option': 1}), 'color': 'primary'},
            {'text': '2️⃣ Чаты пользователя', 'payload': json.dumps({'action': 'sysinfo_opt', 'option': 2}), 'color': 'primary'},
            {'text': '3️⃣ Чаты владельца', 'payload': json.dumps({'action': 'sysinfo_opt', 'option': 3}), 'color': 'primary'},
            {'text': 'ℹ️ Справка', 'payload': json.dumps({'action': 'sysinfo_opt', 'option': 4}), 'color': 'secondary'}
        ])
    
    def create_settings_keyboard(self, settings):
        return self.create_inline_keyboard([
            {'text': f"{'✅' if settings['kick_on_leave'] else '❌'} Кикать при выходе", 'payload': json.dumps({'action': 'settings_toggle', 'setting': 'kick_on_leave'}), 'color': 'primary'},
            {'text': f"👥 Кто может добавлять: {settings['who_can_add']}", 'payload': json.dumps({'action': 'settings_change', 'setting': 'who_can_add'}), 'color': 'primary'},
            {'text': f"{'✅' if settings['games_enabled'] else '❌'} Игры", 'payload': json.dumps({'action': 'settings_toggle', 'setting': 'games_enabled'}), 'color': 'primary'},
            {'text': f"{'✅' if settings['welcome_message'] else '❌'} Приветствие", 'payload': json.dumps({'action': 'settings_toggle', 'setting': 'welcome_message'}), 'color': 'primary'},
            {'text': f"{'✅' if settings['anti_flood'] else '❌'} Антифлуд", 'payload': json.dumps({'action': 'settings_toggle', 'setting': 'anti_flood'}), 'color': 'primary'},
            {'text': '🔙 Закрыть', 'payload': json.dumps({'action': 'settings_close'}), 'color': 'secondary'}
        ])
    
    def create_slave_keyboard(self):
        return self.create_inline_keyboard([
            {'text': '💰 Собрать прибыль', 'payload': json.dumps({'action': 'slave_collect'}), 'color': 'positive'},
            {'text': '🔗 Надеть цепи', 'payload': json.dumps({'action': 'slave_chains'}), 'color': 'primary'},
            {'text': '⬆️ Прокачать рабов', 'payload': json.dumps({'action': 'slave_upgrade'}), 'color': 'primary'},
            {'text': '🆓 Выкупиться', 'payload': json.dumps({'action': 'slave_buyout'}), 'color': 'negative'}
        ])
    
    def create_staff_keyboard(self):
        return self.create_inline_keyboard([{'text': '👥 Показать с никами', 'payload': json.dumps({'action': 'staff_with_nicks'}), 'color': 'primary'}])
    
    def create_who_can_add_keyboard(self):
        return self.create_inline_keyboard([
            {'text': '👥 Все', 'payload': json.dumps({'action': 'settings_set', 'setting': 'who_can_add', 'value': 'all'}), 'color': 'primary'},
            {'text': '🛡️ Администраторы', 'payload': json.dumps({'action': 'settings_set', 'setting': 'who_can_add', 'value': 'admins'}), 'color': 'primary'},
            {'text': '👑 Владелец', 'payload': json.dumps({'action': 'settings_set', 'setting': 'who_can_add', 'value': 'owner'}), 'color': 'positive'},
            {'text': '🔙 Назад', 'payload': json.dumps({'action': 'settings_back'}), 'color': 'secondary'}
        ])
    
    def get_user_name(self, user_id):
        user = self.get_user(user_id)
        return user[24] or user[1]
    
    def handle_slave_system(self, user_id, action):
        if action == "collect":
            self.cursor.execute('SELECT slave_id, level, last_collect FROM slaves WHERE owner_id = ?', (user_id,))
            slaves = self.cursor.fetchall()
            if not slaves:
                return "❌ У вас нет рабов!"
            total_income = 0
            current_time = datetime.now()
            for slave_id, level, last_collect in slaves:
                if last_collect:
                    try:
                        last = datetime.fromisoformat(last_collect)
                        hours_passed = (current_time - last).total_seconds() / 3600
                        hours_passed = min(hours_passed, 24)
                    except:
                        hours_passed = 0
                else:
                    hours_passed = 0
                income = level * 10 * hours_passed
                total_income += income
                self.cursor.execute('UPDATE slaves SET last_collect = ? WHERE owner_id = ? AND slave_id = ?', (current_time.isoformat(), user_id, slave_id))
            if total_income > 0:
                self.add_balance(user_id, 'rub', total_income)
                self.conn.commit()
                return f"💰 Собрано прибыли: {total_income:.2f} ₽"
            else:
                return "⏰ Нет прибыли для сбора! Подождите немного."
        elif action == "buyout":
            self.cursor.execute('SELECT owner_id, level FROM slaves WHERE slave_id = ?', (user_id,))
            owner = self.cursor.fetchone()
            if not owner:
                return "❌ Вы не являетесь рабом!"
            owner_id, level = owner
            buyout_price = 5000 * level
            user = self.get_user(user_id)
            if user[7] >= buyout_price:
                self.add_balance(user_id, 'rub', -buyout_price)
                self.add_balance(owner_id, 'rub', buyout_price)
                self.cursor.execute('DELETE FROM slaves WHERE slave_id = ?', (user_id,))
                self.conn.commit()
                return f"✅ Вы выкупились за {buyout_price:.0f} ₽!"
            else:
                return f"❌ Недостаточно средств! Нужно {buyout_price:.0f} ₽"
        elif action == "chains":
            self.cursor.execute('UPDATE slaves SET chains = chains + 1 WHERE owner_id = ? AND chains < 5', (user_id,))
            self.conn.commit()
            return "🔗 Цепи надеты! Раб будет приносить на 20% больше прибыли." if self.cursor.rowcount > 0 else "❌ Нет рабов или достигнут максимум цепей (5)!"
        elif action == "upgrade":
            self.cursor.execute('SELECT slave_id, level, exp FROM slaves WHERE owner_id = ?', (user_id,))
            slaves = self.cursor.fetchall()
            if not slaves:
                return "❌ У вас нет рабов!"
            upgrade_cost = 1000 * len(slaves)
            user = self.get_user(user_id)
            if user[7] >= upgrade_cost:
                self.add_balance(user_id, 'rub', -upgrade_cost)
                for slave_id, level, exp in slaves:
                    new_exp = exp + 100
                    if new_exp >= level * 100:
                        self.cursor.execute('UPDATE slaves SET level = ?, exp = 0 WHERE owner_id = ? AND slave_id = ?', (level+1, user_id, slave_id))
                    else:
                        self.cursor.execute('UPDATE slaves SET exp = ? WHERE owner_id = ? AND slave_id = ?', (new_exp, user_id, slave_id))
                self.conn.commit()
                return f"⬆️ Рабы прокачаны! Стоимость: {upgrade_cost:.0f} ₽"
            else:
                return f"❌ Недостаточно средств! Нужно {upgrade_cost:.0f} ₽"
        return "❌ Неизвестное действие!"
    
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
    
    def handle_callback_query(self, event):
        if event.type == VkBotEventType.MESSAGE_EVENT:
            payload = event.object.payload
            user_id = event.object.user_id
            chat_id = event.object.peer_id - 2000000000 if event.object.peer_id > 2000000000 else None
            
            try:
                if isinstance(payload, str):
                    data = json.loads(payload)
                else:
                    data = payload
                
                action = data.get('action')
                
                # Магазин
                if action == 'shop_category':
                    category = data.get('category')
                    if category == 'vip':
                        self.send_message("💎 **Выберите VIP статус:**\n\n🌟 VIP I - 5000₽\n💎 VIP II - 15000₽\n👑 VIP III - 35000₽\n\nДействует 30 дней", chat_id, keyboard=self.create_vip_keyboard())
                    else:
                        items = self.inline_shop.get(category, {})
                        if items:
                            category_names = {'phones': '📱 Телефоны', 'houses': '🏠 Дома', 'clothes': '👕 Одежда', 'items': '🎁 Вещи'}
                            self.send_message(f"{category_names.get(category, category)}\n\nВыберите товар:", chat_id, keyboard=self.create_shop_items_keyboard(category, items))
                    return
                
                elif action == 'shop_back':
                    self.send_message("🛒 **Магазин**\n━━━━━━━━━━━━━━━━━━\n💰 Валюта: Доллары ($)\n\nВыберите категорию:", chat_id, keyboard=self.create_shop_category_keyboard())
                    return
                
                elif action == 'buy_vip':
                    level = data.get('level')
                    price = self.shop_items[f'vip{level}']['price']
                    benefits = self.shop_items[f'vip{level}']['benefits']
                    info = (f"💎 **VIP {level} уровня**\n━━━━━━━━━━━━━━━━━━\n💰 Цена: {price}₽\n📅 Действует: 30 дней\n\n📊 **Преимущества:**\n"
                            f"• 🏢 Объединений: {benefits['max_unions']}\n• 💬 Бесед: {benefits['max_chats']}\n"
                            f"• 📢 Команд !скажи: {benefits['daily_say']}/день")
                    self.send_message(info, chat_id, keyboard=self.create_vip_info_keyboard(level, price))
                    return
                
                elif action == 'confirm_buy_vip':
                    level = data.get('level')
                    success, msg = self.buy_vip(user_id, level)
                    self.send_message(msg, chat_id)
                    self.send_message("🛒 **Магазин**\n━━━━━━━━━━━━━━━━━━\n💰 Валюта: Доллары ($)\n\nВыберите категорию:", chat_id, keyboard=self.create_shop_category_keyboard())
                    return
                
                elif action == 'vip_back':
                    self.send_message("💎 **Выберите VIP статус:**\n\n🌟 VIP I - 5000₽\n💎 VIP II - 15000₽\n👑 VIP III - 35000₽\n\nДействует 30 дней", chat_id, keyboard=self.create_vip_keyboard())
                    return
                
                elif action == 'buy_miner':
                    success, msg = self.buy_miner(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                elif action == 'buy_item':
                    item = data.get('item')
                    price = None
                    for category in self.inline_shop.values():
                        if item in category:
                            price = category[item]
                            break
                    if price:
                        success, msg = self.buy_item(user_id, item, price)
                        self.send_message(msg, chat_id)
                    return
                
                # Пинг обновление
                elif action == 'ping_refresh':
                    start_time = time.time()
                    response_time = (time.time() - start_time) * 1000
                    self.send_message(f"🏓 **Бот работает!**\n━━━━━━━━━━━━━━━━━━━━━━\n⏱️ Пинг: {response_time:.2f} мс\n🔄 Статус: ✅ Активен", chat_id, keyboard=self.create_ping_keyboard())
                    return
                
                # Статистика агента
                elif action == 'show_agent_stats':
                    agent_id = data.get('agent_id')
                    self.send_message(self.get_agent_stats_for_user(agent_id), chat_id)
                    return
                
                # Настройки чата
                elif action == 'settings_toggle':
                    setting = data.get('setting')
                    settings = self.get_chat_settings(chat_id)
                    settings[setting] = not settings.get(setting, False)
                    self.save_chat_settings(chat_id, settings)
                    self.send_message(f"⚙️ **Настройки чата**\n\n{setting} изменен на {settings[setting]}", chat_id, keyboard=self.create_settings_keyboard(settings))
                    return
                
                elif action == 'settings_change':
                    if data.get('setting') == 'who_can_add':
                        self.send_message("👥 **Кто может добавлять пользователей?**", chat_id, keyboard=self.create_who_can_add_keyboard())
                    return
                
                elif action == 'settings_set':
                    setting = data.get('setting')
                    value = data.get('value')
                    settings = self.get_chat_settings(chat_id)
                    settings[setting] = value
                    self.save_chat_settings(chat_id, settings)
                    self.send_message(f"⚙️ **Настройки чата**\n\n{setting} изменен на {value}", chat_id, keyboard=self.create_settings_keyboard(settings))
                    return
                
                elif action == 'settings_back':
                    settings = self.get_chat_settings(chat_id)
                    self.send_message("⚙️ **Настройки чата**\n\nВыберите параметр для изменения:", chat_id, keyboard=self.create_settings_keyboard(settings))
                    return
                
                elif action == 'settings_close':
                    self.send_message("⚙️ Настройки закрыты.", chat_id)
                    return
                
                # Система рабов
                elif action == 'slave_collect':
                    self.send_message(self.handle_slave_system(user_id, 'collect'), chat_id)
                    return
                elif action == 'slave_chains':
                    self.send_message(self.handle_slave_system(user_id, 'chains'), chat_id)
                    return
                elif action == 'slave_upgrade':
                    self.send_message(self.handle_slave_system(user_id, 'upgrade'), chat_id)
                    return
                elif action == 'slave_buyout':
                    self.send_message(self.handle_slave_system(user_id, 'buyout'), chat_id)
                    return
                
                # Вайп система
                elif action == 'wipe_money':
                    if hasattr(self, 'waiting_for_wipe_user') and self.waiting_for_wipe_user:
                        msg = self.wipe_money(user_id, self.waiting_for_wipe_user)
                        self.waiting_for_wipe_user = None
                    else:
                        msg = self.wipe_money(user_id)
                    self.send_message(msg, chat_id)
                    return
                elif action == 'wipe_warns':
                    if hasattr(self, 'waiting_for_wipe_user') and self.waiting_for_wipe_user:
                        msg = self.wipe_warns(user_id, self.waiting_for_wipe_user)
                        self.waiting_for_wipe_user = None
                    else:
                        msg = self.wipe_warns(user_id)
                    self.send_message(msg, chat_id)
                    return
                elif action == 'wipe_mutes':
                    if hasattr(self, 'waiting_for_wipe_user') and self.waiting_for_wipe_user:
                        msg = self.wipe_mutes(user_id, self.waiting_for_wipe_user)
                        self.waiting_for_wipe_user = None
                    else:
                        msg = self.wipe_mutes(user_id)
                    self.send_message(msg, chat_id)
                    return
                elif action == 'wipe_bans':
                    if hasattr(self, 'waiting_for_wipe_user') and self.waiting_for_wipe_user:
                        msg = self.wipe_bans(user_id, self.waiting_for_wipe_user)
                        self.waiting_for_wipe_user = None
                    else:
                        msg = self.wipe_bans(user_id)
                    self.send_message(msg, chat_id)
                    return
                elif action == 'wipe_vip':
                    if hasattr(self, 'waiting_for_wipe_user') and self.waiting_for_wipe_user:
                        msg = self.wipe_vip(user_id, self.waiting_for_wipe_user)
                        self.waiting_for_wipe_user = None
                    else:
                        msg = self.wipe_vip(user_id)
                    self.send_message(msg, chat_id)
                    return
                elif action == 'wipe_back':
                    self.send_message("⚠️ **Вайп система**\n\nВыберите что обнулить:", chat_id, keyboard=self.create_wipe_keyboard())
                    return
                
                # Системная информация
                elif action == 'sysinfo_opt':
                    option = data.get('option', 0)
                    if user_id in self.sysinfo_target:
                        target_id = self.sysinfo_target[user_id]
                        if option == 1:
                            info = self.sysinfo_user(user_id, target_id)
                        elif option == 2:
                            info = self.get_user_chats(user_id, target_id)
                        elif option == 3:
                            info = self.get_owner_chats(user_id, target_id)
                        elif option == 4:
                            info = self.get_sysinfo_help()
                        self.send_message(info, user_id=user_id)
                    return
                
                # Системный бан
                elif action == 'sysban_stage':
                    stage = data.get('stage')
                    self.send_message(f"Используйте: /sysban [id] {stage} [причина]", user_id=user_id)
                    return
                
                # Staff с никами
                elif action == 'staff_with_nicks':
                    staff = self.get_staff_list()
                    if staff:
                        staff_text = "👥 **Персонал (с никами):**\n━━━━━━━━━━━━━━━━━━\n"
                        for member in staff:
                            user = self.get_user(member['id'])
                            nickname = user[24] or member['name']
                            role_emoji = self.status_emojis.get(member['role'], '👤')
                            staff_text += f"{role_emoji} {self.get_user_link(member['id'])} - {member['role']}\n"
                        self.send_message(staff_text, chat_id)
                    else:
                        self.send_message("👥 Персонал отсутствует.", chat_id)
                    return
                
                # Обработка ожидания ID агента (отмена)
                elif action == 'agent_cancel':
                    if user_id in self.waiting_for_agent_id:
                        del self.waiting_for_agent_id[user_id]
                        if user_id in self.waiting_for_agent_expiry:
                            del self.waiting_for_agent_expiry[user_id]
                    self.send_message("❌ Настройка прав агента отменена.", user_id=user_id)
                    return
                
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга callback payload: {e}")


if __name__ == "__main__":
    GROUP_TOKEN = os.getenv("VK_TOKEN")
    GROUP_ID = os.getenv("VK_GROUP_ID")
    
    if not GROUP_TOKEN:
        print("❌ Ошибка: Переменная VK_TOKEN не найдена!")
        print("💡 Добавьте переменную окружения VK_TOKEN в настройках Bothost")
        exit(1)
    
    if not GROUP_ID:
        print("❌ Ошибка: Переменная VK_GROUP_ID не найдена!")
        print("💡 Добавьте переменную окружения VK_GROUP_ID в настройках Bothost")
        exit(1)
    
    GROUP_ID = int(GROUP_ID)
    
    print(f"✅ Бот запускается с ID группы: {GROUP_ID}")
    
    bot = VKChatManager(GROUP_TOKEN, GROUP_ID)
    bot.run()
