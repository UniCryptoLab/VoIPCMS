


from django.core.management.base import BaseCommand, CommandError
from voip.libs.skype import SkypeEvent
from voip import settings

class Command(BaseCommand):
    help = 'Listen message from skype to handle'

    def handle(self, *args, **options):
        print('skype boot user:%s' % settings.SKYPE_USERNAME)
        se = SkypeEvent(settings.SKYPE_USERNAME, settings.SKYPE_PASS)
        se.loop()
