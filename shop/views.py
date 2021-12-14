from decimal import Decimal
from typing import Callable, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Avg, Q, QuerySet
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Review, Product, ProductStorage, CartProduct, Wishlist
from .forms import ReviewForm
from .mixins import ProductsMixin


class MainPageView(ProductsMixin, ListView):
    """
    Главная страница сайта
    """
    model = Product
    template_name = 'shop/index.html'
    context_object_name = 'products'

    def get_queryset(self) -> QuerySet:
        products_order_cache_key = 'products_order:20'
        queryset = cache.get(products_order_cache_key)
        if not queryset:
            queryset = self.get_products().order_by('-date_added')[:20]
            cache.set(products_order_cache_key, queryset, 60 * 60)
        return queryset

    def get_context_data(self, *args, **kwargs) -> Dict:
        context = super().get_context_data()
        days = 10
        context['days'] = days
        context = {**context, **self.get_last_selling(days=days)}
        if self.request.user.is_authenticated:
            context = {**context, **self.get_cart(self.request.user.id),
                                  **self.get_wishlist(self.request.user)}
        return context


class ProductDetailView(ProductsMixin, DetailView):
    """
    Страница отображения детальной информации о товаре
    """
    model = Product
    context_object_name = 'product'
    template_name = 'shop/product_detail.html'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None) -> QuerySet:
        return Product.objects.select_related('category').get(slug=self.kwargs.get('slug'))

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data()
        context['offers'] = context['product'].related_storage.select_related('shop').all()
        context['bonus_images'] = context['product'].product_image.all()
        context = {**context, **self.get_reviews(self.request, context['product'])}
        if self.request.user.is_authenticated:
            context = {**context, **self.get_cart(self.request.user.id),
                                  **self.get_wishlist(self.request.user)}
        return context


class StoreView(ProductsMixin, ListView):
    """
    Базовое View для фильтрации продуктов с помощью ProductFilterView или JsonFilterStoreView
    """
    model = Product
    context_object_name = 'products'
    template_name = 'shop/store.html'
    paginate_by = 9

    def get_queryset(self) -> QuerySet:
        return self.get_products()

    def get_context_data(self, *args, **kwargs) -> Dict:
        context = super().get_context_data(*args, **kwargs)
        context['shops'] = self.get_shops()
        context['categories'] = self.get_categories()
        if self.request.user.is_authenticated:
            context = {**context, **self.get_cart(self.request.user.id),
                                  **self.get_wishlist(self.request.user)}
        return context


class ProductFilterView(ProductsMixin, ListView):
    """
    Основной фильтр товаров с полным обновлением страницы
    """
    model = Product
    context_object_name = 'products'
    template_name = 'shop/store.html'
    paginate_by = 9

    def get_queryset(self) -> QuerySet:
        price_min = Decimal(self.request.GET.get('price_min'))
        price_max = Decimal(self.request.GET.get('price_max'))
        if 'shop' in self.request.GET.keys():
            shops_list = list(ProductStorage.objects.only('product_id')
                                                    .filter(shop__in=self.request.GET.getlist('shop'))
                                                    .values_list('product_id', flat=True))
        else:
            shops_list = list(Product.objects.only('id').values_list('id', flat=True))
        if 'shop' and 'category' in self.request.GET.keys():
            queryset = Product.objects.select_related('category')\
                                      .filter(Q(category__in=self.request.GET.getlist('category')),
                                              Q(id__in=shops_list),
                                              Q(price__range=(price_min, price_max)))
        else:
            queryset = Product.objects.select_related('category')\
                                      .filter(Q(category__in=self.request.GET.getlist('category')) |
                                              Q(id__in=shops_list),
                                              Q(price__range=(price_min, price_max)))
        return queryset

    def get_context_data(self, *args, **kwargs) -> Dict:
        context = super().get_context_data(*args, **kwargs)
        context['categories'] = self.get_categories()
        context['url_category'] = ''.join([f'category={c}&' for c in self.request.GET.getlist('category')])
        context['shops'] = self.get_shops()
        context['url_shop'] = ''.join([f'shop={c}&' for c in self.request.GET.getlist('shop')])
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        context['url_prices'] = ''.join([f'price_min={price_min}&price_max={price_max}&'])
        if self.request.user.is_authenticated:
            context = {**context, **self.get_cart(self.request.user.id),
                                  **self.get_wishlist(self.request.user)}
        return context


# class JsonFilterStore(ListView):
#     """
#     Фильтр с использованием jquery, ajax и hogan для частичного обновления страницы. Отключен.
#     PS: Не доработана - после добавления пагинации отключен в пользу ProductFilterView
#     """
#     def get_queryset(self) -> QuerySet:
#         price_min = Decimal(self.request.GET.get('price_min'))
#         price_max = Decimal(self.request.GET.get('price_max'))
#         if 'shop' in self.request.GET.keys():
#             shops_list = list(ProductStorage.objects.only('product_id').filter(
#                 shop__in=self.request.GET.getlist('shop')).values_list('product_id', flat=True))
#         else:
#             shops_list = list(Product.objects.only('id').values_list('id', flat=True))
#         if 'shop' and 'category' in self.request.GET.keys():
#             queryset = Product.objects.filter(
#                 Q(category__in=self.request.GET.getlist('category')),
#                 Q(id__in=shops_list),
#                 Q(price__range=(price_min, price_max))
#             ).all().values("category", "title", "image", "price", "category_id", "slug")
#         else:
#             queryset = Product.objects.filter(
#                 Q(category__in=self.request.GET.getlist('category')) |
#                 Q(id__in=shops_list),
#                 Q(price__range=(price_min, price_max))
#             ).all().values("category", "title", "image", "price", "category_id", "slug")
#         return queryset
#
#     def get(self, request, *args, **kwargs) -> JsonResponse:
#         queryset = self.get_queryset()
#         return JsonResponse({'products': list(queryset)}, safe=False)


class SearchView(ProductsMixin, ListView):
    """
    Реализация поиска по названию продукта и/или выбранной категории в блоке сайта Search
    """
    model = Product
    context_object_name = 'products'
    template_name = 'shop/search.html'
    paginate_by = 9

    def get_queryset(self) -> QuerySet:
        title, category = self.request.GET['product_name'], self.request.GET['category_name']
        if category != 'all':
            if title:
                queryset = Product.objects.defer('description', 'date_added')\
                                          .select_related('category')\
                                          .filter(category_id=category, title__icontains=title)
            else:
                queryset = Product.objects.defer('description', 'date_added')\
                                          .select_related('category')\
                                          .filter(category_id=category)
        else:
            queryset = Product.objects.defer('description', 'date_added')\
                                      .select_related('category')\
                                      .filter(title__icontains=title)
        return queryset

    def get_context_data(self, *args, **kwargs) -> Dict:
        title, category = self.request.GET['product_name'], self.request.GET['category_name']
        context = super().get_context_data()
        if category != 'all':
            context['url_category_name'] = ''.join([f'category_name={category}&'])
        else:
            context['url_category_name'] = ''.join([f'category_name=all&'])
        context['url_product_name'] = ''.join([f'product_name={title}&'])
        if self.request.user.is_authenticated:
            context = {**context, **self.get_cart(self.request.user.id),
                                  **self.get_wishlist(self.request.user)}
        return context


class AddReview(View):
    """
    Добавление отзывов и рейтинга товаров.
    PS: Добавлять отзыв можно сколько угодно раз. Необходимо сделать проверку по ip для реализации схемы
    'один отзыв на одного юзера'. Либо заблокировать отзывы для неаутентифицированных.
    """
    @classmethod
    def post(cls, request, pk: int) -> Callable:
        form = ReviewForm(request.POST)
        product = Product.objects.only('rating').get(pk=pk)
        if form.is_valid():
            form = form.save(commit=False)
            form.product_id = pk
            form.save()
        rating = Review.objects.only('rating').filter(product_id=pk).aggregate(Avg('rating'))['rating__avg']
        if rating:
            product.rating = round(float(rating), 1)
            product.save(update_fields=['rating'])
        return redirect(product.get_absolute_url())


class AddToCart(LoginRequiredMixin, View):
    """
    Добавление товаров из корзины. Только для аутентифицированных пользователей!
    """
    @classmethod
    def get(cls, request) -> Callable:
        product_id = request.GET.get('id')
        quantity = request.GET.get('quantity', 1)
        product = Product.objects.only('price').get(id=product_id)
        user_id = request.user.id
        try:
            item = CartProduct.objects.select_related('product').get(user_id=user_id, product_id=product_id)
            item.qty += int(quantity)
            item.summary_price = product.price * item.qty
            item.save(update_fields=['summary_price', 'qty'])
        except CartProduct.DoesNotExist:
            CartProduct.objects.create(user_id=user_id, product_id=product_id,
                                       qty=quantity, summary_price=product.price)
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


class DeleteFromCart(LoginRequiredMixin, View):
    """
    Удаление товаров из корзины. Только для аутентифицированных пользователей!
    """
    @classmethod
    def get(cls, request) -> Callable:
        product_id = request.GET.get('id')
        user_id = request.user.id
        CartProduct.objects.filter(user_id=user_id, product_id=product_id).delete()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


class AddToWishList(LoginRequiredMixin, View):
    """
    Добавление и удаление продуктов wishlist. Только для аутентифицированных пользователей!
    """
    @classmethod
    def get(cls, request) -> Callable:
        product_id = request.GET.get('id')
        user_id = request.user.id
        wishlist, created = Wishlist.objects.get_or_create(user_id=user_id, product_id=product_id)
        if not created:
            wishlist.delete()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
