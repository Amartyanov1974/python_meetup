from datetime import datetime
import logging
import telegram
from django.core.management.base import BaseCommand
from django.db.models import Q
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    LabeledPrice,
)
from telegram.ext import (
    Updater,
    Filters,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    PreCheckoutQueryHandler,
)

from bot.models import (
    Member,
    Report,
    Question,
)


from python_meetup import settings


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s', level=logging.INFO,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Команда для запуска телеграм-бота
    """

    def handle(self, *args, **kwargs):
        updater = Updater(token=settings.tg_token, use_context=True)
        dispatcher = updater.dispatcher

        def start_conversation(update, context):
            chat_id = update.effective_chat.id
            username = update.effective_chat.username
            query = update.callback_query

            if query:
                query.answer()
            keyboard_start = [
                [
                    InlineKeyboardButton('На главную', callback_data='to_start'),
                ],
            ]

            keyboard = [
                [
                    InlineKeyboardButton('Список докладов', callback_data='to_currrent'),
                    InlineKeyboardButton('Сделать доклад', callback_data='make_report'),
                ],
                [
                    InlineKeyboardButton('Посмотреть вопросы', callback_data='view_questions'),
                    InlineKeyboardButton('О боте', callback_data='abilities'),
                ],
            ]

            if Member.objects.filter(chat_id=chat_id).exists():
                logger.debug('Участник: %s, chat_id: %s', username, chat_id)
                if query:
                    query.edit_message_text(
                        text='Выберите интересующий вопрос:',
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                else:
                    update.message.reply_text(
                        text='Выберите интресующий вас вопрос:',
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
            else:
                if query.data == 'show_abilities':
                    update.edit_message_text(
                        text='Информация о боте, \n его возможностях',
                        reply_markup=InlineKeyboardMarkup(keyboard_start),
                    )
                else:
                     update.message.reply_text(
                        text=f'Здравствуйте, {username}! \nРады приветствовать Вас на нашей конференции!',
                        reply_markup=InlineKeyboardMarkup(keyboard_start),
                    )
                Member.objects.create(chat_id=chat_id, name=username)
            return 'MAIN_MENU'

        def show_abilities(update, _):
            query = update.callback_query

            keyboard = [
                [
                    InlineKeyboardButton('Вернуться на главную', callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()
            query.edit_message_text(
                text='Здесь будет информация о боте',
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            return 'ABILITIES'
        
        def show_conference_program(update, _):
            query = update.callback_query
            keyboard = [
                [
                    InlineKeyboardButton('Предыдущий', callback_data='to_previous'),
                    InlineKeyboardButton('Текущий', callback_data='to_currrent'),
                    InlineKeyboardButton('Следующий', callback_data='to_next'),
                ],
                [
                    InlineKeyboardButton('Программа конференции', callback_data='to_program'),
                    InlineKeyboardButton('Подробности', callback_data='to_report'),
                ],
                [
                    InlineKeyboardButton('На главную', callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()
            if query.data == 'to_previous':
                query.edit_message_text(
                text = 'Показываем предыдущий доклад',
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.MARKDOWN,
            )
            elif query.data == 'to_currrent':
                query.edit_message_text(
                text = 'Показываем текущий доклад',
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.MARKDOWN,
            )
            elif query.data == 'to_next':
                query.edit_message_text(
                text = 'Показываем следующий доклад',
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.MARKDOWN,
            )
            elif query.data == 'to_program':
                query.edit_message_text(
                text = 'Выводим программу конференции',
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.MARKDOWN,
            )

            return 'REPORTS'

        def show_report(update, _):
            query = update.callback_query

            keyboard = [
                [
                    InlineKeyboardButton('Задать вопрос', callback_data='send_question'),
                    InlineKeyboardButton('Вернуться на главную', callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()
            if query.data == 'to_report':
                query.edit_message_text(
                    text='Тема доклада: \n Докладчик:',
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.MARKDOWN,
                )
            else:
                query.edit_message_text(
                    text='Тема доклада: \n Докладчик:',
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.MARKDOWN,
                )
            return 'REPORT'

        def make_report(update, _):
            query = update.callback_query
            keyboard = [
                [
                    InlineKeyboardButton("На главный", callback_data="to_start"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="В ответном сообщении пришлите, пожалуйста, тему Вашего доклада:",
                reply_markup=reply_markup,
            )
            return 'SEND_TITLE_REPORT'


        def send_title_report(update, _):
            title_report= update.message.text
            chat_id = update.effective_chat.id
            username = update.effective_chat.username
            speaker = Member.objects.get(chat_id=chat_id)
            date = update.message.date
            Report.objects.create(title=title_report, speaker=speaker, published_at=date)
            Member.objects.filter(chat_id=chat_id).update(hi_speaker=True)
            keyboard = [
                [
                    InlineKeyboardButton('Список докладов', callback_data='to_reports'),
                    InlineKeyboardButton('Сделать доклад', callback_data='make_report'),
                ],
                [
                    InlineKeyboardButton('Посмотреть вопросы', callback_data='view_questions'),
                    InlineKeyboardButton('О боте', callback_data='abilities'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                text='✅ Спасибо! Ваш доклад поставлен в очередь! Ждите сообщение администратора!',
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )

            return 'MAIN_MENU'


        def view_questions(update, _):
            pass

        
        def send_question(update, _):
            
            query = update.callback_query
            keyboard = [
                [
                    InlineKeyboardButton("На главный", callback_data="to_start"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="В ответном сообщении пришлите, пожалуйста, Ваш вопрос:",
                reply_markup=reply_markup,
            )

            return 'THANKS_QUESTION'


        def thanks_question(update, _):
            review_text = update.message.text
            keyboard = [
                [
                    InlineKeyboardButton('Посмотреть доклады', callback_data='to_reports'),
                    InlineKeyboardButton('Сделать доклад', callback_data='make_report'),
                ],
                [
                    InlineKeyboardButton('Посмотреть вопросы', callback_data='view_questions'),
                    InlineKeyboardButton('О боте', callback_data='abilities'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                text='✅ Спасибо! Ваш вопрос отправлен докладчику!',
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )

            return 'MAIN_MENU'

        def cancel(update, _):
            user = update.message.from_user
            update.message.reply_text(
                'До новых встреч',
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_conversation),
                          CallbackQueryHandler(start_conversation, pattern='to_start'),
                          ],
            states={
                'MAIN_MENU': [
                    CallbackQueryHandler(show_conference_program, pattern='to_currrent'),
                    CallbackQueryHandler(make_report, pattern='make_report'),
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                    CallbackQueryHandler(view_questions, pattern='view_questions'),
                    CallbackQueryHandler(show_abilities, pattern='abilities'),
                ],
                'REPORTS': [
                    CallbackQueryHandler(show_conference_program, pattern='to_previous'),
                    CallbackQueryHandler(show_conference_program, pattern='to_currrent'),
                    CallbackQueryHandler(show_conference_program, pattern='to_next'),
                    CallbackQueryHandler(show_conference_program, pattern='to_program'),
                    CallbackQueryHandler(show_report, pattern='to_report'),
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],
                'REPORT': [
                    CallbackQueryHandler(send_question, pattern='send_question'),
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],
                'ABILITIES': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],
                'MAKE_REPORT': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],

                'SEND_TITLE_REPORT': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                    MessageHandler(Filters.text, send_title_report),
                ],
                'SEND_QUESTION': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],
                'THANKS_QUESTION': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                    MessageHandler(Filters.text, thanks_question),
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )

        dispatcher.add_handler(conv_handler)
        start_handler = CommandHandler('start', start_conversation)
        dispatcher.add_handler(start_handler)

        updater.start_polling()
        updater.idle()
