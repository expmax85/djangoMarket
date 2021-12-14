from typing import Dict, Iterable

from django.core.cache import cache
from django import template

from shop.models import Category, Product

register = template.Library()
# @register.filter(is_safe=True)
# def js(obj):
#     return mark_safe(json.dumps(obj))


@register.filter(name='times')
def times(number: int) -> Iterable:
    return range(number)


@register.filter(name='progress')
def rating(dct: Dict, score: str) -> int:
    """
    Таг для расчета шкалы рейтингов
    :param dct: словарь рейтингов
    :param score: элемент словаря для расчета
    :return: процентное соотношение рейтинга dct[score] -> int
    """
    if score in dct.keys():
        return int(dct[score]/sum(dct.values()) * 100)
    else:
        return 0


@register.filter(name='value')
def value(dct: Dict, key: str) -> int:
    """
    Таг для вывода в шаблоне значений ключей в словаре
    :param dct: словарь
    :param key: ключ
    :return: значение по ключу
    """
    return dct.get(key, 0)


@register.inclusion_tag('shop/related_products.html')
def get_related_products(product: Product) -> Dict:
    """
    Таг для вывода блока связанные продукты в детальной информации о продукте
    :param product: экземпляр Product
    :return: dict-context
    """
    related_products_cache_key = 'related_products:{}'.format(product.id)
    related_products = cache.get(related_products_cache_key)
    if not related_products:
        related_products = Product.objects.select_related('category')\
                                          .filter(category=product.category)\
                                          .exclude(id=product.id)[:10]
        cache.set(related_products_cache_key, related_products, 60 * 60)
    return {'related_products': related_products}


@register.inclusion_tag('shop/searchbar.html')
def get_all_categories() -> Dict:
    """
    Таг для вывода поля search
    :return: dict-context
    """
    search_cache_key = 'search_category:list'
    categories = cache.get(search_cache_key)
    if not categories:
        categories = Category.objects.all()
        cache.set(search_cache_key, categories, 60 * 60)
    return {'categories': categories}
