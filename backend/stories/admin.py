from django.contrib import admin
from .models import Story, StoryView, StoryReaction


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'media_type', 'created_at', 'expires_at', 'is_expired']
    list_filter = ['media_type', 'created_at']
    search_fields = ['user__username', 'caption']
    readonly_fields = ['id', 'created_at']
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ['story', 'viewer', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['viewer__username', 'story__user__username']


@admin.register(StoryReaction)
class StoryReactionAdmin(admin.ModelAdmin):
    list_display = ['story', 'user', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'story__user__username']
