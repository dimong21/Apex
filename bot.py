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
            'kick_on_leave': False,
            'who_can_add': 'all',
            'games_enabled': True,
            'welcome_message': True,
            'anti_flood': False,
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
        self.waiting_for_wipe_user = None
        
        # Руссификация команд
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
            'help': ['/help', '/помо
