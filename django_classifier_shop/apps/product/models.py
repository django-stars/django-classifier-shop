from django.conf import settings
from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from classifier.models import ClassifierAbstract, ClassifierLabelAbstract

from django_classifier_shop.utils.es import get_es


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=7, decimal_places=2)

    def get_es_data(self):
        """
        prepare data to do index in ElasticSearch
        """
        data = {
            'id': self.pk,
            'name': self.name,
            'price': float(self.price),
            'attrs': {},
        }
        for attribute in self.attributes.all():
            data['attrs'][attribute.label.label] = attribute.value

        return data


class AttributeClassifier(ClassifierAbstract):
    pass


class AttributeClassifierLabel(ClassifierLabelAbstract):
    classifier = models.ForeignKey(AttributeClassifier, related_name='labels')


class Attribute(models.Model):
    product = models.ForeignKey(Product, related_name='attributes')
    label = models.ForeignKey(AttributeClassifierLabel, related_name='+')
    value = models.CharField(max_length=500)


def _update_es_index(sender, **kwargs):
    """
    update data in ElasticSearch on product udpates
    """
    if isinstance(kwargs['instance'], Attribute):
        product = kwargs['instance'].product
    else:
        product = kwargs['instance']

    es = get_es()

    es.index(
        index=settings.ELASTICSEARCH['index'],
        doc_type='product',
        body=product.get_es_data()
    )
post_save.connect(_update_es_index, sender=Product)
post_save.connect(_update_es_index, sender=Attribute)

def _update_es_mapping(sender, **kwargs):
    """
    put new mapping for ElasticSearch on change attributes configuration
    """
    apps.app_configs['product'].create_es_mapping()
post_save.connect(
    _update_es_mapping,
    sender=AttributeClassifier,
    dispatch_uid='product__es_mapping'
)
post_save.connect(
    _update_es_mapping,
    sender=AttributeClassifierLabel,
    dispatch_uid='product__es_mapping'
)
