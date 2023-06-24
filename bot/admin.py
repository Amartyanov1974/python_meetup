from django.contrib import admin
from bot.models import (
    Member,
    Report,
    Question,
    Event,

)
from django.utils.translation import gettext_lazy as _


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'chat_id',
        'name',
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    ordering = ['start_at']
    list_display = (
        'title',
        'speaker',
        'start_at',
        'end_at',
    )

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'asker',
        'responder',

    )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'speakers':
            kwargs['queryset'] = Member.objects.filter(is_speaker=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
