"""
Seed messages management command.

Usage:
    python manage.py seed_messages          # Add sample messages
    python manage.py seed_messages --clear  # Clear existing messages first
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from messages_app.models import Message


class Command(BaseCommand):
    help = 'Seeds the database with sample messages between users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing messages before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = Message.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Cleared {deleted_count} existing messages')
            )

        # Define all conversations as list of tuples
        # (sender_username, receiver_username, content, is_read)
        conversations = [
            # Conversation 1: arthurb ↔ pabloPistola
            ('arthurb', 'pabloPistola', 'Knock-knock', True),
            ('pabloPistola', 'arthurb', "nobody's home", False),
            ('arthurb', 'pabloPistola', 'Damn', True),
            ('arthurb', 'pabloPistola', 'You still there?', False),

            # Conversation 2: nataliap ↔ pabloPistola
            ('nataliap', 'pabloPistola', "I don't know how I feel about this", True),
            ('pabloPistola', 'nataliap', "I don't feel anything", False),
            ('nataliap', 'pabloPistola', 'Hello??', False),
            ('nataliap', 'pabloPistola', 'Answer me!', False),

            # Conversation 3: colinw ↔ pabloPistola
            ('colinw', 'pabloPistola', 'What do you think?', True),
            ('pabloPistola', 'colinw', "You don't wanna know", False),
            ('colinw', 'pabloPistola', 'Bro?', True),

            # Conversation 4: crystalr ↔ pabloPistola
            ('crystalr', 'pabloPistola', "So, I think I have some typo's", False),
            ('pabloPistola', 'crystalr', 'I have dyslexia', False),

            # Conversation 5: titod ↔ pabloPistola
            ('titod', 'pabloPistola', 'Yo!', True),
            ('pabloPistola', 'titod', "You're alive!", False),
            ('titod', 'pabloPistola', 'Miss you!', False),
        ]

        created_count = 0
        errors = []

        for sender_name, receiver_name, content, is_read in conversations:
            try:
                sender = User.objects.get(username=sender_name)
                receiver = User.objects.get(username=receiver_name)
                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    content=content,
                    is_read=is_read
                )
                created_count += 1
                self.stdout.write(f'  ✓ {sender_name} → {receiver_name}: "{content[:30]}..."')
            except User.DoesNotExist as e:
                error_msg = f'User not found: {sender_name} or {receiver_name}'
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f'  ✗ {error_msg}'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} messages'))
        
        if errors:
            self.stdout.write(self.style.ERROR(f'Errors: {len(errors)}'))
            self.stdout.write('')
            self.stdout.write('Required users: pabloPistola, arthurb, nataliap, colinw, crystalr, titod')
            self.stdout.write('Make sure these users exist before running this command.')
