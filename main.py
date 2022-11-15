import logging
from enum import StrEnum, auto
from textwrap import dedent
from datetime import date

from environs import Env
from httpx import AsyncClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          PicklePersistence, filters)

logger = logging.getLogger(__name__)


MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton('Начать тренировку', callback_data='train')],
    [InlineKeyboardButton('Добавить тренировку', callback_data='add_train')],
])

class States(StrEnum):
    MENU = auto()
    ADD_TRAIN = auto()
    TRAIN = auto()


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> States:
    message = await update.message.reply_text(
        text=dedent('''\
        Привет! Этот бот помогает в ежедневных тренировках.
        Он умеет напоминать о том что нужно сделать зарядку,
        а так же показывает этапы её прохождения.
        '''),
        reply_markup=MAIN_MENU
    )
    context.user_data['message_id'] = message.id  # type: ignore
    return States.MENU


async def handle_add_train(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> States:
    await update.callback_query.edit_message_text(
        text='Пришли мне json-файл с описанием тренировки',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('Назад', callback_data='back')
        ]])
    )
    return States.ADD_TRAIN


async def handle_load_train(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> States:
    file = await context.bot.get_file(update.message.document.file_id)

    async with AsyncClient() as client:
        response = await client.get(file.file_path)
        response.raise_for_status()
    context.user_data['train'] = response.json()  # type: ignore

    await context.bot.edit_message_text(
        text='Файл успешно загружен',
        chat_id=update.effective_chat.id,  # type: ignore
        message_id=context.user_data['message_id'],  # type: ignore
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('Назад', callback_data='back')
        ]])
    )
    await update.message.delete()
    return States.ADD_TRAIN


async def handle_train(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> States:
    last_passed = context.user_data.get('last_passed', date.today())  # type: ignore
    if date.today() > last_passed:
        context.user_data['current_step'] = 1  # type: ignore

    user_train = context.user_data.get('train')  # type: ignore
    if not user_train:
        await update.callback_query.edit_message_text(
            text='У тебя нет тренировки, добавь её сначала',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('Назад', callback_data='back')
            ]])
        )
        return States.TRAIN


    if 'next_step' in update.callback_query.data:
        current_step = context.user_data['current_step']  # type: ignore
        context.user_data['current_step'] = current_step + 1  # type: ignore

    current_step = context.user_data.get('current_step', 1)  # type: ignore
    step = user_train.get(f'step_{current_step}')

    if not step:
        context.user_data['last_passed'] = date.today()  # type: ignore
        await update.callback_query.edit_message_text(
            text='Тренировка завершена!',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('Назад', callback_data='back')
            ]])
        )
        return States.TRAIN

    await update.callback_query.edit_message_text(
        text=dedent(f'''\
        Название: {step['title']}
        Описание: {step['description']}
        '''),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Следующий шаг', callback_data='next_step')],
            [InlineKeyboardButton('Назад', callback_data='back')]
        ])
    )
    return States.TRAIN


async def handle_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> States:
    await update.callback_query.edit_message_text(
        text=dedent('''\
        Привет! Этот бот помогает в ежедневных тренировках.
        Он умеет напоминать о том что нужно сделать зарядку,
        а так же показывает этапы её прохождения.
        '''),
        reply_markup=MAIN_MENU
    )

    return States.MENU


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    env = Env()
    env.read_env()

    persistence = PicklePersistence('data.pickle')

    application = Application\
        .builder()\
        .token(env.str('TG_BOT_TOKEN'))\
        .persistence(persistence)\
        .concurrent_updates(True)\
        .build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],
        states={
            States.MENU: [
                CallbackQueryHandler(handle_add_train, 'add_train'),
                CallbackQueryHandler(handle_train, 'train')
            ],
            States.ADD_TRAIN: [
                MessageHandler(filters.ATTACHMENT, handle_load_train),
                CallbackQueryHandler(handle_back, 'back')
            ],
            States.TRAIN: [
                CallbackQueryHandler(handle_back, 'back'),
                CallbackQueryHandler(handle_train, 'next_step')
            ]
        },
        fallbacks=[],
        persistent=True,
        name='main_conversation',
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
