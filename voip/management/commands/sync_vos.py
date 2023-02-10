


from django.core.management.base import BaseCommand, CommandError
from voip.libs.skype import SkypeEvent
from voip import settings
from voip.models import Switch

class Command(BaseCommand):
    help = 'Sync vos data to another vos'

    def add_arguments(self, parser):
        parser.add_argument('src', type=str, help='src vos id')
        parser.add_argument('dst', type=str, help='dst vos id')

    def handle(self, *args, **kwargs):
        src_id = kwargs['src']
        dst_id = kwargs['dst']
        print('src: %s dst: %s' % (src_id, dst_id))
        src = Switch.objects.get_switch(src_id)
        customers = src.get_all_customers()
        print(customers)
        pass