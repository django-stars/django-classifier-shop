import logging
from django.apps import AppConfig
from django.conf import settings
from django.db.utils import OperationalError
from elasticsearch.exceptions import TransportError, ConnectionError

from django_classifier_shop.utils.es import get_es


logger = logging.getLogger('django_classifier_shop')


class ProductConfig(AppConfig):
    name = 'django_classifier_shop.apps.product'

    def ready(self):
        """
        redundant logic to put mapping on start of project can be replaced
        by using only on signal or `rebuild_index` management command
        """
        try:
            self.get_model('AttributeClassifierLabel').objects.exists()
        except OperationalError: # raised when migrations weren't applied
            pass
        else:
            self.create_es_mapping()

    def create_es_mapping(self):
        """
        put mapping of data to ElasticSearch
        all attributes has type `keyword` and putted into subdict to simplify
        iterate by them in template
        """
        AttributeClassifierLabel = self.get_model('AttributeClassifierLabel')

        classifier_properties = {}
        for classifier_label in AttributeClassifierLabel.objects.all():
            classifier_properties[classifier_label.label] = {'type': 'keyword'}

        body = {
            'product': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'type': 'text'},
                    'price': {'type': 'double'},
                    'attrs': {
                        'properties': classifier_properties,
                    }
                },
            },
        }

        try:
            es = get_es()
        except ConnectionError as e:
            logger.error('Can not connect to ES: {}'.format(e))
        else:
            try:
                es.indices.put_mapping(doc_type='product', body=body)
            except TransportError as e:
                es.indices.delete(settings.ELASTICSEARCH['index'])
                es.indices.create(settings.ELASTICSEARCH['index'])
                es.indices.put_mapping(doc_type='product', body=body)
