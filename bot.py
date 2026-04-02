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
        return True, f"✅ Бан выполнен в {len([r for r in results if '✅' in r])}/{len(chats)} беседах"
    
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
        return True, f"✅ Мут выполнен в {len([r for r in results if '✅' in r])}/{len(chats)} беседах"
    
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
        return True, f"✅ Кик выполнен в {len([r for r in results if '✅' in r])}/{len(chats)} беседах"
    
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
        return True, f"✅ Роль выдана в {len([r for r in results if '✅' in r])}/{len(chats)} беседах"
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
    if text in self.commands['union']:
                msg = ("🏢 **Система объединений**\n━━━━━━━━━━━━━━━━━━━━━━\n"
                       "• /union_create [название] - Создать\n• /union_join [код] - Вступить\n"
                       "• /union_leave - Выйти\n• /union_info - Информация\n"
                       "• /union_invite - Новый код (владелец)\n"
                       "• /union_ban [пользователь] [причина] - Бан везде\n"
                       "• /union_mute [пользователь] [минуты] - Мут везде\n"
                       "• /union_kick [пользователь] [причина] - Кик везде\n"
                       "• /union_role [пользователь] [роль] - Роль везде")
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
                if __name__ == "__main__":
    GROUP_TOKEN = os.getenv("VK_TOKEN")
    GROUP_ID = os.getenv("VK_GROUP_ID")
    if not GROUP_TOKEN or not GROUP_ID:
        print("❌ Ошибка: переменные окружения не заданы!")
        exit(1)
    GROUP_ID = int(GROUP_ID)
    bot = VKChatManager(GROUP_TOKEN, GROUP_ID)
    bot.run()
