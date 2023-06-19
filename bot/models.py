from django.core.exceptions import ValidationError
from django.db import models
import datetime


class Member(models.Model):
    chat_id = models.CharField(max_length=100,
                               verbose_name='ID чата участника',
                               null=True, blank=True)
    name = models.CharField(max_length=40, verbose_name='Имя участника',
                            null=True, blank=True)
    hi_speaker = models.BooleanField(default=False, verbose_name='Докладчик',)
    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self):
        return f'#{self.pk} {self.name}'


class Report(models.Model):
    title = models.CharField(max_length=40, verbose_name='Название доклада',
                             null=True, blank=True)
    speaker = models.ForeignKey(Member, on_delete=models.CASCADE,
                                verbose_name='Доклад',
                                related_name='reports')
    class Meta:
        verbose_name = 'Доклад'
        verbose_name_plural = 'Доклады'

    def __str__(self):
        return f'#{self.pk} {self.title}'


class Question(models.Model):
    title = models.TextField(max_length=200, verbose_name='Вопрос',
                             null=True, blank=True)
    asking = models.ForeignKey(Member, on_delete=models.CASCADE,
                               verbose_name='Спрашивающий',
                               related_name='my_questions')
    responsible = models.ForeignKey(Member, on_delete=models.CASCADE,
                                    verbose_name='Отвечающий',
                                    related_name='me_questions')
    published_at = models.DateTimeField("Дата и время")
    status = models.BooleanField(default=True, verbose_name='Ответили на вопрос',)
    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return f'#{self.pk} {self.title}'
