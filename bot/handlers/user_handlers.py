from aiogram import Router, F, Bot, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from lexicon.lexicon_en import LEXICON_EN

router = Router()
user_states = {}

url = 'https://2cb5-176-213-104-154.ngrok-free.app'

@router.message(CommandStart())
async def process_start_command(message: Message):

    try:
        args = message.text.split()[1]
    except:
        args = None
    path_to_photo = "bot/img/start_img.jpg"

    if args:
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Let's go", web_app=types.WebAppInfo(url=f"{url}?ref={args}")),
                InlineKeyboardButton(text="Join community", url="https://t.me/TGRExchange")
            ]
        ])  
        caption = LEXICON_EN['/start'] + str(args)
    else:
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Let's go", web_app=types.WebAppInfo(url=url)),
                InlineKeyboardButton(text="Join community", url="https://t.me/TGRExchange")
            ]
        ])  
        caption = LEXICON_EN['/start']
    
    

    await message.answer_photo(
        types.FSInputFile(path=path_to_photo),
        caption=caption,
        reply_markup=inline_kb
    )

@router.message(Command(commands='admin'))
async def process_admin_command(message: Message):
    user_states[message.from_user.id] = 'admin_password_wait'
    await message.answer(text='Введите пароль:')

@router.message()
async def process_user_message(message: Message):
    if message.from_user.id in user_states and user_states[message.from_user.id] == 'admin_password_wait':
        if message.text == '123':
            del user_states[message.from_user.id]
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Админ панель", web_app=types.WebAppInfo(url=f"{url}/admin?password=123")),
                ]
            ])  
            await message.answer(text='Пароль верный\n\nВыполнить вход в админ панель можно всегда по кнопке в сообщении\n\nЕсли удалите сообщение то вводить пароль придёться снова',reply_markup=inline_kb)
        else:
            del user_states[message.from_user.id]
            await message.answer(text='Пароль неверный')
    else:
        pass