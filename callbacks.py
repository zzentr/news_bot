from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from asyncio import to_thread

from main import Interval, set_interval_to_scheduler

router = Router()
            
@router.callback_query(F.data.startswith('hour'))
async def set_interval(callback: CallbackQuery):
    interval = int(callback.data.split('_')[1])
    await callback.answer()
    await to_thread(set_interval_to_scheduler, callback.message.from_user.id, interval)
    await callback.message.edit_text('спасибо, теперь каждый раз когда проходит этот интервал времени '
                                     'я буду присылать вам последнюю новость!',
                                      reply_markup=None)

@router.callback_query(F.data == 'new_interval')
async def state_interval(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Interval.interval)
    await callback.message.edit_text('отправьте мне интервал в часах, только число', reply_markup=None)