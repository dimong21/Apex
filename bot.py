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
import sys

class VKChatManager:
    def __init__(self, group_token, group_id):
        """Инициализация бота"""
        self.group_token = group_token
        self.group_id = group_id
        self.vk = vk_api.VkApi(token=group_token)
        self.longpoll = VkBotLongPoll(self.vk, group_id)
        self.vk_api = self.vk.get_api()
        
        # ========== СУПЕР-АДМИНЫ (имеют доступ ко всем командам) ==========
        self.super_admins = [
            771565937,  # Ваш ID - имеет доступ ко всему
        ]
        
        # Курсы валют
        self.exchange_rates = {
            'usd_to_rub': 90.0,
            'eur_to_rub': 98.0,
            'btc_to_usd': 60000,
            'btc_to_rub': 5400000,
        }
        
        # Настройки чатов по умолчанию
        self.default_chat_settings = {
            'kick_on_leave': False,  # Кикать при выходе
            'who_can_add': 'all',    # all, admins, owner
            'games_enabled': True,   # Включены ли игры
            'welcome_message': True,  # Приветственное сообщение
            'anti_flood': False,     # Антифлуд
            'max_messages_per_second': 5
        }
        
        # Инициализация базы данных
        self.init_database()
        
        # Загрузка конфигурации
        self.config = self.load_config()
        
        # Загрузка курсов валют
        self.load_exchange_rates()
        
        # Префиксы команд
        self.prefixes = ['/', '!', '.']
        
        # Временные хранилища
        self.waiting_for_agent_id = {}
        self.waiting_for_syslinks = {}
        self.sysinfo_target = {}
        self.waiting_for_union_id = {}
        
        # Руссификация команд (ОБНОВЛЕНА)
        self.commands = {
            # Основные команды
            'ban': ['/ban', '/бан', '!ban', '!бан', '.ban', '.бан'],
            'unban': ['/unban', '/разбан', '!unban', '!разбан', '.unban', '.разбан'],
            'mute': ['/mute', '/мут', '!mute', '!мут', '.mute', '.мут'],
            'unmute': ['/unmute', '/размут', '!unmute', '!размут', '.unmute', '.размут'],
            'warn': ['/warn', '/варн', '!warn', '!варн', '.warn', '.варн'],
            'kick': ['/kick', '/кик', '!kick', '!кик', '.kick', '.кик'],
            'ping': ['/ping', '/пинг', '!ping', '!пинг', '.ping', '.пинг'],
            'stats': ['/stats', '/статистика', '!stats', '!статистика', '.stats', '.статистика'],
            'balance': ['/balance', '/баланс', '!balance', '!баланс', '.balance', '.баланс'],
            'bonus': ['/bonus', '/бонус', '!bonus', '!бонус', '.bonus', '.бонус'],
            'transfer': ['/transfer', '/перевод', '!transfer', '!перевод', '.transfer', '.перевод'],
            'mine': ['/mine', '/майнинг', '!mine', '!майнинг', '.mine', '.майнинг'],
            'work': ['/work', '/работа', '!work', '!работа', '.work', '.работа'],
            'shop': ['/shop', '/магазин', '!shop', '!магазин', '.shop', '.магазин'],
            'buy': ['/buy', '/купить', '!buy', '!купить', '.buy', '.купить'],
            'vip': ['/vip', '/вип', '!vip', '!вип', '.vip', '.вип'],
            'staff': ['/staff', '/персонал', '!staff', '!персонал', '.staff', '.персонал'],
            'say': ['/say', '/скажи', '!say', '!скажи', '.say', '.скажи'],
            'start': ['/start', '/старт', '!start', '!старт', '.start', '.старт'],
            'help': ['/help', '/помощь', '!help', '!помощь', '.help', '.помощь'],
            'report': ['/report', '/репорт', '!report', '!репорт', '.report', '.репорт'],
            'slaves': ['/slaves', '/рабы', '!slaves', '!рабы', '.slaves', '.рабы'],
            'rates': ['/rates', '/курсы', '!rates', '!курсы', '.rates', '.курсы'],
            'settings': ['/settings', '/настройки', '!settings', '!настройки', '.settings', '.настройки'],
            
            # Управление ролями
            'roleslist': ['/roleslist', '/списокролей', '!roleslist', '!списокролей', '.roleslist', '.списокролей'],
            'setrole': ['/setrole', '/выдатьроль', '!setrole', '!выдатьроль', '.setrole', '.выдатьроль'],
            'addrole': ['/addrole', '/добавитьроль', '!addrole', '!добавитьроль', '.addrole', '.добавитьроль'],
            
            # Фильтры
            'filter': ['/filter', '/фильтр', '!filter', '!фильтр', '.filter', '.фильтр'],
            'invite': ['/invite', '/пригласить', '!invite', '!пригласить', '.invite', '.пригласить'],
            'chat_info': ['/chatinfo', '/инфобеседы', '!chatinfo', '!инфобеседы', '.chatinfo', '.инфобеседы'],
            
            # Агентские команды (скрытые, доступ через /agent)
            'agent': ['/agent', '/агент', '!agent', '!агент', '.agent', '.агент'],
            'reports': ['/reports', '/репорты', '!reports', '!репорты', '.reports', '.репорты'],
            'botadmins': ['/botadmins', '/ботадмины', '!botadmins', '!ботадмины', '.botadmins', '.ботадмины'],
            'mutereports': ['/mutereports', '/мутрепорты', '!mutereports', '!мутрепорты', '.mutereports', '.мутрепорты'],
            'unmutereports': ['/unmutereports', '/размутрепорты', '!unmutereports', '!размутрепорты', '.unmutereports', '.размутрепорты'],
            'givemoney': ['/givemoney', '/выдатьденьги', '!givemoney', '!выдатьденьги', '.givemoney', '.выдатьденьги'],
            'givevip': ['/givevip', '/выдатьвип', '!givevip', '!выдатьвип', '.givevip', '.выдатьвип'],
            'sysban': ['/sysban', '/системныйбан', '!sysban', '!системныйбан', '.sysban', '.системныйбан'],
            'sysunban': ['/sysunban', '/системныйразбан', '!sysunban', '!системныйразбан', '.sysunban', '.системныйразбан'],
            'sysrole': ['/sysrole', '/системнаяроль', '!sysrole', '!системнаяроль', '.sysrole', '.системнаяроль'],
            'sysinfo': ['/sysinfo', '/системнаяинформация', '!sysinfo', '!системнаяинформация', '.sysinfo', '.системнаяинформация'],
            'snick': ['/snick', '/сетник', '!snick', '!сетник', '.snick', '.сетник'],
            'rnick': ['/rnick', '/делник', '!rnick', '!делник', '.rnick', '.делник'],
            'delkick': ['/delkick', '/делкик', '!delkick', '!делкик', '.delkick', '.делкик'],
            'nonames': ['/nonames', '/безников', '!nonames', '!безников', '.nonames', '.безников'],
            'ponicku': ['/ponicku', '/понику', '!ponicku', '!понику', '.ponicku', '.понику'],
            
            # Секретные команды (доступ через /agent)
            'bhelp': ['/bhelp', '/бхелп', '!bhelp', '!бхелп', '.bhelp', '.бхелп'],
            'sysrestart': ['/sysrestart', '/системныйрестарт', '!sysrestart', '!системныйрестарт'],
            'syslinks': ['/syslinks', '/ссылки', '!syslinks', '!ссылки'],
            'logs': ['/logs', '/логи', '!logs', '!логи'],
            'wipe': ['/wipe', '/вайп', '!wipe', '!вайп'],
            'wipeuser': ['/wipeuser', '/вайпюзера', '!wipeuser', '!вайпюзера'],
            
            # Система объединений
            'gkick': ['/gkick', '/гкик', '!gkick', '!гкик'],
            'gban': ['/gban', '/гбан', '!gban', '!гбан'],
            'gmute': ['/gmute', '/гмут', '!gmute', '!гмут'],
            'grole': ['/grole', '/гроль', '!grole', '!гроль'],
            
            # Редактирование команд
            'editcmd': ['/editcmd', '/редактироватькоманду', '!editcmd', '!редактироватькоманду', '.editcmd', '.редактироватькоманду'],
            'setrate': ['/setrate', '/установитькурс', '!setrate', '!установитькурс', '.setrate', '.установитькурс'],
        }
        
        # Цены в магазине (ОБНОВЛЕНЫ)
        self.shop_items = {
            'vip1': {
                'name': '🌟 VIP статус I уровня', 
                'price': 5000, 
                'type': 'vip', 
                'level': 1,
                'benefits': {
                    'max_chats': 50,
                    'max_unions': 30,
                    'daily_say': 50
                }
            },
            'vip2': {
                'name': '💎 VIP статус II уровня', 
                'price': 15000, 
                'type': 'vip', 
                'level': 2,
                'benefits': {
                    'max_chats': 120,
                    'max_unions': 70,
                    'daily_say': 120
                }
            },
            'vip3': {
                'name': '👑 VIP статус III уровня', 
                'price': 35000, 
                'type': 'vip', 
                'level': 3,
                'benefits': {
                    'max_chats': 250,
                    'max_unions': 150,
                    'daily_say': 300
                }
            },
            'bitcoin_miner': {'name': '⛏️ Майнер биткойнов', 'price': 5000, 'type': 'item', 'value': 'miner', 'hourly': 0.5},
        }
        
        # Магазин с инлайн кнопками
        self.inline_shop = {
            'phones': {
                'iPhone 15 Pro': 999,
                'iPhone 15 Pro Max': 1199,
                'Samsung Galaxy S24 Ultra': 1299,
                'Samsung Galaxy S24': 899,
                'Google Pixel 8 Pro': 999,
                'Google Pixel 8': 699,
                'Xiaomi 14 Ultra': 899,
                'Xiaomi 14 Pro': 699,
                'OnePlus 12': 749,
                'Nothing Phone 2': 599
            },
            'houses': {
                '🏠 Квартира-студия': 50000,
                '🏡 1-комнатная квартира': 100000,
                '🏘️ 2-комнатная квартира': 200000,
                '🏠 Загородный дом': 500000,
                '🏢 Пентхаус': 1000000,
                '🏰 Особняк': 5000000,
                '🏝️ Вилла на острове': 10000000
            },
            'clothes': {
                '👕 Футболка': 50,
                '👖 Джинсы': 100,
                '👔 Костюм': 500,
                '👟 Кроссовки': 150,
                '🧥 Пальто': 300,
                '🧢 Кепка': 30,
                '🧣 Шарф': 40,
                '🧤 Перчатки': 35,
                '👗 Платье': 250,
                '👘 Халат': 80
            },
            'items': {
                '💍 Кольцо': 200,
                '⌚ Часы': 500,
                '💎 Бриллиант': 1000,
                '🎮 Игровая приставка': 400,
                '📚 Книга': 30,
                '💻 Ноутбук': 800,
                '📱 Смартфон': 600,
                '🎧 Наушники': 100,
                '📷 Фотоаппарат': 450,
                '🚗 Машина': 5000
            }
        }
        
        # Эмодзи для статусов
        self.status_emojis = {
            'user': '👤',
            'moderator': '🛡️',
            'admin': '⚡',
            'owner': '👑'
        }
        
        # Подозрительные логи
        self.suspicious_logs = []
        
        print("🤖 Бот успешно запущен!")
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def is_super_admin(self, user_id):
        """Проверка, является ли пользователь супер-админом (имеет доступ ко всем командам)"""
        return user_id in self.super_admins
    
    def has_command_access(self, user_id, command, chat_id=None):
        """Проверка доступа к команде (супер-админ имеет доступ ко всему)"""
        if self.is_super_admin(user_id):
            return True
        return self.check_permission(user_id, command)
    
    def load_exchange_rates(self):
        """Загрузка курсов валют из конфига"""
        try:
            with open('exchange_rates.json', 'r', encoding='utf-8') as f:
                saved_rates = json.load(f)
                self.exchange_rates.update(saved_rates)
        except:
            self.save_exchange_rates()
    
    def save_exchange_rates(self):
        """Сохранение курсов валют"""
        try:
            with open('exchange_rates.json', 'w', encoding='utf-8') as f:
                json.dump(self.exchange_rates, f, ensure_ascii=False, indent=4)
        except:
            pass
    
    def get_user_link(self, user_id):
        """Получение ссылки на пользователя с именем"""
        user = self.get_user(user_id)
        nickname = user[24] or user[1]
        return f"[id{user_id}|{nickname}]"
    
    def get_user_name(self, user_id):
        """Получение имени пользователя по ID"""
        user = self.get_user(user_id)
        return user[24] or user[1]
    
    def extract_user_id(self, text, reply_message=None):
        """Извлечение ID пользователя из различных форматов упоминаний"""
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
    
    def get_chat_settings(self, chat_id):
        """Получение настроек чата"""
        self.cursor.execute('SELECT settings FROM chats WHERE chat_id = ?', (chat_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            try:
                return json.loads(result[0])
            except:
                pass
        return self.default_chat_settings.copy()
    
    def save_chat_settings(self, chat_id, settings):
        """Сохранение настроек чата"""
        self.cursor.execute('UPDATE chats SET settings = ? WHERE chat_id = ?', 
                           (json.dumps(settings, ensure_ascii=False), chat_id))
        self.conn.commit()
    
    # ==================== ИНИЦИАЛИЗАЦИЯ БД ====================
    
    def init_database(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect('vk_bot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                role TEXT DEFAULT 'user',
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
                created_at TEXT,
                settings TEXT DEFAULT '{}'
            )
        ''')
        
        # Таблица бесед в объединениях
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS union_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                union_id INTEGER,
                chat_id INTEGER,
                added_at TEXT,
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
            ('user', '{}', 0),
            ('moderator', '{"ban": true, "mute": true, "warn": true, "kick": true, "filter": true}', 40),
            ('admin', '{"ban": true, "mute": true, "warn": true, "kick": true, "setrole": true, "filter": true, "addrole": true}', 50),
            ('owner', '{"*": true}', 100)
        ]
        
        for role in default_roles:
            self.cursor.execute('INSERT OR IGNORE INTO roles (role_name, permissions, priority) VALUES (?, ?, ?)', role)
        
        self.conn.commit()
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            default_config = {
                'chat_id': 0,
                'mute_time': 5,
                'warning_limit': 3,
                'work_reward': [50, 200],
                'mine_reward': [0.1, 0.5],
                'bonus_reward': [100, 500],
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
    
    # ==================== КЛАВИАТУРЫ ====================
    
    def create_callback_keyboard(self, buttons):
        """Создание callback-клавиатуры (инлайн с обработкой)"""
        keyboard = {
            "inline": True,
            "buttons": []
        }
        
        row = []
        for button in buttons:
            row.append({
                "action": {
                    "type": "callback",
                    "label": button['label'],
                    "payload": button.get('payload', {})
                },
                "color": button.get('color', 'primary')
            })
            
            if len(row) == 2 or button == buttons[-1]:
                keyboard['buttons'].append(row)
                row = []
        
        return json.dumps(keyboard, ensure_ascii=False)
    
    def create_shop_category_keyboard(self):
        """Создание клавиатуры для категорий магазина"""
        buttons = [
            {'label': '📱 Телефоны', 'payload': json.dumps({'action': 'shop_category', 'category': 'phones'}), 'color': 'primary'},
            {'label': '🏠 Дома', 'payload': json.dumps({'action': 'shop_category', 'category': 'houses'}), 'color': 'primary'},
            {'label': '👕 Одежда', 'payload': json.dumps({'action': 'shop_category', 'category': 'clothes'}), 'color': 'primary'},
            {'label': '🎁 Вещи', 'payload': json.dumps({'action': 'shop_category', 'category': 'items'}), 'color': 'primary'},
            {'label': '💎 VIP Статусы', 'payload': json.dumps({'action': 'shop_category', 'category': 'vip'}), 'color': 'positive'},
            {'label': '⛏️ Майнер BTC', 'payload': json.dumps({'action': 'buy_miner'}), 'color': 'primary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_shop_items_keyboard(self, category, items):
        """Создание клавиатуры для товаров в категории"""
        buttons = []
        for item_name, price in items.items():
            buttons.append({
                'label': f"{item_name} - {price}$",
                'payload': json.dumps({'action': 'buy_item', 'item': item_name}),
                'color': 'primary'
            })
        
        buttons.append({
            'label': '🔙 Назад в магазин',
            'payload': json.dumps({'action': 'shop_back'}),
            'color': 'secondary'
        })
        
        return self.create_callback_keyboard(buttons)
    
    def create_vip_keyboard(self):
        """Создание клавиатуры для выбора VIP статуса"""
        buttons = [
            {'label': '🌟 VIP I - 5000₽', 'payload': json.dumps({'action': 'buy_vip', 'level': 1}), 'color': 'positive'},
            {'label': '💎 VIP II - 15000₽', 'payload': json.dumps({'action': 'buy_vip', 'level': 2}), 'color': 'positive'},
            {'label': '👑 VIP III - 35000₽', 'payload': json.dumps({'action': 'buy_vip', 'level': 3}), 'color': 'positive'},
            {'label': '🔙 Назад в магазин', 'payload': json.dumps({'action': 'shop_back'}), 'color': 'secondary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_vip_info_keyboard(self, level, price):
        """Создание клавиатуры с информацией о VIP и кнопкой покупки"""
        buttons = [
            {'label': '💎 Купить', 'payload': json.dumps({'action': 'confirm_buy_vip', 'level': level}), 'color': 'positive'},
            {'label': '🔙 Назад', 'payload': json.dumps({'action': 'vip_back'}), 'color': 'secondary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_ping_keyboard(self):
        """Создание клавиатуры для /ping с кнопкой обновления"""
        buttons = [
            {'label': '🔄 Обновить', 'payload': json.dumps({'action': 'ping_refresh'}), 'color': 'primary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_botadmins_keyboard(self):
        """Создание клавиатуры для /botadmins"""
        agents = self.get_all_agents()
        buttons = []
        
        for agent_id, name, agent_number, tickets, rating in agents:
            buttons.append({
                'label': f"#{agent_number} - {self.get_user_name(agent_id)}",
                'payload': json.dumps({'action': 'show_agent_stats', 'agent_id': agent_id}),
                'color': 'primary'
            })
        
        return self.create_callback_keyboard(buttons)
    
    def create_agent_permissions_keyboard(self, target_id, current_permissions):
        """Создание клавиатуры для управления правами агента"""
        buttons = []
        
        perm_names = {
            'reports': '📋 Доступ к /reports',
            'agent': '👑 Управление агентами (/agent)',
            'givemoney': '💰 Выдача денег',
            'givevip': '💎 Выдача VIP',
            'sysban': '🔨 Системный бан',
            'sysrole': '⭐ Системная роль',
            'sysinfo': 'ℹ️ Системная информация',
            'botadmins': '👥 Список агентов',
            'snick': '📝 Установка ника',
            'rnick': '🗑️ Удаление ника',
            'delkick': '🚪 Кик забаненных',
            'mutereports': '🔇 Мут репортов',
            'unmutereports': '🔊 Размут репортов',
            'bhelp': '📖 Скрытые команды',
            'sysrestart': '🔄 Рестарт бота',
            'syslinks': '🔗 Ссылки на беседы',
            'logs': '📜 Подозрительные логи'
        }
        
        for perm_key, perm_name in perm_names.items():
            status = "✅" if current_permissions.get(perm_key, False) else "❌"
            buttons.append({
                'label': f"{status} {perm_name}",
                'payload': json.dumps({
                    'action': 'agent_toggle_perm',
                    'target_id': target_id,
                    'permission': perm_key,
                    'current': current_permissions.get(perm_key, False)
                }),
                'color': 'primary'
            })
        
        buttons.append({
            'label': '🔙 Назад',
            'payload': json.dumps({'action': 'agent_back'}),
            'color': 'secondary'
        })
        
        return self.create_callback_keyboard(buttons)
    
    def create_settings_keyboard(self, settings):
        """Создание клавиатуры для настроек чата"""
        buttons = [
            {'label': f"{'✅' if settings['kick_on_leave'] else '❌'} Кикать при выходе", 
             'payload': json.dumps({'action': 'settings_toggle', 'setting': 'kick_on_leave'}), 'color': 'primary'},
            {'label': f"👥 Кто может добавлять: {settings['who_can_add']}", 
             'payload': json.dumps({'action': 'settings_change', 'setting': 'who_can_add'}), 'color': 'primary'},
            {'label': f"{'✅' if settings['games_enabled'] else '❌'} Игры", 
             'payload': json.dumps({'action': 'settings_toggle', 'setting': 'games_enabled'}), 'color': 'primary'},
            {'label': f"{'✅' if settings['welcome_message'] else '❌'} Приветствие", 
             'payload': json.dumps({'action': 'settings_toggle', 'setting': 'welcome_message'}), 'color': 'primary'},
            {'label': f"{'✅' if settings['anti_flood'] else '❌'} Антифлуд", 
             'payload': json.dumps({'action': 'settings_toggle', 'setting': 'anti_flood'}), 'color': 'primary'},
            {'label': '🔙 Закрыть', 'payload': json.dumps({'action': 'settings_close'}), 'color': 'secondary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_slave_keyboard(self):
        """Создание клавиатуры для системы рабов"""
        buttons = [
            {'label': '💰 Собрать прибыль', 'payload': json.dumps({'action': 'slave_collect'}), 'color': 'positive'},
            {'label': '🔗 Надеть цепи', 'payload': json.dumps({'action': 'slave_chains'}), 'color': 'primary'},
            {'label': '⬆️ Прокачать рабов', 'payload': json.dumps({'action': 'slave_upgrade'}), 'color': 'primary'},
            {'label': '🆓 Выкупиться', 'payload': json.dumps({'action': 'slave_buyout'}), 'color': 'negative'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_wipe_keyboard(self):
        """Создание клавиатуры для вайпа"""
        buttons = [
            {'label': '💰 Вайп денег', 'payload': json.dumps({'action': 'wipe_money'}), 'color': 'negative'},
            {'label': '⚠️ Вайп варнов', 'payload': json.dumps({'action': 'wipe_warns'}), 'color': 'negative'},
            {'label': '🔇 Вайп мутов', 'payload': json.dumps({'action': 'wipe_mutes'}), 'color': 'negative'},
            {'label': '⛔ Вайп банов', 'payload': json.dumps({'action': 'wipe_bans'}), 'color': 'negative'},
            {'label': '💎 Вайп VIP', 'payload': json.dumps({'action': 'wipe_vip'}), 'color': 'negative'},
            {'label': '🔙 Назад', 'payload': json.dumps({'action': 'wipe_back'}), 'color': 'secondary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_kick_keyboard(self, user_id):
        """Создание клавиатуры для кика пользователя"""
        buttons = [
            {'label': '🚪 Кикнуть', 'payload': json.dumps({'action': 'kick_user', 'target_id': user_id}), 'color': 'primary'},
            {'label': '⛔ Забанить', 'payload': json.dumps({'action': 'ban_user', 'target_id': user_id}), 'color': 'negative'},
            {'label': '🔇 Замутить', 'payload': json.dumps({'action': 'mute_user', 'target_id': user_id}), 'color': 'primary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    def create_who_can_add_keyboard(self):
        """Создание клавиатуры для выбора кто может добавлять"""
        buttons = [
            {'label': '👥 Все', 'payload': json.dumps({'action': 'settings_set', 'setting': 'who_can_add', 'value': 'all'}), 'color': 'primary'},
            {'label': '🛡️ Администраторы', 'payload': json.dumps({'action': 'settings_set', 'setting': 'who_can_add', 'value': 'admins'}), 'color': 'primary'},
            {'label': '👑 Владелец', 'payload': json.dumps({'action': 'settings_set', 'setting': 'who_can_add', 'value': 'owner'}), 'color': 'positive'},
            {'label': '🔙 Назад', 'payload': json.dumps({'action': 'settings_back'}), 'color': 'secondary'}
        ]
        return self.create_callback_keyboard(buttons)
    
    # ==================== ОСНОВНЫЕ МЕТОДЫ ====================
    
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
                self.cursor.execute('''
                    UPDATE chats 
                    SET is_active = 1, activated_at = ?, owner_id = ?
                    WHERE chat_id = ?
                ''', (current_time, user_id, chat_id))
            else:
                self.cursor.execute('''
                    INSERT INTO chats (chat_id, chat_name, owner_id, is_active, activated_at, created_at, settings)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (chat_id, f"Chat_{chat_id}", user_id, 1, current_time, current_time, json.dumps(self.default_chat_settings)))
            
            self.cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', ('owner', user_id))
            self.conn.commit()
            
            welcome_msg = (
                "✅ **Беседа активирована!**\n"
                f"👑 Владелец беседы: {self.get_user_link(user_id)}\n"
                "🎉 Удачного использования бота!\n\n"
                "📋 **Список команд:** /help\n"
                "⚙️ **Настройки чата:** /settings\n"
                "❓ **Вопросы по боту:** /report"
            )
            
            self.send_message(welcome_msg, chat_id)
            return True, "✅ Беседа успешно активирована!"
            
        except Exception as e:
            print(f"❌ Ошибка активации: {e}")
            error_msg = f"❌ Ошибка активации: {str(e)[:100]}"
            self.send_message(error_msg, chat_id)
            return False, error_msg
    
    def send_message(self, message, chat_id=None, user_id=None, keyboard=None):
        try:
            params = {
                'random_id': random.randint(1, 1000000),
                'message': message
            }
            
            if user_id:
                params['user_id'] = user_id
            elif chat_id:
                params['chat_id'] = chat_id
            
            if keyboard:
                params['keyboard'] = keyboard
            
            self.vk_api.messages.send(**params)
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            return False
    
    def get_or_create_chat(self, chat_id):
        self.cursor.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
        chat = self.cursor.fetchone()
        
        if not chat:
            try:
                current_time = datetime.now().isoformat()
                self.cursor.execute('''
                    INSERT INTO chats (chat_id, chat_name, owner_id, is_active, created_at, settings)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (chat_id, f"Chat_{chat_id}", 0, 0, current_time, json.dumps(self.default_chat_settings)))
                self.conn.commit()
            except Exception as e:
                print(f"⚠️ Ошибка создания беседы в БД: {e}")
            
            return self.get_or_create_chat(chat_id)
        
        return chat
    
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
            self.cursor.execute('''
                INSERT INTO users (user_id, name, join_date, messages_count, say_used_today, last_say_reset, miners_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, current_time, 0, 0, current_time, 0))
            self.conn.commit()
            return self.get_user(user_id)
        
        return user
    
    def get_user_stats_detailed(self, user_id, chat_id=None):
        user = self.get_user(user_id)
        
        inviter_info = ""
        if chat_id:
            self.cursor.execute('''
                SELECT inviter_id FROM invites 
                WHERE chat_id = ? AND user_id = ?
                ORDER BY invited_at DESC LIMIT 1
            ''', (chat_id, user_id))
            inviter = self.cursor.fetchone()
            
            if inviter and inviter[0]:
                inviter_info = f"👫 Пригласил(а): {self.get_user_link(inviter[0])}"
        
        if user[20] == 1:
            agent_number = user[21] or 0
            tickets_processed = user[22] or 0
            avg_rating = user[23] or 0
            
            stats = (
                f"👑 **Агент поддержки №{agent_number}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔧 Рассмотрено тикетов: {tickets_processed}\n"
                f"🅰️ Средняя оценка ответов: {avg_rating:.1f}/5 ⭐\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
            )
        else:
            stats = f"🔍 Информация о пользователе:\n━━━━━━━━━━━━━━━━━━━━━━\n"
        
        base_role = user[2]
        if base_role.startswith('vip'):
            base_role = 'user'
        
        status_emoji = self.status_emojis.get(base_role, '👤')
        status_text = {
            'user': 'Пользователь',
            'moderator': 'Модератор',
            'admin': 'Администратор',
            'owner': 'Владелец'
        }.get(base_role, 'Пользователь')
        
        stats += f"{status_emoji} Статус: {status_text}\n"
        stats += f"⚠ Предупреждений: {user[10]}/{self.config['warning_limit']}\n"
        
        nickname = user[24] or user[1]
        stats += f"📄 Никнейм: {nickname}\n"
        
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
            vip_names = {
                1: '🌟 VIP I уровня',
                2: '💎 VIP II уровня',
                3: '👑 VIP III уровня'
            }
            vip_display_name = vip_names.get(user[3], f'VIP {user[3]} уровня')
            stats += f"💎 VIP статус: {vip_display_name}\n"
            if user[4]:
                try:
                    vip_until = datetime.fromisoformat(user[4])
                    stats += f"💎 Действует до: {vip_until.strftime('%d.%m.%Y %H:%M')}\n"
                except:
                    pass
        
        stats += f"✍ Сообщений отправлено: {user[17]}\n"
        stats += f"⛏️ Майнеров: {user[30] or 0}\n"
        
        if inviter_info:
            stats += f"{inviter_info}\n"
        
        stats += f"⚙ ID: {user_id}\n"
        
        return stats
    
    def get_vip_info(self, user_id):
        user = self.get_user(user_id)
        
        if user[3] == 0:
            return "❌ У вас нет VIP статуса! Используйте /shop для покупки."
        
        benefits, next_benefits = self.config['vip_benefits'].get(user[3], ({}, None))
        
        self.cursor.execute('SELECT COUNT(*) FROM unions WHERE owner_id = ?', (user_id,))
        unions_count = self.cursor.fetchone()[0]
        
        if user[19]:
            try:
                last_reset = datetime.fromisoformat(user[19])
                if datetime.now().date() > last_reset.date():
                    self.cursor.execute('UPDATE users SET say_used_today = 0, last_say_reset = ? WHERE user_id = ?', 
                                      (datetime.now().isoformat(), user_id))
                    self.conn.commit()
                    say_used = 0
                else:
                    say_used = user[18] if user[18] else 0
            except:
                say_used = 0
        else:
            say_used = 0
        
        vip_until = None
        if user[4]:
            try:
                vip_until = datetime.fromisoformat(user[4])
            except:
                pass
        
        vip_names = {1: '🌟 VIP I уровня', 2: '💎 VIP II уровня', 3: '👑 VIP III уровня'}
        vip_display_name = vip_names.get(user[3], f'VIP {user[3]} уровня')
        
        info = f"✨ **{vip_display_name}**\n"
        info += f"💎 Уровень: {user[3]}\n\n"
        info += f"📊 **Ваши возможности:**\n"
        info += f"━━━━━━━━━━━━━━━━━━\n"
        info += f"🏢 Можно создать объединений: {benefits['max_unions'] - unions_count}/{benefits['max_unions']}\n"
        info += f"💬 В каждое объединение можно добавить: {benefits['max_chats']} бесед\n"
        info += f"📢 Команд !скажи на сегодня: {say_used}/{benefits['daily_say']}\n\n"
        
        if next_benefits:
            info += f"🔮 **Следующий уровень VIP {user[3] + 1}:**\n"
            info += f"💬 {next_benefits['max_chats']} бесед, "
            info += f"🏢 {next_benefits['max_unions']} объединений, "
            info += f"📢 {next_benefits['daily_say']} команд !скажи\n\n"
        
        if vip_until:
            info += f"⏰ Статус действует до: {vip_until.strftime('%d.%m.%Y %H:%M')}"
        
        return info
    
    def get_staff_list(self):
        staff_roles = ['moderator', 'admin', 'owner']
        staff_list = []
        
        for role in staff_roles:
            self.cursor.execute('SELECT user_id, name FROM users WHERE role = ?', (role,))
            users = self.cursor.fetchall()
            
            for user_id, name in users:
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
                               (role_name, json.dumps({}), priority))
            self.conn.commit()
            self.status_emojis[role_name] = '👤'
            return True, f"✅ Роль '{role_name}' создана! Приоритет: {priority}"
        except sqlite3.IntegrityError:
            return False, f"❌ Роль '{role_name}' уже существует!"
    
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
                required_role = 'moderator'
                required_priority = 40
            else:
                required_role = 'user'
                required_priority = 0
        
        self.cursor.execute('SELECT priority FROM roles WHERE role_name = ?', (role,))
        user_priority = self.cursor.fetchone()
        
        if not user_priority:
            return False
        
        return user_priority[0] >= required_priority
    
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
        vip_key = f'vip{level}'
        
        if vip_key not in self.shop_items:
            return False, "❌ Такого VIP статуса не существует!"
        
        price = self.shop_items[vip_key]['price']
        
        if user[7] >= price:
            self.cursor.execute('UPDATE users SET rubles = rubles - ? WHERE user_id = ?', (price, user_id))
            vip_until = (datetime.now() + timedelta(days=30)).isoformat()
            role = f'vip{level}'
            self.cursor.execute('UPDATE users SET vip_level = ?, vip_until = ?, role = ? WHERE user_id = ?',
                               (level, vip_until, role, user_id))
            self.conn.commit()
            return True, f"✅ Поздравляем! Вы приобрели {self.shop_items[vip_key]['name']} на 30 дней!"
        
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
            return False, "❌ Неверная валюта! Доступны: rub, usd, eur, btc"
        
        idx, name = currency_map[currency]
        
        if user[idx] < amount:
            return False, f"❌ Недостаточно средств!"
        
        self.cursor.execute(f'UPDATE users SET {name} = {name} - ? WHERE user_id = ?', (amount, user_id))
        self.cursor.execute(f'UPDATE users SET {name} = {name} + ? WHERE user_id = ?', (amount, target_id))
        self.conn.commit()
        
        self.log_action(user_id, 'transfer', target_id, f"{amount} {currency.upper()}")
        return True, f"✅ Переведено {amount} {currency.upper()} пользователю {self.get_user_link(target_id)}"
    
    # ==================== МОДЕРАЦИЯ ====================
    
    def ban_user(self, user_id, admin_id, chat_id, reason=None):
        try:
            self.vk_api.messages.removeChatUser(chat_id=chat_id, user_id=user_id)
            
            self.cursor.execute('UPDATE users SET role = "banned" WHERE user_id = ?', (user_id,))
            self.conn.commit()
            
            self.log_action(chat_id, admin_id, 'ban', user_id, reason)
            
            admin_name = self.get_user_link(admin_id)
            user_name = self.get_user_link(user_id)
            
            msg = f"⛔ Пользователь {user_name} забанен администратором {admin_name}"
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
        
        self.cursor.execute('''
            UPDATE users 
            SET is_muted = 1, mute_until = ?
            WHERE user_id = ?
        ''', (mute_until.isoformat(), user_id))
        self.conn.commit()
        
        self.log_action(chat_id, admin_id, 'mute', user_id, f"{minutes} минут")
        
        admin_name = self.get_user_link(admin_id)
        user_name = self.get_user_link(user_id)
        
        self.send_message(f"🔇 Пользователю {user_name} выдан мут на {minutes} минут от {admin_name}", chat_id)
        
        threading.Timer(minutes * 60, self.unmute_user, args=[user_id]).start()
    
    def unmute_user(self, user_id):
        self.cursor.execute('''
            UPDATE users 
            SET is_muted = 0, mute_until = NULL
            WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
    
    def add_warn(self, user_id, admin_id, chat_id, reason=None):
        user = self.get_user(user_id)
        warns = user[10] + 1
        
        self.cursor.execute('UPDATE users SET warns = ? WHERE user_id = ?', (warns, user_id))
        self.conn.commit()
        
        self.log_action(chat_id, admin_id, 'warn', user_id, reason)
        
        admin_name = self.get_user_link(admin_id) if admin_id != 0 else "Система"
        user_name = self.get_user_link(user_id)
        
        self.send_message(f"⚠️ Пользователю {user_name} выдан варн ({warns}/{self.config['warning_limit']}) от {admin_name}", chat_id)
        
        if reason:
            self.send_message(f"📝 Причина: {reason}", chat_id)
        
        if warns >= self.config['warning_limit']:
            self.mute_user(user_id, admin_id, chat_id, 30)
            self.cursor.execute('UPDATE users SET warns = 0 WHERE user_id = ?', (user_id,))
            self.conn.commit()
    
    def kick_user(self, admin_id, user_id, chat_id, reason=None):
        """Кик пользователя из беседы"""
        try:
            self.vk_api.messages.removeChatUser(chat_id=chat_id, user_id=user_id)
            
            self.log_action(chat_id, admin_id, 'kick', user_id, reason)
            
            admin_name = self.get_user_link(admin_id)
            user_name = self.get_user_link(user_id)
            
            msg = f"🚪 Пользователь {user_name} кикнут администратором {admin_name}"
            if reason:
                msg += f"\n📝 Причина: {reason}"
            
            self.send_message(msg, chat_id)
            return True
        except Exception as e:
            print(f"Ошибка кика: {e}")
            return False
    
    # ==================== СИСТЕМА ВАЙПА ====================
    
    def wipe_money(self, admin_id, user_id=None):
        """Вайп денег у пользователя или у всех"""
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
        """Вайп варнов у пользователя или у всех"""
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
        """Вайп мутов у пользователя или у всех"""
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
        """Вайп банов у пользователя или у всех"""
        if user_id:
            self.cursor.execute('UPDATE users SET role = "user", sysban_level = 0 WHERE user_id = ?', (user_id,))
            msg = f"⛔ Бан пользователя {self.get_user_link(user_id)} снят!"
        else:
            self.cursor.execute('UPDATE users SET role = "user", sysban_level = 0 WHERE role = "banned" OR sysban_level > 0')
            msg = "⛔ Баны всех пользователей сняты!"
        
        self.conn.commit()
        self.log_action(0, admin_id, 'wipe_bans', user_id or 0, "Вайп банов")
        return msg
    
    def wipe_vip(self, admin_id, user_id=None):
        """Вайп VIP статусов у пользователя или у всех"""
        if user_id:
            self.cursor.execute('UPDATE users SET vip_level = 0, vip_until = NULL, role = "user" WHERE user_id = ?', (user_id,))
            msg = f"💎 VIP статус пользователя {self.get_user_link(user_id)} снят!"
        else:
            self.cursor.execute('UPDATE users SET vip_level = 0, vip_until = NULL, role = "user" WHERE vip_level > 0')
            msg = "💎 VIP статусы всех пользователей сняты!"
        
        self.conn.commit()
        self.log_action(0, admin_id, 'wipe_vip', user_id or 0, "Вайп VIP")
        return msg
    
    # ==================== СИСТЕМА ОБЪЕДИНЕНИЙ ====================
    
    def get_or_create_union(self, user_id, union_name=None):
        """Получение или создание объединения"""
        self.cursor.execute('SELECT id, name FROM unions WHERE owner_id = ?', (user_id,))
        union = self.cursor.fetchone()
        
        if not union and union_name:
            current_time = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO unions (owner_id, name, created_at)
                VALUES (?, ?, ?)
            ''', (user_id, union_name, current_time))
            self.conn.commit()
            return self.cursor.lastrowid, union_name
        
        return union[0] if union else None, union[1] if union else None
    
    def add_chat_to_union(self, admin_id, chat_id, union_id=None):
        """Добавление беседы в объединение"""
        user = self.get_user(admin_id)
        union_id, union_name = self.get_or_create_union(admin_id)
        
        if not union_id:
            return False, "❌ У вас нет объединения! Создайте его через /гкопировать"
        
        self.cursor.execute('SELECT * FROM union_chats WHERE union_id = ? AND chat_id = ?', (union_id, chat_id))
        if self.cursor.fetchone():
            return False, "❌ Эта беседа уже в объединении!"
        
        self.cursor.execute('INSERT INTO union_chats (union_id, chat_id, added_at) VALUES (?, ?, ?)',
                           (union_id, chat_id, datetime.now().isoformat()))
        self.conn.commit()
        return True, f"✅ Беседа добавлена в объединение '{union_name}'!"
    
    def execute_global_command(self, admin_id, command, target_id=None, reason=None, minutes=None, role=None):
        """Выполнение глобальной команды во всех беседах объединения"""
        union_id, union_name = self.get_or_create_union(admin_id)
        
        if not union_id:
            return False, "❌ У вас нет объединения!"
        
        self.cursor.execute('SELECT chat_id FROM union_chats WHERE union_id = ?', (union_id,))
        chats = self.cursor.fetchall()
        
        if not chats:
            return False, "❌ В вашем объединении нет бесед!"
        
        results = []
        for chat in chats:
            chat_id = chat[0]
            try:
                if command == 'ban':
                    self.ban_user(target_id, admin_id, chat_id, reason)
                    results.append(f"Беседа {chat_id}: ✅")
                elif command == 'mute':
                    self.mute_user(target_id, admin_id, chat_id, minutes)
                    results.append(f"Беседа {chat_id}: ✅")
                elif command == 'kick':
                    self.kick_user(admin_id, target_id, chat_id, reason)
                    results.append(f"Беседа {chat_id}: ✅")
                elif command == 'role':
                    self.sysrole_user(admin_id, target_id, role, chat_id)
                    results.append(f"Беседа {chat_id}: ✅")
            except:
                results.append(f"Беседа {chat_id}: ❌")
        
        success_count = len([r for r in results if '✅' in r])
        return True, f"✅ Выполнено в {success_count}/{len(chats)} беседах"
    
    # ==================== АГЕНТСКАЯ СИСТЕМА ====================
    
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
        
        self.cursor.execute('''
            UPDATE users 
            SET is_agent = 1, agent_number = ?, tickets_processed = 0, avg_rating = 0, reports_muted = 0
            WHERE user_id = ?
        ''', (next_number, user_id))
        
        self.cursor.execute('''
            INSERT OR IGNORE INTO agent_permissions (user_id, permissions)
            VALUES (?, ?)
        ''', (user_id, json.dumps({
            'reports': True,
            'agent': False,
            'givemoney': False,
            'givevip': False,
            'sysban': False,
            'sysrole': False,
            'sysinfo': False,
            'botadmins': False,
            'snick': False,
            'rnick': False,
            'delkick': False,
            'mutereports': False,
            'unmutereports': False,
            'bhelp': False,
            'sysrestart': False,
            'syslinks': False,
            'logs': False
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
        
        if result:
            perms = json.loads(result[0])
        else:
            perms = {}
        
        perms[permission] = value
        
        self.cursor.execute('INSERT OR REPLACE INTO agent_permissions (user_id, permissions) VALUES (?, ?)',
                           (target_id, json.dumps(perms)))
        self.conn.commit()
        
        status = "включен" if value else "отключен"
        return True, f"✅ Доступ к {permission} {status} для агента #{self.get_agent_number(target_id)}!"
    
    def get_agent_info(self, admin_id, target_id):
        if not self.can_manage_agents(admin_id):
            return "❌ У вас нет прав для просмотра информации об агентах!"
        
        if not self.is_agent(target_id):
            return f"❌ Пользователь {self.get_user_link(target_id)} не является агентом!"
        
        self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (target_id,))
        result = self.cursor.fetchone()
        perms = json.loads(result[0]) if result else {}
        
        agent_number = self.get_agent_number(target_id)
        
        info = f"🔐 **Доступы агента #{agent_number}**\n"
        info += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        info += f"👤 {self.get_user_link(target_id)}\n\n"
        
        perm_names = {
            'reports': '📋 Доступ к /reports',
            'agent': '👑 Управление агентами',
            'givemoney': '💰 Выдача денег',
            'givevip': '💎 Выдача VIP',
            'sysban': '🔨 Системный бан',
            'sysrole': '⭐ Системная роль',
            'sysinfo': 'ℹ️ Системная информация',
            'botadmins': '👥 Список агентов',
            'snick': '📝 Установка ника',
            'rnick': '🗑️ Удаление ника',
            'delkick': '🚪 Кик забаненных',
            'mutereports': '🔇 Мут репортов',
            'unmutereports': '🔊 Размут репортов',
            'bhelp': '📖 Скрытые команды',
            'sysrestart': '🔄 Рестарт бота',
            'syslinks': '🔗 Ссылки на беседы',
            'logs': '📜 Подозрительные логи'
        }
        
        for perm_key, perm_name in perm_names.items():
            status = "✅" if perms.get(perm_key, False) else "❌"
            info += f"{status} {perm_name}\n"
        
        return info
    
    def get_all_agents(self):
        self.cursor.execute('''
            SELECT user_id, name, agent_number, tickets_processed, avg_rating 
            FROM users WHERE is_agent = 1 ORDER BY agent_number ASC
        ''')
        return self.cursor.fetchall()
    
    def get_bot_admins(self, admin_id):
        if not self.is_agent(admin_id):
            return "❌ Вы не являетесь агентом!"
        
        agents = self.get_all_agents()
        
        if not agents:
            return "📋 Список агентов пуст."
        
        info = "👑 **Список агентов поддержки**\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for agent_id, name, agent_number, tickets, rating in agents:
            self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (agent_id,))
            result = self.cursor.fetchone()
            perms = json.loads(result[0]) if result else {}
            
            if tickets >= 100:
                rank = "🏆 Элитный"
            elif tickets >= 50:
                rank = "⭐ Опытный"
            elif tickets >= 20:
                rank = "📈 Развивающийся"
            else:
                rank = "🆕 Новичок"
            
            info += f"**#{agent_number}** {rank}\n"
            info += f"👤 {self.get_user_link(agent_id)}\n"
            info += f"📊 Тикетов: {tickets} | Рейтинг: {rating:.1f}⭐\n"
            
            has_reports = "📝" if perms.get('reports', False) else "🔇"
            has_sysban = "🔨" if perms.get('sysban', False) else "⚙️"
            has_givemoney = "💰" if perms.get('givemoney', False) else "💵"
            
            info += f"Права: {has_reports} {has_sysban} {has_givemoney}\n"
            info += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return info
    
    def get_agent_stats_for_user(self, agent_id):
        user = self.get_user(agent_id)
        agent_number = user[21] or 0
        tickets = user[22] or 0
        rating = user[23] or 0
        
        info = f"👑 **Статистика агента #{agent_number}**\n"
        info += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        info += f"👤 {self.get_user_link(agent_id)}\n"
        info += f"📊 Всего обработано: {tickets}\n"
        info += f"⭐ Средний рейтинг: {rating:.1f}/5\n"
        
        return info
    
    def get_syslinks(self, admin_id, chat_id):
        """Получение ссылки на беседу"""
        if not self.has_agent_permission(admin_id, 'syslinks'):
            return "❌ У вас нет доступа к этой команде!"
        
        try:
            invite_link = self.vk_api.messages.getInviteLink(peer_id=2000000000 + chat_id)
            return f"🔗 Ссылка на беседу {chat_id}:\n{invite_link['link']}"
        except Exception as e:
            return f"❌ Ошибка получения ссылки: {str(e)}"
    
    def get_suspicious_logs(self, admin_id):
        """Получение подозрительных логов"""
        if not self.has_agent_permission(admin_id, 'logs'):
            return "❌ У вас нет доступа к этой команде!"
        
        if not self.suspicious_logs:
            return "📋 Подозрительные логи отсутствуют."
        
        info = "📜 **Подозрительные логи:**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for log in self.suspicious_logs[-20:]:
            info += f"🕐 {log.get('time', '')}\n"
            info += f"👤 Пользователь: {self.get_user_link(log.get('user', 0))}\n"
            info += f"🔧 Действие: {log.get('action', '')}\n"
            if log.get('target'):
                info += f"🎯 Цель: {self.get_user_link(log.get('target'))}\n"
            if log.get('reason'):
                info += f"📝 Причина: {log.get('reason')}\n"
            info += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return info
    
    def sysrestart(self, admin_id):
        """Рестарт бота"""
        if not self.has_agent_permission(admin_id, 'sysrestart'):
            return False, "❌ У вас нет доступа к этой команде!"
        
        self.log_action(admin_id, 'sysrestart', 0, "Рестарт бота")
        return True, "🔄 Бот перезапускается..."
    
    def get_bhelp(self, admin_id):
        """Получение списка скрытых команд"""
        if not self.has_agent_permission(admin_id, 'bhelp'):
            return "❌ У вас нет доступа к этой команде!"
        
        help_msg = (
            "🔐 **Скрытые команды (доступ через /agent):**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "• /bhelp - Этот список\n"
            "• /sysrestart - Перезапуск бота\n"
            "• /syslinks [id] - Ссылка на беседу\n"
            "• /logs - Подозрительные логи\n"
            "• /wipe - Вайп денег\n"
            "• /wipeuser [id] - Вайп пользователя\n"
            "• /gkick [id] - Глобальный кик\n"
            "• /gban [id] - Глобальный бан\n"
            "• /gmute [id] [минуты] - Глобальный мут\n"
            "• /grole [id] [роль] - Глобальная роль\n\n"
            "⚙️ **Система объединений:**\n"
            "• /гкопировать [название] - Создать объединение\n"
            "• /гкик [id] [причина] - Кик во всех беседах\n"
            "• /гбан [id] [причина] - Бан во всех беседах\n"
            "• /гмут [id] [минуты] - Мут во всех беседах\n"
            "• /гроль [id] [роль] - Выдать роль во всех беседах"
        )
        return help_msg
    
    # ==================== СИСТЕМА РЕПОРТОВ ====================
    
    def add_report(self, user_id, reporter_id, message, chat_id=None):
        user = self.get_user(user_id)
        
        if user[24] == 1:
            return False, "❌ Вы не можете отправлять репорты!"
        
        current_time = datetime.now().isoformat()
        self.cursor.execute('''
            INSERT INTO reports (user_id, reporter_id, message, chat_id, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, reporter_id, message, chat_id or 0, current_time))
        self.conn.commit()
        
        report_id = self.cursor.lastrowid
        self.notify_agents(report_id, user_id, message)
        return True, f"✅ Репорт #{report_id} отправлен!"
    
    def notify_agents(self, report_id, user_id, message):
        self.cursor.execute('''
            SELECT user_id FROM users WHERE is_agent = 1 AND reports_muted = 0
        ''')
        agents = self.cursor.fetchall()
        
        report_text = f"📝 **Новый репорт #{report_id}**\n"
        report_text += f"👤 От пользователя: {self.get_user_link(user_id)}\n"
        report_text += f"💬 Сообщение: {message[:200]}\n"
        report_text += f"🔧 Для ответа используйте /reports в ЛС бота"
        
        for agent in agents:
            self.send_message(report_text, user_id=agent[0])
    
    def get_open_reports(self):
        self.cursor.execute('SELECT * FROM reports WHERE status = "open" ORDER BY created_at DESC')
        return self.cursor.fetchall()
    
    def get_report_info(self, report_id):
        self.cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
        report = self.cursor.fetchone()
        
        if not report:
            return "❌ Репорт не найден!"
        
        report_id, user_id, reporter_id, message, chat_id, status, created_at, closed_at, closed_by, rating = report
        
        info = f"📋 **Репорт #{report_id}**\n"
        info += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        info += f"👤 Пользователь: {self.get_user_link(user_id)}\n"
        info += f"📝 Репорт от: {self.get_user_link(reporter_id)}\n"
        info += f"💬 Сообщение: {message}\n"
        info += f"📅 Создан: {created_at}\n"
        info += f"🔘 Статус: {'✅ Открыт' if status == 'open' else '❌ Закрыт'}\n"
        
        if status == 'closed':
            info += f"🔒 Закрыт: {closed_at}\n"
            info += f"👨‍💼 Кем: {self.get_user_link(closed_by)}\n"
            info += f"⭐ Оценка: {rating}/5\n"
        
        if chat_id and chat_id != 0:
            info += f"💬 Беседа: {chat_id}\n"
        
        return info
    
    def close_report(self, agent_id, report_id, rating=5):
        if not self.is_agent(agent_id):
            return False, "❌ Вы не являетесь агентом поддержки!"
        
        self.cursor.execute('SELECT * FROM reports WHERE id = ? AND status = "open"', (report_id,))
        report = self.cursor.fetchone()
        
        if not report:
            return False, "❌ Репорт не найден или уже закрыт!"
        
        current_time = datetime.now().isoformat()
        
        self.cursor.execute('''
            UPDATE reports SET status = 'closed', closed_at = ?, closed_by = ?, rating = ? WHERE id = ?
        ''', (current_time, agent_id, rating, report_id))
        
        self.cursor.execute('''
            UPDATE users 
            SET tickets_processed = tickets_processed + 1,
                avg_rating = (avg_rating * tickets_processed + ?) / (tickets_processed + 1)
            WHERE user_id = ?
        ''', (rating, agent_id))
        
        self.conn.commit()
        self.log_action(agent_id, 'close_report', report[1], f"Репорт #{report_id}, оценка {rating}")
        self.send_message(f"✅ Ваш репорт #{report_id} закрыт! Оценка: {rating}/5 ⭐", user_id=report[1])
        return True, f"✅ Репорт #{report_id} закрыт!"
    
    def get_agent_stats(self, agent_id):
        if not self.is_agent(agent_id):
            return "❌ Вы не являетесь агентом!"
        
        user = self.get_user(agent_id)
        agent_number = user[21] or 0
        tickets = user[22] or 0
        rating = user[23] or 0
        
        self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (agent_id,))
        result = self.cursor.fetchone()
        perms = json.loads(result[0]) if result else {}
        
        self.cursor.execute('SELECT COUNT(*) FROM reports WHERE closed_by = ?', (agent_id,))
        closed_by_me = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT AVG(rating) FROM reports WHERE closed_by = ? AND rating > 0', (agent_id,))
        my_avg_rating = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute('SELECT COUNT(*) FROM reports WHERE status = "open"')
        open_reports = self.cursor.fetchone()[0]
        
        stats = f"👑 **Статистика агента #{agent_number}**\n"
        stats += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        stats += f"📊 Всего обработано: {tickets}\n"
        stats += f"⭐ Средний рейтинг: {rating:.1f}/5\n"
        stats += f"🔧 Закрыто мной: {closed_by_me}\n"
        stats += f"🎯 Мой средний рейтинг: {my_avg_rating:.1f}/5\n"
        stats += f"📋 Открытых репортов: {open_reports}\n\n"
        
        stats += f"🔐 **Мои права:**\n"
        
        perm_names = {
            'reports': 'Доступ к репортам',
            'agent': 'Управление агентами',
            'givemoney': 'Выдача денег',
            'givevip': 'Выдача VIP',
            'sysban': 'Системный бан',
            'sysrole': 'Системная роль',
            'sysinfo': 'Системная информация',
            'botadmins': 'Список агентов',
            'bhelp': 'Скрытые команды',
            'sysrestart': 'Рестарт бота',
            'syslinks': 'Ссылки на беседы',
            'logs': 'Подозрительные логи'
        }
        
        for perm_key, perm_name in perm_names.items():
            status = "✅" if perms.get(perm_key, False) else "❌"
            stats += f"{status} {perm_name}\n"
        
        return stats
    
    def handle_reports_in_dm(self, user_id, text):
        if not self.is_agent(user_id):
            self.send_message("❌ У вас нет доступа к этой команде!", user_id=user_id)
            return
        
        parts = text.lower().split()
        
        if len(parts) >= 2:
            if parts[1] == 'list':
                reports = self.get_open_reports()
                if reports:
                    msg = "📋 **Открытые репорты:**\n━━━━━━━━━━━━━━━━━━\n"
                    for report in reports[:10]:
                        report_id, user_id_reporter, reporter_id, rep_message, chat_id, status, created_at, closed_at, closed_by, rating = report
                        msg += f"**#{report_id}** | от {self.get_user_link(user_id_reporter)}\n"
                        msg += f"💬 {rep_message[:50]}...\n"
                        msg += f"📅 {created_at[:16]}\n"
                        msg += f"➡️ /reports close {report_id} [оценка]\n━━━━━━━━━━━━━━━━━━\n"
                    
                    if len(reports) > 10:
                        msg += f"\n... и еще {len(reports) - 10} репортов"
                    
                    self.send_message(msg, user_id=user_id)
                else:
                    self.send_message("✅ Нет открытых репортов!", user_id=user_id)
                return
            
            elif parts[1] == 'close':
                if len(parts) >= 3:
                    try:
                        report_id = int(parts[2])
                        rating = int(parts[3]) if len(parts) > 3 else 5
                        if rating < 1 or rating > 5:
                            rating = 5
                        success, msg = self.close_report(user_id, report_id, rating)
                        self.send_message(msg, user_id=user_id)
                    except ValueError:
                        self.send_message("❌ Использование: /reports close [id] [оценка 1-5]", user_id=user_id)
                else:
                    self.send_message("❌ Использование: /reports close [id] [оценка 1-5]", user_id=user_id)
                return
            
            elif parts[1] == 'info':
                if len(parts) >= 3:
                    try:
                        report_id = int(parts[2])
                        info = self.get_report_info(report_id)
                        self.send_message(info, user_id=user_id)
                    except ValueError:
                        self.send_message("❌ Использование: /reports info [id]", user_id=user_id)
                else:
                    self.send_message("❌ Использование: /reports info [id]", user_id=user_id)
                return
            
            elif parts[1] == 'stats':
                stats = self.get_agent_stats(user_id)
                self.send_message(stats, user_id=user_id)
                return
        
        help_text = (
            "📋 **Система репортов**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Доступные команды:\n\n"
            "• /reports list - Список открытых репортов\n"
            "• /reports close [id] [оценка] - Закрыть репорт\n"
            "• /reports info [id] - Информация о репорте\n"
            "• /reports stats - Моя статистика\n\n"
            "Оценка: 1-5 ⭐ (по умолчанию 5)"
        )
        self.send_message(help_text, user_id=user_id)
    
    # ==================== СИСТЕМНЫЕ КОМАНДЫ ====================
    
    def log_action(self, user_id, action, target_id=None, reason=None):
        current_time = datetime.now().isoformat()
        self.cursor.execute('INSERT INTO logs (chat_id, user_id, action, target_id, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                           (0, user_id, action, target_id, reason, current_time))
        self.conn.commit()
        
        suspicious_actions = ['sysban', 'sysunban', 'sysrole', 'givemoney', 'givevip', 'add_agent', 'del_agent', 'set_rate', 'wipe']
        if action in suspicious_actions:
            log_entry = {'time': current_time, 'user': user_id, 'action': action, 'target': target_id, 'reason': reason}
            self.suspicious_logs.append(log_entry)
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
            self.cursor.execute('''
                UPDATE users SET role = 'user', vip_level = 0, bitcoin = 0, rubles = 0, dollars = 0, euros = 0,
                is_agent = 0, agent_number = 0, nickname = '', sysban_level = ? WHERE user_id = ?
            ''', (level, user_id))
            self.cursor.execute('DELETE FROM agent_permissions WHERE user_id = ?', (user_id,))
        elif level == 3:
            self.cursor.execute('''
                UPDATE users SET bitcoin = 0, rubles = 0, dollars = 0, euros = 0, sysban_level = ? WHERE user_id = ?
            ''', (level, user_id))
        else:
            self.cursor.execute('''
                UPDATE users SET sysban_level = ?, sysban_by = ?, sysban_reason = ?, sysban_date = ? WHERE user_id = ?
            ''', (level, admin_id, reason or "Не указана", current_time, user_id))
        
        self.conn.commit()
        self.log_action(admin_id, 'sysban', user_id, f"Стадия {level}: {reason}")
        
        level_names = {
            1: "1️⃣ Полный ЧС бота - нет доступа к боту, кикает из бесед",
            2: "2️⃣ Запрет доступа к командам - не кикает, но не дает пользоваться командами",
            3: "3️⃣ Слив денег - обнуление баланса + полный ЧС",
            4: "4️⃣ Анулировать аккаунт - снятие агента, денег, сброс данных"
        }
        
        return True, f"✅ Пользователь {self.get_user_link(user_id)} забанен!\n{level_names[level]}\nПричина: {reason or 'Не указана'}"
    
    def sysunban_user(self, admin_id, user_id):
        if not self.has_agent_permission(admin_id, 'sysban'):
            return False, "❌ У вас нет доступа к команде /sysunban!"
        
        self.cursor.execute('''
            UPDATE users SET sysban_level = 0, sysban_by = 0, sysban_reason = '', sysban_date = '' WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
        self.log_action(admin_id, 'sysunban', user_id, "Разбан")
        return True, f"✅ Пользователь {self.get_user_link(user_id)} разбанен!"
    
    def sysrole_user(self, admin_id, user_id, role, chat_id):
        if not self.has_agent_permission(admin_id, 'sysrole'):
            return False, "❌ У вас нет доступа к команде /sysrole!"
        
        self.cursor.execute('SELECT * FROM roles WHERE role_name = ?', (role,))
        if not self.cursor.fetchone():
            return False, f"❌ Роли '{role}' не существует!"
        
        try:
            self.vk_api.messages.editChat(chat_id=chat_id, member_id=user_id, role=role)
            self.log_action(admin_id, 'sysrole', user_id, f"Роль {role} в беседе {chat_id}")
            return True, f"✅ Пользователю {self.get_user_link(user_id)} выдана роль {role} в беседе!"
        except Exception as e:
            return False, f"❌ Ошибка выдачи роли: {str(e)}"
    
    def sysinfo_user(self, admin_id, user_id):
        if not self.has_agent_permission(admin_id, 'sysinfo'):
            return "❌ У вас нет доступа к команде /sysinfo!"
        
        user = self.get_user(user_id)
        in_blacklist = user[25] > 0
        
        info = f"📋 **Системная информация о {self.get_user_link(user_id)}**\n"
        info += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        info += f"🔒 В ЧС бота: {'✅ Да' if in_blacklist else '❌ Нет'}\n"
        
        if in_blacklist:
            level_names = {1: "Полный ЧС бота", 2: "Запрет доступа к командам", 3: "Слив денег", 4: "Анулирование аккаунта"}
            info += f"├─ Стадия: {level_names.get(user[25], user[25])}\n"
            info += f"├─ Кто занёс: {self.get_user_link(user[26])}\n"
            info += f"└─ Причина: {user[27] or 'Не указана'}\n"
        
        self.cursor.execute('SELECT chat_id FROM chats WHERE owner_id = ?', (user_id,))
        owner_chats = self.cursor.fetchall()
        
        self.cursor.execute('SELECT DISTINCT chat_id FROM invites WHERE user_id = ?', (user_id,))
        user_chats = self.cursor.fetchall()
        
        info += f"\n🏢 В каких чатах пользователь: {len(user_chats)}\n"
        for chat in user_chats[:5]:
            info += f"├─ Беседа {chat[0]}\n"
        if len(user_chats) > 5:
            info += f"└─ и еще {len(user_chats) - 5} чатов...\n"
        
        info += f"\n👑 В каких чатах владелец: {len(owner_chats)}\n"
        for chat in owner_chats[:5]:
            info += f"├─ Беседа {chat[0]}\n"
        if len(owner_chats) > 5:
            info += f"└─ и еще {len(owner_chats) - 5} чатов...\n"
        
        return info
    
    def get_sysinfo_help(self):
        return (
            "ℹ️ **Что означают цифры в sysinfo:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ - Информация о пользователе\n"
            "2️⃣ - В каких чатах пользователь\n"
            "3️⃣ - В каких чатах владелец\n"
            "4️⃣ - Эта справка"
        )
    
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
    
    def get_exchange_rates_info(self):
        info = "💱 **Текущие курсы валют:**\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━\n"
        info += f"🇺🇸 1 USD = {self.exchange_rates['usd_to_rub']:.2f} RUB\n"
        info += f"🇪🇺 1 EUR = {self.exchange_rates['eur_to_rub']:.2f} RUB\n"
        info += f"₿ 1 BTC = {self.exchange_rates['btc_to_usd']:.0f} USD\n"
        info += f"₿ 1 BTC = {self.exchange_rates['btc_to_rub']:.0f} RUB"
        return info
    
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
            return False, "❌ Неверная валюта! Доступны: usd, eur, btc_usd, btc_rub"
        
        self.save_exchange_rates()
        self.log_action(admin_id, 'set_rate', 0, f"{currency} = {rate}")
        return True, f"✅ Курс {currency} установлен: {rate}"
    
    def get_role_display_name(self, role_name):
        self.cursor.execute('SELECT role_name FROM roles WHERE role_name = ?', (role_name,))
        role = self.cursor.fetchone()
        
        if role:
            return role[0]
        
        default_names = {
            'user': 'Пользователь',
            'moderator': 'Модератор',
            'admin': 'Администратор',
            'owner': 'Владелец'
        }
        
        return default_names.get(role_name, role_name)
    
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
    
    def delkick_command(self, admin_id, chat_id=None):
        if not self.has_agent_permission(admin_id, 'delkick'):
            return False, "❌ У вас нет доступа к команде /delkick!"
        
        self.cursor.execute('SELECT user_id FROM users WHERE sysban_level = 1 OR sysban_level = 3')
        banned_users = self.cursor.fetchall()
        
        kicked_count = 0
        for user in banned_users:
            try:
                self.cursor.execute('SELECT chat_id FROM chats WHERE is_active = 1')
                chats = self.cursor.fetchall()
                for chat in chats:
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
                msg += f"\n... и еще {len(users) - 20} пользователей"
        else:
            msg = "✅ Все пользователи имеют ники!"
        
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    def ponicku_command(self, admin_id, search_part, chat_id=None):
        if not self.has_agent_permission(admin_id, 'snick'):
            return False, "❌ У вас нет доступа к команде /ponicku!"
        
        self.cursor.execute('SELECT user_id, name, nickname FROM users WHERE nickname LIKE ? AND nickname != "" AND is_agent = 0',
                           (f'%{search_part}%',))
        users = self.cursor.fetchall()
        
        if users:
            msg = f"📋 **Пользователи с частью '{search_part}' в нике:**\n━━━━━━━━━━━━━━━━━━\n"
            for uid, name, nickname in users[:20]:
                msg += f"• {self.get_user_link(uid)} - ник: {nickname}\n"
            if len(users) > 20:
                msg += f"\n... и еще {len(users) - 20} пользователей"
        else:
            msg = f"❌ Пользователи с частью '{search_part}' в нике не найдены."
        
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
            return False, "❌ Неверная валюта! Доступны: rub, usd, eur, btc"
        
        self.cursor.execute(f'UPDATE users SET {currency_map[currency]} = {currency_map[currency]} + ? WHERE user_id = ?', 
                           (amount, target_id))
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
        self.cursor.execute('UPDATE users SET vip_level = ?, vip_until = ?, role = ? WHERE user_id = ?',
                           (level, vip_until, f'vip{level}', target_id))
        self.conn.commit()
        self.log_action(admin_id, 'give_vip', target_id, f"VIP {level}")
        
        msg = f"✅ Пользователю {self.get_user_link(target_id)} выдан VIP {level} уровня на 30 дней!"
        if chat_id:
            self.send_message(msg, chat_id)
        return True, msg
    
    # ==================== СИСТЕМА РАБОВ ====================
    
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
                        if hours_passed > 24:
                            hours_passed = 24
                    except:
                        hours_passed = 0
                else:
                    hours_passed = 0
                
                income = level * 10 * hours_passed
                total_income += income
                
                self.cursor.execute('UPDATE slaves SET last_collect = ? WHERE owner_id = ? AND slave_id = ?',
                                   (current_time.isoformat(), user_id, slave_id))
            
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
            if self.cursor.rowcount > 0:
                return "🔗 Цепи надеты! Раб будет приносить на 20% больше прибыли."
            else:
                return "❌ Нет рабов или достигнут максимум цепей (5)!"
        
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
                        new_level = level + 1
                        self.cursor.execute('UPDATE slaves SET level = ?, exp = 0 WHERE owner_id = ? AND slave_id = ?',
                                           (new_level, user_id, slave_id))
                    else:
                        self.cursor.execute('UPDATE slaves SET exp = ? WHERE owner_id = ? AND slave_id = ?',
                                           (new_exp, user_id, slave_id))
                
                self.conn.commit()
                return f"⬆️ Рабы прокачаны! Стоимость: {upgrade_cost:.0f} ₽"
            else:
                return f"❌ Недостаточно средств! Нужно {upgrade_cost:.0f} ₽"
        
        return "❌ Неизвестное действие!"
    
    # ==================== ОСНОВНОЙ ОБРАБОТЧИК ====================
    
    def handle_message(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            
            chat_id = None
            if message.get('peer_id', 0) > 2000000000:
                chat_id = message['peer_id'] - 2000000000
                print(f"📨 Сообщение в беседе {chat_id}: {message.get('text', '')[:50]}")
            else:
                user_id = message['from_id']
                text = message.get('text', '')
                if text.lower() in self.commands['reports']:
                    self.handle_reports_in_dm(user_id, text)
                return
            
            if chat_id:
                self.get_or_create_chat(chat_id)
            
            # Обработка действий в беседе (приглашения/выходы)
            if message.get('action'):
                action = message['action']
                action_type = action.get('type')
                
                if action_type == 'chat_invite_user':
                    invited_id = action.get('member_id')
                    inviter_id = message['from_id']
                    
                    if invited_id == -self.group_id:
                        # Бота добавили
                        welcome_text = (
                            "🤖 **Бот добавлен в чат!**\n\n"
                            "📌 **Для начала работы:**\n"
                            "1️⃣ Выдайте боту права администратора\n"
                            "2️⃣ Введите команду /start\n\n"
                            "🔘 **Введите /start для активации**"
                        )
                        self.send_message(welcome_text, chat_id)
                    else:
                        # Пригласили пользователя
                        self.record_invite(chat_id, invited_id, inviter_id)
                        
                        settings = self.get_chat_settings(chat_id)
                        if settings.get('welcome_message', True):
                            self.send_message(f"👋 Добро пожаловать в беседу, {self.get_user_link(invited_id)}! Пригласил: {self.get_user_link(inviter_id)}", chat_id)
                
                elif action_type == 'chat_kick_user':
                    kicked_id = action.get('member_id')
                    
                    if kicked_id == -self.group_id:
                        # Бота удалили
                        self.cursor.execute('UPDATE chats SET is_active = 0 WHERE chat_id = ?', (chat_id,))
                        self.conn.commit()
                        print(f"🔴 Бот удален из беседы {chat_id}")
                    else:
                        # Кикнули пользователя
                        settings = self.get_chat_settings(chat_id)
                        if settings.get('kick_on_leave', False):
                            self.cursor.execute('UPDATE users SET role = "banned" WHERE user_id = ?', (kicked_id,))
                            self.conn.commit()
                            self.send_message(f"⛔ Пользователь {self.get_user_link(kicked_id)} кикнут и добавлен в ЧС!", chat_id)
            
            if 'text' in message:
                text = message['text'].lower()
                user_id = message['from_id']
                
                user = self.get_user(user_id)
                if user[25] in [1, 2, 3]:
                    if user[25] == 1 or user[25] == 3:
                        if text not in self.commands['report']:
                            self.send_message("❌ Вы находитесь в ЧС бота. Обратитесь в поддержку.", chat_id)
                            return
                    elif user[25] == 2:
                        if text not in self.commands['report'] and not any(text in cmd_list for cmd_list in self.commands.values()):
                            self.send_message("❌ Вам запрещен доступ к командам.", chat_id)
                            return
                
                if text in self.commands['start']:
                    success, msg = self.activate_chat(chat_id, message['from_id'])
                    return
                
                self.cursor.execute('SELECT is_active FROM chats WHERE chat_id = ?', (chat_id,))
                result = self.cursor.fetchone()
                
                if not result or result[0] == 0:
                    if text not in self.commands['start']:
                        error_msg = "❌ Беседа не активирована! Введите /start для активации."
                        self.send_message(error_msg, chat_id)
                    return
                
                # Обработка ожидания ID агента
                if user_id in self.waiting_for_agent_id and self.waiting_for_agent_id[user_id]:
                    try:
                        target_id = int(text)
                        self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (target_id,))
                        result = self.cursor.fetchone()
                        perms = json.loads(result[0]) if result else {}
                        keyboard = self.create_agent_permissions_keyboard(target_id, perms)
                        self.send_message(f"🔧 **Настройка прав агента #{self.get_agent_number(target_id)}**\n\nВыберите доступ для изменения:", chat_id, keyboard=keyboard)
                        del self.waiting_for_agent_id[user_id]
                    except ValueError:
                        self.send_message("❌ Неверный ID! Введите числовой ID.", chat_id)
                    return
                
                # Обработка ожидания ID для /syslinks
                if user_id in self.waiting_for_syslinks and self.waiting_for_syslinks[user_id]:
                    try:
                        target_chat_id = int(text)
                        link = self.get_syslinks(user_id, target_chat_id)
                        self.send_message(link, chat_id)
                        del self.waiting_for_syslinks[user_id]
                    except ValueError:
                        self.send_message("❌ Неверный ID беседы!", chat_id)
                    return
                
                # ========== СЕКРЕТНЫЕ КОМАНДЫ (через /agent) ==========
                
                if text in self.commands['bhelp']:
                    help_msg = self.get_bhelp(user_id)
                    self.send_message(help_msg, chat_id)
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
                    logs = self.get_suspicious_logs(user_id)
                    self.send_message(logs, chat_id)
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
                                keyboard = self.create_wipe_keyboard()
                                self.send_message(f"⚠️ **Вайп пользователя {self.get_user_link(target_id)}**\n\nВыберите что обнулить:", chat_id, keyboard=keyboard)
                                self.waiting_for_wipe_user = target_id
                            else:
                                self.send_message("❌ Пользователь не найден!", chat_id)
                        else:
                            self.send_message("❌ Использование: /wipeuser [пользователь]", chat_id)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                # ========== СИСТЕМА ОБЪЕДИНЕНИЙ ==========
                
                if text in self.commands['gkick']:
                    if self.has_agent_permission(user_id, 'sysban'):
                        parts = text.split()
                        if len(parts) >= 2:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            reason = ' '.join(parts[2:]) if len(parts) > 2 else None
                            success, msg = self.execute_global_command(user_id, 'kick', target_id, reason)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Использование: /gkick [пользователь] [причина]", chat_id)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                if text in self.commands['gban']:
                    if self.has_agent_permission(user_id, 'sysban'):
                        parts = text.split()
                        if len(parts) >= 2:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            reason = ' '.join(parts[2:]) if len(parts) > 2 else None
                            success, msg = self.execute_global_command(user_id, 'ban', target_id, reason)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Использование: /gban [пользователь] [причина]", chat_id)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                if text in self.commands['gmute']:
                    if self.has_agent_permission(user_id, 'sysban'):
                        parts = text.split()
                        if len(parts) >= 3:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            minutes = int(parts[2]) if len(parts) > 2 else 5
                            success, msg = self.execute_global_command(user_id, 'mute', target_id, None, minutes)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Использование: /gmute [пользователь] [минуты]", chat_id)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                if text in self.commands['grole']:
                    if self.has_agent_permission(user_id, 'sysrole'):
                        parts = text.split()
                        if len(parts) >= 3:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            role = parts[2]
                            success, msg = self.execute_global_command(user_id, 'role', target_id, None, None, role)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Использование: /grole [пользователь] [роль]", chat_id)
                    else:
                        self.send_message("❌ У вас нет доступа к этой команде!", chat_id)
                    return
                
                # ========== КОМАНДЫ ДЛЯ АГЕНТОВ ==========
                
                if text in self.commands['rates']:
                    info = self.get_exchange_rates_info()
                    self.send_message(info, chat_id)
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
                
                # Команда /agent - управление агентами
                if text in self.commands['agent']:
                    if not self.can_manage_agents(user_id):
                        self.send_message("❌ У вас нет доступа к команде /agent!", chat_id)
                        return
                    
                    self.send_message("🔧 **Управление правами агентов**\n\nВведите ID агента для настройки:", chat_id)
                    self.waiting_for_agent_id[user_id] = True
                    return
                
                if text in self.commands['botadmins']:
                    if not self.is_agent(user_id):
                        self.send_message("❌ Вы не являетесь агентом!", chat_id)
                        return
                    
                    agents = self.get_all_agents()
                    if agents:
                        info = "👑 **Список агентов поддержки**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        for agent_id, name, agent_number, tickets, rating in agents:
                            info += f"**#{agent_number}** | {self.get_user_link(agent_id)}\n"
                            info += f"📊 Тикетов: {tickets} | Рейтинг: {rating:.1f}⭐\n"
                            info += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        
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
                        keyboard = self.create_sysban_keyboard()
                        self.send_message("Выберите стадию бана:", chat_id, keyboard=keyboard)
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
                
                if text in self.commands['sysrole']:
                    if not self.has_agent_permission(user_id, 'sysrole'):
                        self.send_message("❌ У вас нет доступа к команде /sysrole!", chat_id)
                        return
                    parts = text.split()
                    if len(parts) >= 3:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                        if target_id:
                            role = parts[2]
                            success, msg = self.sysrole_user(user_id, target_id, role, chat_id)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Пользователь не найден!", chat_id)
                    else:
                        self.send_message("❌ Использование: /sysrole [пользователь] [роль]", chat_id)
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
                    target_id = None
                    if len(parts) > 1:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    else:
                        target_id = self.extract_user_id('', message.get('reply_message'))
                    if target_id:
                        success, msg = self.rnick_command(user_id, target_id, chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                if text in self.commands['delkick']:
                    if not self.has_agent_permission(user_id, 'delkick'):
                        self.send_message("❌ У вас нет доступа к команде /delkick!", chat_id)
                        return
                    success, msg = self.delkick_command(user_id, chat_id)
                    self.send_message(msg, chat_id)
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
                        search_part = parts[1]
                        success, msg = self.ponicku_command(user_id, search_part, chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Использование: /ponicku [часть ника]", chat_id)
                    return
                
                if text in self.commands['mutereports']:
                    if not self.has_agent_permission(user_id, 'mutereports'):
                        self.send_message("❌ У вас нет доступа к команде /mutereports!", chat_id)
                        return
                    parts = text.split(maxsplit=1)
                    target_id = None
                    if len(parts) > 1:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    else:
                        target_id = self.extract_user_id('', message.get('reply_message'))
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
                    target_id = None
                    if len(parts) > 1:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    else:
                        target_id = self.extract_user_id('', message.get('reply_message'))
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
                    
                    msg = f"🏓 **Бот работает!**\n"
                    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    msg += f"⏱️ Пинг: {response_time:.2f} мс\n"
                    msg += f"🔄 Статус: ✅ Активен"
                    
                    keyboard = self.create_ping_keyboard()
                    self.send_message(msg, chat_id, keyboard=keyboard)
                    return
                
                if text in self.commands['shop']:
                    keyboard = self.create_shop_category_keyboard()
                    self.send_message("🛒 **Магазин**\n━━━━━━━━━━━━━━━━━━\n💰 Валюта: Доллары ($)\n\nВыберите категорию:", chat_id, keyboard=keyboard)
                    return
                
                if text in self.commands['help']:
                    help_msg = (
                        "📋 **Список команд:**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        "👤 **Пользовательские:**\n"
                        "• /stats - Ваша статистика\n"
                        "• /balance - Ваш баланс\n"
                        "• /work - Работа\n"
                        "• /mine - Майнинг BTC\n"
                        "• /bonus - Ежедневный бонус\n"
                        "• /vip - Информация о VIP\n"
                        "• /shop - Магазин\n"
                        "• /transfer [id] [валюта] [сумма] - Перевод\n"
                        "• /slaves - Система рабов\n"
                        "• /settings - Настройки чата\n\n"
                        "🛡️ **Модерация:**\n"
                        "• /ban [id] - Бан пользователя\n"
                        "• /mute [id] [минуты] - Мут\n"
                        "• /warn [id] - Варн\n"
                        "• /kick [id] - Кик пользователя\n"
                        "• /filter add [слово] [действие] - Добавить фильтр\n"
                        "• /filter list - Список фильтров\n\n"
                        "💎 **VIP команды:**\n"
                        "• !скажи [текст] - Сказать от имени бота\n\n"
                        "🔧 **Для администраторов:**\n"
                        "• /setrole [id] [роль] - Выдать роль\n"
                        "• /addrole [название] [приоритет] - Добавить роль\n"
                        "• /roleslist - Список ролей\n"
                        "• /editcmd [команда] [приоритет] [роль] - Настройка прав\n\n"
                        "💱 **Курсы валют:**\n"
                        "• /rates - Текущие курсы\n\n"
                        "📌 **Все команды работают с префиксами: / ! .**"
                    )
                    self.send_message(help_msg, chat_id)
                    return
                
                if text in self.commands['report']:
                    parts = text.split(maxsplit=1)
                    if len(parts) > 1:
                        report_text = parts[1]
                        success, msg = self.add_report(user_id, user_id, report_text, chat_id)
                        self.send_message(msg, chat_id)
                    else:
                        self.send_message("❌ Использование: /report [текст вопроса/проблемы]", chat_id)
                    return
                
                if text in self.commands['transfer']:
                    parts = text.split()
                    if len(parts) >= 4:
                        try:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            if target_id:
                                currency = parts[2]
                                amount = float(parts[3])
                                success, msg = self.transfer_money(user_id, target_id, currency, amount)
                                self.send_message(msg, chat_id)
                            else:
                                self.send_message("❌ Пользователь не найден!", chat_id)
                        except ValueError:
                            self.send_message("❌ Использование: /transfer [id] [валюта] [сумма]", chat_id)
                    else:
                        self.send_message("❌ Использование: /transfer [id] [валюта] [сумма]\nДоступные валюты: rub, usd, eur, btc", chat_id)
                    return
                
                if text in self.commands['slaves']:
                    keyboard = self.create_slave_keyboard()
                    self.send_message("🔄 **Система рабов**\n\nВыберите действие:", chat_id, keyboard=keyboard)
                    return
                
                if text in self.commands['stats']:
                    stats = self.get_user_stats_detailed(user_id, chat_id)
                    self.send_message(stats, chat_id)
                    return
                
                if text in self.commands['vip']:
                    vip_info = self.get_vip_info(user_id)
                    self.send_message(vip_info, chat_id)
                    return
                
                if text in self.commands['staff']:
                    staff = self.get_staff_list()
                    if staff:
                        staff_text = "👥 **Персонал сервера:**\n━━━━━━━━━━━━━━━━━━\n"
                        for member in staff:
                            role_emoji = self.status_emojis.get(member['role'], '👤')
                            staff_text += f"{role_emoji} {self.get_user_link(member['id'])} - {member['role'].upper()}\n"
                        self.send_message(staff_text, chat_id)
                    else:
                        self.send_message("👥 Персонал отсутствует.", chat_id)
                    return
                
                if text in self.commands['roleslist']:
                    roles = self.get_roles_list()
                    if roles:
                        roles_text = "📋 **Список ролей:**\n━━━━━━━━━━━━━━━━━━\n"
                        for role_name, priority in roles:
                            role_display = self.get_role_display_name(role_name)
                            roles_text += f"• {role_display} - приоритет: {priority}\n"
                        self.send_message(roles_text, chat_id)
                    else:
                        self.send_message("📋 Роли не найдены.", chat_id)
                    return
                
                if text in self.commands['addrole']:
                    parts = text.split()
                    if len(parts) >= 3:
                        role_name = parts[1]
                        try:
                            priority = int(parts[2])
                            success, msg = self.add_custom_role(user_id, role_name, priority)
                            self.send_message(msg, chat_id)
                        except ValueError:
                            self.send_message("❌ Приоритет должен быть числом!", chat_id)
                    else:
                        self.send_message("❌ Использование: /addrole [название] [приоритет]", chat_id)
                    return
                
                if text in self.commands['setrole']:
                    parts = text.split()
                    if len(parts) >= 3:
                        try:
                            target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                            if target_id:
                                role = parts[2]
                                success, msg = self.set_user_role(user_id, target_id, role, chat_id)
                                self.send_message(msg, chat_id)
                            else:
                                self.send_message("❌ Пользователь не найден!", chat_id)
                        except ValueError:
                            self.send_message("❌ ID должен быть числом!", chat_id)
                    else:
                        self.send_message("❌ Использование: /setrole [пользователь] [роль]", chat_id)
                    return
                
                # Модерация
                if text in self.commands['ban']:
                    if not self.has_command_access(user_id, 'ban'):
                        self.send_message("❌ У вас нет прав для бана!", chat_id)
                        return
                    
                    parts = text.split(maxsplit=2)
                    target_id = None
                    
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    
                    if target_id:
                        reason = parts[2] if len(parts) > 2 else None
                        self.ban_user(target_id, user_id, chat_id, reason)
                    else:
                        self.send_message("❌ Пользователь не найден! Используйте:\n/ban [id] [причина]\n/ban @id123 причина\nИли ответьте на сообщение пользователя и напишите /ban [причина]", chat_id)
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
                        self.send_message("❌ Использование: /mute [пользователь] [минуты]\nИли ответьте на сообщение пользователя и напишите /mute [минуты]", chat_id)
                    return
                
                if text in self.commands['warn']:
                    if not self.has_command_access(user_id, 'warn'):
                        self.send_message("❌ У вас нет прав для выдачи варнов!", chat_id)
                        return
                    
                    parts = text.split(maxsplit=2)
                    target_id = None
                    
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    
                    if target_id:
                        reason = parts[2] if len(parts) > 2 else None
                        self.add_warn(target_id, user_id, chat_id, reason)
                    else:
                        self.send_message("❌ Пользователь не найден! Используйте:\n/warn [id] [причина]\n/warn @id123 причина\nИли ответьте на сообщение пользователя и напишите /warn [причина]", chat_id)
                    return
                
                if text in self.commands['kick']:
                    if not self.has_command_access(user_id, 'kick'):
                        self.send_message("❌ У вас нет прав для кика!", chat_id)
                        return
                    
                    parts = text.split(maxsplit=2)
                    target_id = None
                    
                    if len(parts) >= 2:
                        target_id = self.extract_user_id(parts[1], message.get('reply_message'))
                    
                    if target_id:
                        reason = parts[2] if len(parts) > 2 else None
                        self.kick_user(user_id, target_id, chat_id, reason)
                    else:
                        self.send_message("❌ Пользователь не найден!", chat_id)
                    return
                
                if text in self.commands['balance']:
                    user = self.get_user(user_id)
                    balance_msg = f"💰 **Ваш баланс:**\n━━━━━━━━━━━━━━━━━━\n"
                    balance_msg += f"🇷🇺 Рубли: {user[7]:.2f} ₽\n"
                    balance_msg += f"🇺🇸 Доллары: {user[8]:.2f} $\n"
                    balance_msg += f"🇪🇺 Евро: {user[9]:.2f} €\n"
                    balance_msg += f"₿ Биткойны: {user[6]:.8f} BTC"
                    self.send_message(balance_msg, chat_id)
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
                            self.send_message(msg, chat_id)
                        elif item == 'vip2':
                            success, msg = self.buy_vip(user_id, 2)
                            self.send_message(msg, chat_id)
                        elif item == 'vip3':
                            success, msg = self.buy_vip(user_id, 3)
                            self.send_message(msg, chat_id)
                        elif item == 'miner':
                            success, msg = self.buy_miner(user_id)
                            self.send_message(msg, chat_id)
                        else:
                            self.send_message("❌ Неизвестный товар! Используйте /shop", chat_id)
                    else:
                        self.send_message("❌ Использование: /buy [товар]", chat_id)
                    return
                
                if text in self.commands['chat_info']:
                    chat = self.get_or_create_chat(chat_id)
                    info = f"📊 **Информация о беседе**\n━━━━━━━━━━━━━━━━━━\n"
                    info += f"💬 Название: {chat[1]}\n"
                    info += f"🆔 ID: {chat[0]}\n"
                    info += f"🔘 Статус: {'✅ Активна' if chat[3] == 1 else '❌ Не активирована'}\n"
                    self.send_message(info, chat_id)
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
    
    def add_chat_filter(self, chat_id, word, action, admin_id):
        try:
            self.cursor.execute('''
                INSERT INTO chat_filters (chat_id, word, action, added_by, added_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, word.lower(), action, admin_id, datetime.now().isoformat()))
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
        self.cursor.execute('''
            INSERT INTO invites (chat_id, user_id, inviter_id, invited_at)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, user_id, inviter_id, datetime.now().isoformat()))
        self.conn.commit()
    
    # ==================== CALLBACK ОБРАБОТЧИК ====================
    
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
                
                # Обработка управления правами агента
                if action == 'agent_toggle_perm':
                    target_id = data.get('target_id')
                    permission = data.get('permission')
                    current = data.get('current', False)
                    
                    if self.can_manage_agents(user_id):
                        success, msg = self.update_agent_permissions(user_id, target_id, permission, not current)
                        self.send_message(msg, user_id=user_id)
                        
                        self.cursor.execute('SELECT permissions FROM agent_permissions WHERE user_id = ?', (target_id,))
                        result = self.cursor.fetchone()
                        perms = json.loads(result[0]) if result else {}
                        keyboard = self.create_agent_permissions_keyboard(target_id, perms)
                        self.send_message(f"🔧 **Настройка прав агента #{self.get_agent_number(target_id)}**\n\nВыберите доступ для изменения:", user_id=user_id, keyboard=keyboard)
                    return
                
                elif action == 'agent_back':
                    self.send_message("🔧 **Управление правами агентов**\n\nВведите ID агента для настройки:", user_id=user_id)
                    return
                
                # Обработка магазина
                elif action == 'shop_category':
                    category = data.get('category')
                    if category == 'vip':
                        keyboard = self.create_vip_keyboard()
                        self.send_message("💎 **Выберите VIP статус:**\n\n🌟 VIP I - 5000₽\n💎 VIP II - 15000₽\n👑 VIP III - 35000₽\n\nДействует 30 дней", chat_id, keyboard=keyboard)
                    else:
                        items = self.inline_shop.get(category, {})
                        if items:
                            keyboard = self.create_shop_items_keyboard(category, items)
                            category_names = {'phones': 'Телефоны', 'houses': 'Дома', 'clothes': 'Одежда', 'items': 'Вещи'}
                            self.send_message(f"📱 **{category_names.get(category, category)}**\n\nВыберите товар:", chat_id, keyboard=keyboard)
                    return
                
                elif action == 'shop_back':
                    keyboard = self.create_shop_category_keyboard()
                    self.send_message("🛒 **Магазин**\n━━━━━━━━━━━━━━━━━━\n💰 Валюта: Доллары ($)\n\nВыберите категорию:", chat_id, keyboard=keyboard)
                    return
                
                elif action == 'buy_vip':
                    level = data.get('level')
                    price = self.shop_items[f'vip{level}']['price']
                    benefits = self.shop_items[f'vip{level}']['benefits']
                    
                    info = f"💎 **VIP {level} уровня**\n━━━━━━━━━━━━━━━━━━\n"
                    info += f"💰 Цена: {price}₽\n"
                    info += f"📅 Действует: 30 дней\n\n"
                    info += f"📊 **Преимущества:**\n"
                    info += f"• 🏢 Объединений: {benefits['max_unions']}\n"
                    info += f"• 💬 Бесед: {benefits['max_chats']}\n"
                    info += f"• 📢 Команд !скажи: {benefits['daily_say']}/день"
                    
                    keyboard = self.create_vip_info_keyboard(level, price)
                    self.send_message(info, chat_id, keyboard=keyboard)
                    return
                
                elif action == 'confirm_buy_vip':
                    level = data.get('level')
                    success, msg = self.buy_vip(user_id, level)
                    self.send_message(msg, chat_id)
                    
                    keyboard = self.create_shop_category_keyboard()
                    self.send_message("🛒 **Магазин**\n━━━━━━━━━━━━━━━━━━\n💰 Валюта: Доллары ($)\n\nВыберите категорию:", chat_id, keyboard=keyboard)
                    return
                
                elif action == 'vip_back':
                    keyboard = self.create_vip_keyboard()
                    self.send_message("💎 **Выберите VIP статус:**\n\n🌟 VIP I - 5000₽\n💎 VIP II - 15000₽\n👑 VIP III - 35000₽\n\nДействует 30 дней", chat_id, keyboard=keyboard)
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
                
                # Обработка /ping обновления
                elif action == 'ping_refresh':
                    start_time = time.time()
                    response_time = (time.time() - start_time) * 1000
                    
                    msg = f"🏓 **Бот работает!**\n"
                    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    msg += f"⏱️ Пинг: {response_time:.2f} мс\n"
                    msg += f"🔄 Статус: ✅ Активен"
                    
                    keyboard = self.create_ping_keyboard()
                    self.send_message(msg, chat_id, keyboard=keyboard)
                    return
                
                # Обработка показа статистики агента
                elif action == 'show_agent_stats':
                    agent_id = data.get('agent_id')
                    stats = self.get_agent_stats_for_user(agent_id)
                    self.send_message(stats, chat_id)
                    return
                
                # Обработка настроек чата
                elif action == 'settings_toggle':
                    setting = data.get('setting')
                    settings = self.get_chat_settings(chat_id)
                    settings[setting] = not settings.get(setting, False)
                    self.save_chat_settings(chat_id, settings)
                    
                    keyboard = self.create_settings_keyboard(settings)
                    self.send_message(f"⚙️ **Настройки чата**\n\n{setting} изменен на {settings[setting]}", chat_id, keyboard=keyboard)
                    return
                
                elif action == 'settings_change':
                    setting = data.get('setting')
                    if setting == 'who_can_add':
                        keyboard = self.create_who_can_add_keyboard()
                        self.send_message("👥 **Кто может добавлять пользователей?**", chat_id, keyboard=keyboard)
                    return
                
                elif action == 'settings_set':
                    setting = data.get('setting')
                    value = data.get('value')
                    settings = self.get_chat_settings(chat_id)
                    settings[setting] = value
                    self.save_chat_settings(chat_id, settings)
                    
                    keyboard = self.create_settings_keyboard(settings)
                    self.send_message(f"⚙️ **Настройки чата**\n\n{setting} изменен на {value}", chat_id, keyboard=keyboard)
                    return
                
                elif action == 'settings_back':
                    settings = self.get_chat_settings(chat_id)
                    keyboard = self.create_settings_keyboard(settings)
                    self.send_message("⚙️ **Настройки чата**\n\nВыберите параметр для изменения:", chat_id, keyboard=keyboard)
                    return
                
                elif action == 'settings_close':
                    self.send_message("⚙️ Настройки закрыты.", chat_id)
                    return
                
                # Обработка системы рабов
                elif action == 'slave_collect':
                    result = self.handle_slave_system(user_id, 'collect')
                    self.send_message(result, chat_id)
                    return
                
                elif action == 'slave_chains':
                    result = self.handle_slave_system(user_id, 'chains')
                    self.send_message(result, chat_id)
                    return
                
                elif action == 'slave_upgrade':
                    result = self.handle_slave_system(user_id, 'upgrade')
                    self.send_message(result, chat_id)
                    return
                
                elif action == 'slave_buyout':
                    result = self.handle_slave_system(user_id, 'buyout')
                    self.send_message(result, chat_id)
                    return
                
                # Обработка вайпа
                elif action == 'wipe_money':
                    if hasattr(self, 'waiting_for_wipe_user'):
                        msg = self.wipe_money(user_id, self.waiting_for_wipe_user)
                        delattr(self, 'waiting_for_wipe_user')
                    else:
                        msg = self.wipe_money(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                elif action == 'wipe_warns':
                    if hasattr(self, 'waiting_for_wipe_user'):
                        msg = self.wipe_warns(user_id, self.waiting_for_wipe_user)
                        delattr(self, 'waiting_for_wipe_user')
                    else:
                        msg = self.wipe_warns(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                elif action == 'wipe_mutes':
                    if hasattr(self, 'waiting_for_wipe_user'):
                        msg = self.wipe_mutes(user_id, self.waiting_for_wipe_user)
                        delattr(self, 'waiting_for_wipe_user')
                    else:
                        msg = self.wipe_mutes(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                elif action == 'wipe_bans':
                    if hasattr(self, 'waiting_for_wipe_user'):
                        msg = self.wipe_bans(user_id, self.waiting_for_wipe_user)
                        delattr(self, 'waiting_for_wipe_user')
                    else:
                        msg = self.wipe_bans(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                elif action == 'wipe_vip':
                    if hasattr(self, 'waiting_for_wipe_user'):
                        msg = self.wipe_vip(user_id, self.waiting_for_wipe_user)
                        delattr(self, 'waiting_for_wipe_user')
                    else:
                        msg = self.wipe_vip(user_id)
                    self.send_message(msg, chat_id)
                    return
                
                elif action == 'wipe_back':
                    keyboard = self.create_wipe_keyboard()
                    self.send_message("⚠️ **Вайп система**\n\nВыберите что обнулить:", chat_id, keyboard=keyboard)
                    return
                
                # Обработка системной информации
                elif action == 'sysinfo_opt_':
                    option = int(data.get('option', 0))
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
                
                # Обработка системного бана
                elif action == 'sysban_stage_':
                    stage = data.get('stage')
                    stage_info = f"**Стадия {stage}:**\n━━━━━━━━━━━━━━━━━━━━━━\n"
                    if stage == 1:
                        stage_info += "1️⃣ Полный ЧС бота\n• Нет доступа к боту\n• Кикает при добавлении в беседу\n\n"
                    elif stage == 2:
                        stage_info += "2️⃣ Запрет доступа к командам\n• Не кикает из беседы\n• Не дает пользоваться командами\n\n"
                    elif stage == 3:
                        stage_info += "3️⃣ Слив денег\n• То же, что полный ЧС бота\n• Обнуление баланса\n\n"
                    elif stage == 4:
                        stage_info += "4️⃣ Анулировать аккаунт\n• Снятие агента\n• Снятие всех денег\n• Сброс всех данных\n\n"
                    stage_info += "Используйте: /sysban [id] [стадия] [причина]"
                    self.send_message(stage_info, user_id=user_id)
                    return
                
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга callback payload: {e}")
    
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


import os

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
