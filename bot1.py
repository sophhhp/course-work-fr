import os
import telebot
from telebot import types
import random

from bot_token1 import BOT_TOKEN


bot = telebot.TeleBot(BOT_TOKEN)


# Чтение слов-стимулов для эксперимента из файла, создание словаря стимулов
ALL_WORDS = []
with open('stimuli.txt', 'r', encoding='utf-8') as f:
    words = f.readlines()
    for word in words:
        ALL_WORDS.append(word.replace('\n', ''))


# Словарь списков пользователей
user_lists = dict()
# Список слов для тестирования каждого пользователя
user_words = dict()
# Список пользователей, чьи результаты уже есть в системе
user_finished = list()
# Список пользователей, прошедших анкету
user_formulaire_finished = list()

CONTINUE_FULL_PROMPT = 'prompt_continue'
AGE_PROMPT = 'prompt_formulaire_âge'
FIRST_LANGUAGE_PROMPT = 'prompt_formulaire_langue_maternelle'
LOCATION_PROMPT = 'prompt_place'
GENDER_PROMPT = 'prompt_sexe'
OTHER_LANGUAGES_PROMPT = 'prompt_autres_langues'


# Отправка приветственного сообщения с информацией
@bot.message_handler(commands=['start'])
def send_welcome(message):
    with open('start.txt', 'r', encoding='utf-8') as f_start:
        start = f_start.read()
    bot.reply_to(message, start)


# Отправка слов-стимулов
@bot.message_handler(commands=['commencer'])
def send_word(message):
    # Проверка на первое прохождение теста
    if not message.chat.id in user_finished and not message.chat.id in user_lists:
        personal_random_list = ALL_WORDS[:]
        random.shuffle(personal_random_list)
        user_lists[message.chat.id] = dict()
        user_lists[message.chat.id]['mandatory'] = personal_random_list[:25]
        user_lists[message.chat.id]['extra'] = personal_random_list[25:]

    # Отправка слов-стимулов в ответ на слово-реакцию до момента пустого списка
    if len(user_lists[message.chat.id]['mandatory']) > 0:
        user_words[message.chat.id] = random.choice(
            user_lists[message.chat.id]['mandatory'])
        # Удаление слов из словаря
        user_lists[message.chat.id]['mandatory'].remove(
            user_words[message.chat.id])
        bot.reply_to(message, user_words[message.chat.id])
    else:
        # Сообщение с благодарностью и вопрос
        with open('fin.txt', 'r', encoding='utf-8') as f_fin:
            fin = f_fin.read()
        with open('question.txt', 'r', encoding='utf-8') as f_question:
            question = f_question.read()
        # Вопрос про продолжение теста
        if len(user_lists[message.chat.id]['extra']) > 0:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, one_time_keyboard=True)
            btn_yes = types.KeyboardButton('Oui')
            btn_no = types.KeyboardButton('Non')
            markup.row(btn_yes, btn_no)
            user_words[message.chat.id] = CONTINUE_FULL_PROMPT
            bot.reply_to(message, question, reply_markup=markup)
        else:
            bot.reply_to(message, fin)
        # Добавление в список пользователей, прошедших тест
            user_finished.append(message.chat.id)


# Отправка сообщения с благодарностью за прохождение теста
@bot.message_handler(commands=['stop'])
def send_welcome(message):
    with open('fin.txt', 'r', encoding='utf-8') as f_fin:
        fin = f_fin.read()
    bot.reply_to(message, fin)


# Начало заполнения анкеты пользователя
@bot.message_handler(commands=['formulaire'])
def send_blank(message):
    bot.reply_to(message, 'Quel est votre âge? (en années)')
    user_words[message.chat.id] = AGE_PROMPT


# Запись анкеты и результатов пользователя в csv-файл
def record_answer(message):
    with open(f'results/{message.chat.id}.csv', 'a', encoding='utf-8') as f:
        f.write(str(user_words[message.chat.id]) +
                ',' + message.text.replace(',', '') + '\n')


# Заполнение анкеты пользователя
@bot.message_handler()
def save_message(message):
    if user_words[message.chat.id] == AGE_PROMPT:
        markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True)
        btn_man = types.KeyboardButton('Masculin')
        btn_woman = types.KeyboardButton('Féminin')
        btn_other = types.KeyboardButton('Autre')
        btn_no = types.KeyboardButton('—')
        markup.row(btn_man, btn_woman, btn_other, btn_no)
        bot.reply_to(message, 'Quel est votre sexe? \n(si vous préférez ne pas répondre, choisissez « — »)', reply_markup=markup)
        record_answer(message)
        user_words[message.chat.id] = GENDER_PROMPT
    elif user_words[message.chat.id] == GENDER_PROMPT:
        bot.reply_to(
            message, 'Quelle est votre/vos langue(s) maternelle(s)?')
        record_answer(message)
        user_words[message.chat.id] = FIRST_LANGUAGE_PROMPT
    elif user_words[message.chat.id] == FIRST_LANGUAGE_PROMPT:
        bot.reply_to(message, 'Quelles autres langues parlez-vous?')
        record_answer(message)
        user_words[message.chat.id] = OTHER_LANGUAGES_PROMPT
    elif user_words[message.chat.id] == OTHER_LANGUAGES_PROMPT:
        bot.reply_to(
            message, 'Dans quel pays avez-vous passé 10 premières années de votre vie?')
        record_answer(message)
        user_words[message.chat.id] = LOCATION_PROMPT
    elif user_words[message.chat.id] == LOCATION_PROMPT:
        record_answer(message)
        with open('commencer.txt', 'r', encoding='utf-8') as f_commencer:
            commencer = f_commencer.read()
        bot.reply_to(message, commencer)
    elif user_words[message.chat.id] == CONTINUE_FULL_PROMPT:
        if message.text == 'Oui':
            user_lists[message.chat.id]['mandatory'] = user_lists[message.chat.id]['extra'][:]
            user_lists[message.chat.id]['extra'] = list()
            send_word(message)
        else:
            user_lists[message.chat.id]['extra'] = list()
            send_word(message)
    elif user_words[message.chat.id] in ALL_WORDS:
        record_answer(message)
        send_word(message)


bot.infinity_polling()