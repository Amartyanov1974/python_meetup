from datetime import datetime
from django.utils import timezone
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
            try:
                member = Member.objects.get(chat_id=str(chat_id))
            except Member.DoesNotExist:
                member = Member.objects.create(chat_id=str(chat_id),name=username)
            if member.is_organizer:
                keyboard = [
                    [
                        InlineKeyboardButton('Начало выступления', callback_data='start_meeting'),
                        InlineKeyboardButton('Конец выступления', callback_data='end_meeting'),
                    ],
                    # [
                    #     InlineKeyboardButton('Оповестить участников о новом выступлении', callback_data='view_program'),
                    # ],

                ]
            elif member.is_speaker:
                keyboard = [
                    [
                        InlineKeyboardButton('Как спикер', callback_data='choose_speaker'),
                    ],
                    [
                        InlineKeyboardButton('План мероприятия', callback_data='to_currrent'),
                    ],
                    [
                        InlineKeyboardButton('О боте', callback_data='about_bot'),
                    ],
                ]
            else:
                keyboard = [
                    [
                        InlineKeyboardButton('План мероприятия', callback_data='to_currrent'),
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
                parse_mode=telegram.ParseMode.HTML,
            )

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
                    InlineKeyboardButton('Задать вопрос', callback_data='ask_question'),
                ],
                [
                    InlineKeyboardButton('На главную', callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()
            if query.data == 'to_previous':
                now = datetime.now()
                report = Report.objects.filter(end_at__lt=now).order_by('-end_at').first()
                txt = 'Доклад : {} \nДокладчик: {}\nНачало доклада: {} \nОкончание доклада: {}'.format(report.title, report.speaker,
                                                                                           timezone.localtime(report.start_at),
                                                                                           timezone.localtime(report.end_at))
                query.edit_message_text(
                text = txt,
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.HTML,
            )
            elif query.data == 'to_currrent':
                now = datetime.now()
                report = Report.objects.filter(start_at__lt=now).order_by('-start_at').first()
                txt = 'Доклад : {} \nДокладчик: {}\nНачало доклада: {} \nОкончание доклада: {}'.format(report.title, report.speaker,
                                                                                           timezone.localtime(report.start_at),
                                                                                           timezone.localtime(report.end_at))
                query.edit_message_text(
                text = txt,
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.HTML,
            )
            elif query.data == 'to_next':
                now = datetime.now()
                report = Report.objects.filter(start_at__gt=now).order_by('start_at').first()
                txt = 'Доклад : {} \nДокладчик: {}\nНачало доклада: {} \nОкончание доклада: {}'.format(report.title, report.speaker,
                                                                                           timezone.localtime(report.start_at),
                                                                                           timezone.localtime(report.end_at))
                query.edit_message_text(
                text = txt,
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.HTML,
            )
            elif query.data == 'to_program':
                now = datetime.now()
                reports = Report.objects.all()
                txt = ''
                for report in reports:
                    txt = f'{txt} \n{report.title} \n{report.speaker} \n{timezone.localtime(report.start_at).time()} - {timezone.localtime(report.end_at).time()}'
                query.edit_message_text(
                text = txt,
                reply_markup = reply_markup,
                parse_mode = telegram.ParseMode.HTML,
            )

            return 'REPORTS'


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
                    CallbackQueryHandler(choose_speaker, pattern='choose_speaker'),
                    CallbackQueryHandler(show_abilities, pattern='about_bot'),
                ],
                'REPORTS': [
                    CallbackQueryHandler(show_conference_program, pattern='to_previous'),
                    CallbackQueryHandler(show_conference_program, pattern='to_currrent'),
                    CallbackQueryHandler(show_conference_program, pattern='to_next'),
                    CallbackQueryHandler(show_conference_program, pattern='to_program'),
                    CallbackQueryHandler(ask_question, pattern='ask_question'),
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
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
                'ABILITIES': [
                    CallbackQueryHandler(start_conversation, pattern='to_start'),
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
