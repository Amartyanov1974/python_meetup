from django.db import models


class Member(models.Model):
    chat_id = models.CharField(max_length=100,
                               verbose_name='ID чата участника',
                               null=True, blank=True)
    name = models.CharField(max_length=40, verbose_name='Имя участника',
                            null=True, blank=True)
    is_speaker = models.BooleanField(default=False, verbose_name='Докладчик', )
    is_organizer = models.BooleanField(default=False, verbose_name='Организатор', )
    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self):
        return self.name if self.name else "Unnamed member"


class Report(models.Model):
    title = models.CharField(max_length=40, verbose_name='Название доклада',
                             null=True, blank=True)
    speaker = models.ForeignKey(Member, on_delete=models.CASCADE,
                                verbose_name='Докладчик',
                                related_name='reports',
                                limit_choices_to={'is_speaker': True})
    start_at = models.DateTimeField("Начало доклада", null=True, blank=True)
    end_at = models.DateTimeField("Конец доклада", null=True, blank=True)

    class Meta:
        verbose_name = 'Доклад'
        verbose_name_plural = 'Доклады'

    def __str__(self):
        return f'#{self.pk} {self.title}'


class Question(models.Model):
    title = models.TextField(max_length=200, verbose_name='Вопрос',
                             null=True, blank=True)
    asker = models.ForeignKey(Member, on_delete=models.CASCADE,
                              verbose_name='Задавший вопрос',
                              related_name='asked_questions',
                              null=True, blank=True)
    responder = models.ForeignKey(Member, on_delete=models.CASCADE,
                                  verbose_name='Отвечающий',
                                  related_name='answered_questions')
    report = models.ForeignKey(Report, on_delete=models.CASCADE, verbose_name='Презентация',
                               related_name='questions',
                               null=True, blank=True)

    is_answered = models.BooleanField(default=False, verbose_name='Вопрос отвечен')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return f'#{self.pk} {self.title}' if self.title else f'#{self.pk}'


class Event(models.Model):
    date = models.DateField(verbose_name='Дата мероприятия')
    location = models.CharField(max_length=100, verbose_name='Место проведения')
    speakers = models.ManyToManyField(Member, verbose_name='Список спикеров', related_name='events')
    program = models.TextField(verbose_name='Программа мероприятия')

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

    def __str__(self):
        return f'#{self.pk} {self.date}'
