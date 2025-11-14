from django.contrib import admin

from .models import Video,VideoEmotions,VideoReport
admin.site.register(Video)
admin.site.register(VideoEmotions)
admin.site.register(VideoReport)