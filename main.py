import logging
from enum import StrEnum, auto
from textwrap import dedent

from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, PicklePersistence,
                          filters, MessageHandler)


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
    await update.message.reply_text(
        text=dedent('''\
        Привет! Этот бот помогает в ежедневных тренировках.
        Он умеет напоминать о том что нужно сделать зарядку,
        а так же показывает этапы её прохождения.
        '''),
        reply_markup=MAIN_MENU
    )
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
    print(update)

    await update.message.edit_text(
        text='Файл успешно загружен',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('Назад', callback_data='back')
        ]])
    )
    return States.ADD_TRAIN


async def handle_start_train(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> States:
    user_train = context.user_data.get('train')  # type: ignore
    if not user_train:
        await update.callback_query.edit_message_text(
            text='У тебя нет тренировки, добавь её сначала',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('Назад', callback_data='back')
            ]])
        )
        return States.TRAIN


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
                CallbackQueryHandler(handle_start_train, 'train')
            ],
            States.ADD_TRAIN: [
                MessageHandler(filters.ATTACHMENT, handle_load_train),
                CallbackQueryHandler(handle_back, 'back')
            ],
            States.TRAIN: [
                CallbackQueryHandler(handle_back, 'back')
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
