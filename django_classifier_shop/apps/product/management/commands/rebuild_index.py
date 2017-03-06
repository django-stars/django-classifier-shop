from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from django_classifier_shop.apps.product.models import (
    Product, _update_es_index
)
from django_classifier_shop.utils.es import get_es


class Command(BaseCommand):

    def handle(self, *args, **options):
        es = get_es()
        es.indices.delete(settings.ELASTICSEARCH['index'])
        es.indices.create(settings.ELASTICSEARCH['index'])

        apps.app_configs['product'].create_es_mapping()

        for product in Product.objects.all():
            _update_es_index(None, instance=product)
