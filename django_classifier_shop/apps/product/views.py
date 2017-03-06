from django.conf import settings
from django.views.generic import ListView

from django_classifier_shop.utils.es import get_es, ESAggregationsUrlProcessor
from .models import Product, AttributeClassifierLabel


class ProductListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'product/product_list.html'

    def get(self, *args, **kwargs):
        self.es = get_es()

        return super().get(*args, **kwargs)

    def get_queryset(self):
        """
        overwrite default get_queryset to use ElasticSearch to get all data
        instead of database
        """
        results = self.es.search(
            index=settings.ELASTICSEARCH['index'],
            doc_type='product',
            body={
                'query': self._get_es_query(),
            }
        )

        # django can't use variables started with `_` in templates
        for product in results['hits']['hits']:
            product['source'] = product['_source']

        return results['hits']['hits']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aggs'] = self.get_aggregations()

        return context

    def get_aggregations(self):
        """
        get ElasticSerach terms aggregation for attributes
        https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html
        """
        results = self.es.search(
            index=settings.ELASTICSEARCH['index'],
            doc_type='product',
            body={
                'aggs': self._get_es_aggs(),
            }
        )
        return ESAggregationsUrlProcessor(
            results.get('aggregations', []),
            self.request.get_full_path()
        )

    def _get_es_aggs(self):
        aggs = {}
        for classifier_label in AttributeClassifierLabel.objects.all():
            aggs[classifier_label.label] = {
                'terms': {'field': 'attrs.{}'.format(classifier_label.label)},
            }

        return aggs

    def _get_es_query(self):
        """
        build ElasticSearch query expression to fetch all records if
        request is empty or with filtering by attributes

        https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-all-query.html
        https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-terms-query.html
        """
        query = {'match_all': {}}
        _filter = []
        for field in self.request.GET:
            _filter.append({
                'terms': {
                    'attrs.{}'.format(field): self.request.GET.getlist(field),
                }
            })

        if _filter:
            query = {
                'bool': {
                    'filter': _filter,
                },
            }

        return query
