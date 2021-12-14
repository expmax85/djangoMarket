from datetime import timedelta, date
from typing import Dict

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import QuerySet, Count, Sum, Prefetch

from shop.models import Category, CartProduct, Shop, PurchaseHistory, Product, Wishlist, ProductStorage


class ProductsMixin:
    """
    Вспомогательный миксин для фильтров и дополнительных запросов
    """
    @classmethod
    def context_pagination(cls, request, queryset: QuerySet, size_page: int = 3) -> Paginator:
        """
        Функция для создания пагинации
        :return: Paginator
        """
        paginator = Paginator(queryset, size_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj

    @classmethod
    def get_products(cls) -> QuerySet:
        """
        Выборка всех продуктов и категорий к ним
        :return: QuerySet
        """
        products_cache_key = 'products:all'
        products = cache.get(products_cache_key)
        if not products:
            products = Product.objects.select_related('category').all()
            cache.set(products_cache_key, products, 60 * 60)
        return products

    @classmethod
    def get_categories(cls) -> QuerySet:
        """
        Выборка категорий и кол-ва товаров в них
        :return: queryset c категориями и кол-вом связанных с ними товаров
        """
        all_categories_cache_key = 'categories:all'
        all_categories = cache.get(all_categories_cache_key)
        if not all_categories:
            all_categories = Category.objects.all().annotate(num_products=Count('related_products'))
            cache.set(all_categories_cache_key, all_categories, 60 * 60)
        return all_categories

    @classmethod
    def get_shops(cls) -> QuerySet:
        """
        Выборка магазинов и кол-ва товаров в них
        :return: queryset c магазинами и кол-вом связанных с ними товаров
        """
        all_shops_cache_key = 'shops:all'
        all_shops = cache.get(all_shops_cache_key)
        if not all_shops:
            all_shops = Shop.objects.prefetch_related('storage').all()\
                                    .annotate(num_products=Count('product'))
            cache.set(all_shops_cache_key, all_shops, 60 * 60)
        return all_shops

    @classmethod
    def get_cart(cls, user_id: int, shops=False) -> Dict:
        """
        Выборка товаров в корзине. Только для аутентифицированных пользователей!
        :return: словарь с queryset c товарами в корзине
        """
        if shops:
            cart = CartProduct.objects.select_related('product')\
                                      .defer('product__description', 'product__date_added', 'product__rating')\
                                      .filter(user_id=user_id)\
                                      .prefetch_related(Prefetch('product__related_storage',
                                                          queryset=ProductStorage.objects.select_related('shop').all()))
        else:
            cart = CartProduct.objects.select_related('product')\
                                      .defer('product__description', 'product__date_added', 'product__rating')\
                                      .filter(user_id=user_id)
        result = cart.aggregate(Sum('summary_price'), Sum('qty'))
        return {'cart': cart,
                'subtotal': result['summary_price__sum'],
                'quantity': result['qty__sum']}

    @classmethod
    def clear_cart(cls, user_id: int) -> None:
        """
        Полная очиска корзины пользователя
        :param user_id: int = id пользователя
        :return: None
        """
        CartProduct.objects.filter(user_id=user_id).delete()
        return None

    @classmethod
    def get_wishlist(cls, user_id: int) -> Dict:
        """
        Выборка товаров в списке желаемого. Только для аутентифицированных пользователей!
        :return: словарь с queryset c товарами в списке желаемого
        """
        wishlist = list(Wishlist.objects.only('product_id')
                                        .filter(user_id=user_id)
                                        .values_list('product_id', flat=True))
        return {'wishlist': wishlist}

    @classmethod
    def get_last_selling(cls, days: int) -> Dict:
        """
        Выборка самых продаваемых товаров за последние days дней
        :param days: timedelta
        :return: Dict-context
        """
        temp = PurchaseHistory.objects.filter(purchase_date__gt=(date.today() - timedelta(days=days)))\
                                      .values('product_id')\
                                      .annotate(num_qty=Sum('qty'))\
                                      .order_by('-num_qty')[:20]
        last_selling_cache_key = 'last_selling:all'
        last_selling = cache.get(last_selling_cache_key)
        if not last_selling:
            last_selling = Product.objects.select_related('category')\
                                          .filter(id__in=[i['product_id'] for i in list(temp)])
            cache.set(last_selling_cache_key, last_selling, 60 * 60 * 12)

        total = dict()
        for i in list(temp):
            total[i['product_id']] = i['num_qty']
        return {'last_selling': last_selling, 'total': total}

    @classmethod
    def get_reviews(cls, request, product: Product) -> Dict:
        """
        Метод для вывода отзывов по продукту, а также расчет рейтингов - общих по блаам и среднего.
        :param request: request для извлечения текужей страницы при пагинации отзывов
        :param product: целевой экземпляр Product
        :return: словарь-контекст
        """
        context = dict()
        reviews_cache_key = 'reviews:{}'.format(product.id)
        reviews = cache.get(reviews_cache_key)
        if not reviews:
            reviews = product.related_reviews.all()
            cache.set(reviews_cache_key, reviews, 120 * 60)
        context['page_obj'] = cls.context_pagination(request, reviews)
        reviews_list = list(reviews.values('rating').order_by('rating').annotate(count_score=Count('rating')))
        rating_annotate = dict()
        for i in range(5):
            rating_annotate[str(i + 1)] = reviews_list[i]['count_score'] if i < len(list(reviews_list)) else 0
        context['dict_ratio'] = rating_annotate
        return context

    # def get_client_ip(self, request):
    # """Для анонимных пользователей извлечение ip в качестве имени"""
    #     from_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    #     if from_ip:
    #         ip = from_ip.split(',')[0]
    #     else:
    #         ip = request.META.get('REMOTE_ADDR')
    #     return ip
