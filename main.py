import logging
from enum import StrEnum, auto
from textwrap import dedent

from environs import Env
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          ConversationHandler, PicklePersistence)

logger = logging.getLogger(__name__)


class States(StrEnum):
    MENU = auto()


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> States:
    await update.message.reply_text(
        dedent('''\
        Привет! Этот бот помогает в ежедневных тренировках.
        Он умеет напоминать о том что нужно сделать зарядку,
        а так же показывает этапы её прохождения.
        ''')
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
            States.MENU: []
        },
        fallbacks=[],
        persistent=True,
        name='main_conversation'
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
