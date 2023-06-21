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
    Event,
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

            member = Member.objects.get(chat_id=chat_id)
            if member.is_speaker:
                keyboard = [
                    [
                        InlineKeyboardButton('Как спикер', callback_data='choose_speaker'),
                        InlineKeyboardButton('Как гость', callback_data='choose_guest'),
                    ],
                    [
                        InlineKeyboardButton('План мероприятия', callback_data='view_program'),
                    ],
                    [
                        InlineKeyboardButton('О боте', callback_data='about_bot'),
                    ],
                ]
            else:
                keyboard = [
                    [
                        InlineKeyboardButton('План мероприятия', callback_data='view_program'),
                        InlineKeyboardButton('Задать вопрос', callback_data='ask_question'),
                    ],
                    [
                        InlineKeyboardButton('О боте', callback_data='about_bot'),
                    ],
                ]

            if query:
                query.edit_message_text(
                    text=f'Здравствуйте, {username}! \nРады приветствовать Вас на нашей конференции!',
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                update.message.reply_text(
                    text=f'Здравствуйте, {username}! \nРады приветствовать Вас на нашей конференции!',
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )

            return 'MAIN_MENU'

        def choose_speaker(update, context):
            query = update.callback_query
            member = Member.objects.get(chat_id=query.message.chat.id)
            speaker_id = member.id

            context.chat_data['speaker_id'] = speaker_id
            keyboard = [
                [
                    InlineKeyboardButton('Посмотреть вопросы', callback_data='get_questions'),
                ],
                [
                    InlineKeyboardButton('На главную', callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()
            query.edit_message_text(
                text='Можете проверить задал ли вам кто-то вопрос:',
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

            return 'CHOOSE_SPEAKER'
        def get_questions(update, context):
            query = update.callback_query
            speaker_id = context.chat_data.get('speaker_id')

            questions = Question.objects.filter(responder__id=speaker_id)

            keyboard = [
                [
                    InlineKeyboardButton('На главную', callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()

            if questions.exists():
                questions_text = '\n\n'.join(f'{i+1}. (Слушатель: {quest.asker.name})\n   Вопрос: {quest.title}' for i, quest in enumerate(questions))
                message_text = f'Адресованные вам вопросы:\n\n{questions_text}'
            else:
                message_text = 'У вас пока нет адресованных вопросов.'

            query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

        def ask_question(update, context):
            query = update.callback_query
            member = Member.objects.get(chat_id=query.message.chat.id)
            asker = member.name
            responder_id = member.id
            context.chat_data['asker'] = asker
            context.chat_data['responder_id'] = responder_id

            keyboard = [
                [InlineKeyboardButton('На главную', callback_data='to_start')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.answer()
            query.edit_message_text(
                text='Введите вопрос:',
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

            return 'ASK_QUESTION'

        def save_question(update, context):
            question_text = update.message.text
            asker_name = context.chat_data.get('asker')
            responder_id = context.chat_data.get('responder_id')

            asker = Member.objects.get(name=asker_name)
            responder = Member.objects.get(id=responder_id)

            question = Question(title=question_text, asker=asker, responder=responder)
            question.save()

            context.bot.send_message(
                chat_id=update.message.chat_id,
                text='Ваш вопрос сохранен'
            )

            keyboard = [
                [InlineKeyboardButton('На главную', callback_data='to_start')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                text='Спасибо за ваш вопрос!',
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

            return 'MAIN_MENU'



        def show_conference_program(update, _):
            query = update.callback_query
            keyboard = [
                [
                    InlineKeyboardButton('Первая тема', callback_data='to_report'),
                    InlineKeyboardButton('Вторая тема', callback_data='to_report'),
                ],
                [
                    InlineKeyboardButton('Третья тема', callback_data='to_report'),
                    InlineKeyboardButton('Четвертая тема', callback_data='to_report'),
                ],
                [
                    InlineKeyboardButton('Пятая тема', callback_data='to_report'),
                    InlineKeyboardButton('Шестая тема', callback_data='to_report'),
                ],
                [
                    InlineKeyboardButton('На главную', callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()
            query.edit_message_text(
                text='Выберите интересующий Вас доклад:',
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
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
                    InlineKeyboardButton('Посмотреть вопросы', callback_data='abilities'),
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
                    InlineKeyboardButton('Список докладов', callback_data='to_reports'),
                    InlineKeyboardButton('Сделать доклад', callback_data='make_report'),
                ],
                [
                    InlineKeyboardButton('Посмотреть вопросы', callback_data='abilities'),
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
                    CallbackQueryHandler(choose_speaker, pattern='choose_speaker'),
                    CallbackQueryHandler(ask_question, pattern='ask_question'),
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                    CallbackQueryHandler(get_questions, pattern='get_questions'),
                ],
                'CHOOSE_SPEAKER': [
                    CallbackQueryHandler(get_questions, pattern='get_questions'),
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],
                'GET_QUESTIONS': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],
                'ASK_QUESTION': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
                ],
                'REPORT': [
                    CallbackQueryHandler(send_question, pattern='send_question'),
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
        dispatcher.add_handler(CallbackQueryHandler(ask_question, pattern='ask_question'))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save_question))

        updater.start_polling()
        updater.idle()
