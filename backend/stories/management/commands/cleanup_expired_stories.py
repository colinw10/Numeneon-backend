"""
Management command to clean up expired stories.

Usage:
    python manage.py cleanup_expired_stories

Run via cron for automatic cleanup:
    0 * * * * cd /path/to/project && python manage.py cleanup_expired_stories

Or use Render's scheduled jobs, Heroku Scheduler, etc.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from stories.models import Story


class Command(BaseCommand):
    help = 'Delete expired stories (older than 24 hours)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        expired_stories = Story.objects.filter(expires_at__lt=now)
        count = expired_stories.count()

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'Would delete {count} expired stories (dry run)')
            )
            for story in expired_stories[:10]:  # Show first 10
                self.stdout.write(f'  - {story.user.username}: {story.created_at}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            deleted, _ = expired_stories.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted} expired stories')
            )
