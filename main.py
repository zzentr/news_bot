from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from asyncio import run
from asyncio import to_thread
import aiohttp
from datetime import datetime, timedelta
from random import choice
from dotenv import load_dotenv
import os
load_dotenv()


bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()
scheduler = AsyncIOScheduler()
users_jobs = {}

class Interval(StatesGroup):

    interval = State()


@dp.message(Command('start'))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='1 час', callback_data='hour_1'),
                                                InlineKeyboardButton(text='3 часа', callback_data='hour_3'),
                                                InlineKeyboardButton(text='5 часов', callback_data='hour_5')],
                                              [InlineKeyboardButton(text='Написать свой интервал', 
                                                                    callback_data='new_interval')]])
    await message.answer('привет, я буду присылать вам последние новости из мира чтобы вы всегда были в курсе дел.\n\n'
                         'выберите интервал времени в часах через который я буду присылать вам сообщение!', 
                         reply_markup=keyboard)

async def send_news(tg_id):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {'X-Api-Key': os.getenv('NEWS_API')}
            from_time = datetime.now() - timedelta(days=2)

            async with session.get(url=f'https://newsapi.org/v2/everything?q=новости&language=ru&pageSize=1&from={from_time}',
                                    headers=headers, ssl=False) as response:
                
                if response.ok:
                    data = await response.json()
                    news = data['articles'][0]
                    emoji = choice(['❗️', '❓', '⚠️', '🔥'])
                    await bot.send_message(chat_id=tg_id, text=f'{emoji} <b>{news['title']}</b> {emoji}\n\n{news['description']}\n\n{news['url']}', 
                                        parse_mode='html')
                    
                else:
                    await bot.send_message(chat_id=tg_id, text='извините, но сервис с новостями не отвечает')

    except Exception as e:
        print(f'Error: {e}')
        await bot.send_message(chat_id=tg_id, text='извините, у нас небольшие неполадки, скоро все починим!')

@dp.message(Command('interval'))
async def new_interval(message: Message, state: FSMContext):
    await state.set_state(Interval.interval)
    await message.answer('отправьте мне новый интервал')

@dp.message(Interval.interval)
async def set_another_interval(message: Message, state: FSMContext):
    interval = message.text

    try:
        interval = int(interval)
    except ValueError:
        await message.answer('отправьте только число')
        return
    
    await state.clear()
    await to_thread(set_interval_to_scheduler, message.from_user.id, interval)
    await message.answer('спасибо, теперь каждый раз когда проходит этот интервал времени '
                        'я буду присылать вам последнюю новость!')
    
@dp.message()
async def text(message: Message):
    await message.answer('не понимаю, отправьте мне команду!')

def set_interval_to_scheduler(tg_id: int, interval: int):
    if tg_id in users_jobs:
        scheduler.modify_job(users_jobs[tg_id], trigger=IntervalTrigger(hours=interval))
    else:
        job = scheduler.add_job(send_news, 'interval', hours=interval, args=[tg_id])
        users_jobs[tg_id] = job.id

async def main():
    scheduler.start() 
    from callbacks import router
    dp.include_routers(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    run(main())