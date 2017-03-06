from django.contrib import admin

from .models import (
    Product, AttributeClassifier, AttributeClassifierLabel, Attribute
)


class AttributeAdmin(admin.TabularInline):
    model = Attribute
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', )
    inlines = [AttributeAdmin]


class AttributeClassifierLabelAdmin(admin.TabularInline):
    model = AttributeClassifierLabel


@admin.register(AttributeClassifier)
class AttributeClassifierAdmin(admin.ModelAdmin):
    list_display = ('kind', 'labels', 'value_type', 'value_validator', )
    inlines = [AttributeClassifierLabelAdmin]

    def labels(self, obj):
        return ', '.join(obj.labels.values_list('label', flat=True))
