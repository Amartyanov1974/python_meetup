from django.contrib import admin
from django.db import transaction
from django.db.utils import IntegrityError
from bot.models import (
    Member,
    Report,
    Question,
)
from django.utils.translation import gettext_lazy as _
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s', level=logging.DEBUG,
)

logger = logging.getLogger(__name__)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_filter = (
        'hi_speaker',
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'speaker',
    )    


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    readonly_fields = (
        'published_at',
    )
