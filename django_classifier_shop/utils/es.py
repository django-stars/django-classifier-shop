import urllib.parse
from copy import deepcopy

from django.conf import settings
from elasticsearch import Elasticsearch


def get_es():
    es = Elasticsearch(hosts=settings.ELASTICSEARCH['hosts'])
    if not es.indices.exists(settings.ELASTICSEARCH['index']):
        es.indices.create(settings.ELASTICSEARCH['index'])

    return es


class ESAggregationsUrlProcessorItem:

    def __init__(self, field, key, count, url, qs):
        self.field = field
        self.key = key
        self.count = count
        self._url = url
        self._qs = qs

    def is_selected(self):
        return self.field in self._qs and self.key in self._qs[self.field]

    def get_url(self):
        qs = deepcopy(self._qs)
        if self.is_selected():
            qs[self.field].pop(qs[self.field].index(self.key))
        else:
            if self.field not in qs:
                qs[self.field] = []
            qs[self.field].append(self.key)

        return urllib.parse.urlunparse(
            urllib.parse.ParseResult(
                self._url.scheme,
                self._url.netloc,
                self._url.path,
                self._url.params,
                urllib.parse.urlencode(qs, doseq=True),
                self._url.fragment
            )
        )

class ESAggregationsUrlProcessor:

    def __init__(self, aggs, path):
        self.aggs = aggs
        self.url = urllib.parse.urlparse(path)
        self.qs = urllib.parse.parse_qs(self.url.query)

    def __iter__(self):
        for field in sorted(self.aggs):
            yield {
                'label': field,
                'items': [
                    ESAggregationsUrlProcessorItem(
                        field,
                        bucket['key'],
                        bucket['doc_count'],
                        self.url,
                        self.qs
                    )
                    for bucket in self.aggs[field]['buckets']
                ]
            }
