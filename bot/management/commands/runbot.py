from datetime import datetime
from datetime import timedelta
import logging

from django.utils import timezone
import telegram
from django.core.management.base import BaseCommand
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Updater,
    Filters,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

from bot.models import (
    Member,
    Report,
    Question,
    Event,
)

from python_meetup import settings
from bot.bot_description import (
    DESCRIPTION,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
    level=logging.INFO,
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
                member = Member.objects.create(chat_id=str(chat_id),
                                               name=username)
            if member.is_organizer:
                keyboard = [
                    [
                        InlineKeyboardButton('План мероприятия',
                                             callback_data='to_currrent'),

                        InlineKeyboardButton('Перенос докладов',
                                             callback_data='input_time'),
                    ],
                ]
            elif member.is_speaker:
                keyboard = [
                    [
                        InlineKeyboardButton('Посмотреть вопросы',
                                             callback_data='get_questions'),
                    ],
                    [
                        InlineKeyboardButton('План мероприятия',
                                             callback_data='to_currrent'),
                    ],
                    [
                        InlineKeyboardButton('О боте',
                                             callback_data='about_bot'),
                    ],
                ]
            else:
                keyboard = [
                    [
                        InlineKeyboardButton('План мероприятия',
                                             callback_data='to_currrent'),
                    ],
                    [
                        InlineKeyboardButton('О боте',
                                             callback_data='about_bot'),
                    ],
                ]
            txt = f'Здравствуйте, {username}! \nРады приветствовать Вас на нашей конференции!'
            if query:
                query.edit_message_text(
                    text=txt,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                update.message.reply_text(
                    text=txt,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            return 'MAIN_MENU'

        def input_time(update, context):
            query = update.callback_query

            now = datetime.now()
            current_report = Report.objects.filter(start_at__lte=now,
                                                   end_at__gte=now).first()
            if not current_report:
                query.answer(text="На текущий момент нет доклада.")
                return 'REPORTS'
            keyboard = [
                [InlineKeyboardButton('На главную',
                                      callback_data='to_start')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.answer()
            query.edit_message_text(
                text='Введите время в минутах на сколько хотите сдвинуть программу:',
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

            return 'INPUT_TIME'

        def get_questions(update, context):
            query = update.callback_query
            chat_id = update.effective_chat.id

            questions = Question.objects.filter(responder__chat_id=chat_id)

            keyboard = [
                [
                    InlineKeyboardButton('На главную',
                                         callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()

            if questions.exists():
                questions_text = '\n\n'.join(f'{i+1}. (Слушатель: @{quest.asker.name})\n   Вопрос: {quest.title}' for i, quest in enumerate(questions))
                message_text = f'Адресованные вам вопросы:\n\n{questions_text}'
            else:
                message_text = 'У вас пока нет адресованных вопросов.'

            query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.HTML,
            )
            return 'GET_QUESTIONS'

        def show_abilities(update, _):
            query = update.callback_query

            keyboard = [
                [
                    InlineKeyboardButton('Вернуться на главную',
                                         callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()
            query.edit_message_text(
                text=DESCRIPTION,
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            return 'ABILITIES'

        def show_conference_program(update, _):
            query = update.callback_query
            keyboard = [
                [
                    InlineKeyboardButton('Предыдущий',
                                         callback_data='to_previous'),
                    InlineKeyboardButton('Текущий',
                                         callback_data='to_currrent'),
                    InlineKeyboardButton('Следующий',
                                         callback_data='to_next'),
                ],
                [
                    InlineKeyboardButton('Программа конференции',
                                         callback_data='to_program'),
                    InlineKeyboardButton('Задать вопрос',
                                         callback_data='ask_question'),
                ],
                [
                    InlineKeyboardButton('На главную',
                                         callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.answer()

            if query.data == 'to_previous':
                now = datetime.now()
                report = Report.objects.filter(end_at__lt=now) \
                    .order_by('-end_at').first()
                if report:
                    txt = 'Доклад : {} \nДокладчик: {}\nНачало доклада: {} \nОкончание доклада: {}' \
                        .format(report.title, report.speaker,
                                timezone.localtime(report.start_at),
                                timezone.localtime(report.end_at))
                else:
                    txt = 'Докладов еще не было'
                query.edit_message_text(
                    text=txt,
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.HTML,
                )
            elif query.data == 'to_currrent':
                now = datetime.now()
                report = Report.objects.filter(start_at__lt=now,
                                               end_at__gt=now).first()
                if report:
                    txt = 'Доклад : {} \nДокладчик: {}\nНачало доклада: {} \nОкончание доклада: {}' \
                        .format(report.title, report.speaker,
                                timezone.localtime(report.start_at),
                                timezone.localtime(report.end_at))
                else:
                    txt = 'Докладов сейчас нет'
                query.edit_message_text(
                    text=txt,
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.HTML,
                )
            elif query.data == 'to_next':
                now = datetime.now()
                report = Report.objects.filter(start_at__gt=now) \
                    .order_by('start_at').first()
                if report:
                    txt = 'Доклад : {} \nДокладчик: {}\nНачало доклада: {} \nОкончание доклада: {}' \
                        .format(report.title, report.speaker,
                                timezone.localtime(report.start_at),
                                timezone.localtime(report.end_at))
                else:
                    txt = 'Докладов больше нет'
                query.edit_message_text(
                    text=txt,
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.HTML,
                )
            elif query.data == 'to_program':
                now = datetime.now()
                reports = Report.objects.all()
                txt = ''
                if reports:
                    for report in reports:
                        title = report.title
                        speaker = report.speaker
                        start_at = timezone.localtime(report.start_at).time()
                        end_at = timezone.localtime(report.end_at).time()
                        txt = f'{txt} \n{title} \n{speaker} \n{start_at} - {end_at}'
                else:
                    txt = 'Докладов нет'
                query.edit_message_text(
                    text=txt,
                    reply_markup=reply_markup,
                    parse_mode=telegram.ParseMode.HTML,
                )

            return 'REPORTS'

        def ask_question(update, context):
            query = update.callback_query
            member = Member.objects.get(chat_id=query.message.chat.id)


            now = datetime.now()
            current_report = Report.objects.filter(start_at__lte=now,
                                                   end_at__gte=now).first()
            if not current_report:
                query.answer(text="На текущий момент нет докладчика.")
                return 'REPORTS'

            responder = current_report.speaker
            responder_id = responder.id
            context.chat_data['asker'] = member.name
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

            question = Question(
                title=question_text,
                asker=asker,
                responder=responder)
            question.save()

            context.bot.send_message(chat_id=update.message.chat_id,
                                     text='Ваш вопрос сохранен')

            keyboard = [
                [InlineKeyboardButton('На главную',
                                      callback_data='to_start')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text='Спасибо за ваш вопрос!',
                                      reply_markup=reply_markup,
                                      parse_mode=telegram.ParseMode.MARKDOWN,)

            return 'MAIN_MENU'

        def shift_reports(update, context):

            try:
                minutes = int(update.message.text)
            except ValueError:
                return 'INPUT_TIME'

            now = datetime.now()
            current_report = Report.objects.filter(start_at__lt=now,
                                                   end_at__gt=now).first()
            future_reports = Report.objects.filter(start_at__gt=now)

            if current_report:
                current_report.end_at += timedelta(minutes=minutes)
                current_report.save()

            for report in future_reports:
                report.start_at += timedelta(minutes=minutes)
                report.end_at += timedelta(minutes=minutes)
                report.save()
                txt = f'Ваш доклад сдвинут на {minutes} минут!'
                try:
                    context.bot.send_message(chat_id=report.speaker.chat_id,
                                            text=txt)
                except telegram.error.BadRequest:
                    pass                            

            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('На главную', callback_data='to_start')]])

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Время всех докладов успешно сдвинуто на {minutes} минут.',
                                     reply_markup=reply_markup)
            return 'MAIN_MENU'

        def cancel(update, _):
            update.message.reply_text('До новых встреч',
                                      reply_markup=ReplyKeyboardRemove(),)
            return ConversationHandler.END

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_conversation),
                          CallbackQueryHandler(start_conversation,
                                               pattern='to_start'),
                          ],
            states={
                'MAIN_MENU': [
                    CallbackQueryHandler(show_conference_program,
                                         pattern='to_currrent'),
                    CallbackQueryHandler(get_questions,
                                         pattern='get_questions'),
                    CallbackQueryHandler(show_abilities,
                                         pattern='about_bot'),

                    CallbackQueryHandler(input_time, pattern='input_time'),
                ],
                'REPORTS': [
                    CallbackQueryHandler(show_conference_program,
                                         pattern='to_previous'),
                    CallbackQueryHandler(show_conference_program,
                                         pattern='to_currrent'),
                    CallbackQueryHandler(show_conference_program,
                                         pattern='to_next'),
                    CallbackQueryHandler(show_conference_program,
                                         pattern='to_program'),
                    CallbackQueryHandler(ask_question,
                                         pattern='ask_question'),
                    CallbackQueryHandler(start_conversation,
                                         pattern='to_start'),
                ],
                'GET_QUESTIONS': [
                    CallbackQueryHandler(start_conversation,
                                         pattern='to_start'),
                ],
                'START_MEETING': [
                    CallbackQueryHandler(start_conversation,
                                         pattern='to_start'),
                ],
                'END_MEETING': [
                    CallbackQueryHandler(start_conversation,
                                         pattern='to_start'),
                ],
                'ASK_QUESTION': [
                    CallbackQueryHandler(start_conversation,
                                         pattern='to_start'),
                ],
                'INPUT_TIME': [
                    CallbackQueryHandler(start_conversation,
                                         pattern='to_start'),
                ],
                'ABILITIES': [
                    CallbackQueryHandler(start_conversation,
                                         pattern='to_start'),
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )

        dispatcher.add_handler(conv_handler)
        start_handler = CommandHandler('start', start_conversation)
        dispatcher.add_handler(start_handler)

        dispatcher.add_handler(CallbackQueryHandler(input_time,
                                                    pattern='input_time'))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                              shift_reports))

        dispatcher.add_handler(CallbackQueryHandler(ask_question,
                                                    pattern='ask_question'))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                              save_question))

        updater.start_polling()
        updater.idle()
