import logging
from typing import Dict, Union, List, Callable

from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import transaction
from django.db.models import QuerySet
from django.forms import forms

from shop.models import Product, ProductStorage, PurchaseHistory
from .models import Customer, CustomerGroup


logger = logging.getLogger(__name__)


def create_customer(form: forms) -> Callable:
    """
    создание новго профиля Customer
    :param form: заполненная форма с полями профиля и пользователя
    :return: перенаправление на аутентификацию
    """
    user = form.save()
    phone = form.cleaned_data['phone']
    city = form.cleaned_data['city']
    Customer.objects.create(user=user, phone=phone, city=city)
    return _get_auth_user(form)


def _get_auth_user(form: forms) -> Callable:
    """
    Автоматическая аутентификация пользователя после регистрации
    :param form: форма с полями для аутентификации
    :return: аутентификация на сайте
    """
    username = form.cleaned_data['username']
    raw_password = form.cleaned_data['password1']
    return authenticate(username=username, password=raw_password)


def edit_customer(request, form: forms) -> None:
    """
    Редактирование и сохранение данных покупателя
    :param request: запрос для извлечения id пользователя
    :param form: заполненная форма с измененными данными
    :return: None
    """
    customer = get_customer(user_id=request.user.id)
    customer.user.first_name = form.cleaned_data['first_name']
    customer.user.last_name = form.cleaned_data['last_name']
    customer.user.email = form.cleaned_data['email']
    customer.phone = form.cleaned_data['phone']
    customer.city = form.cleaned_data['city']
    customer.user.save()
    customer.save()


@transaction.atomic()
def edit_balance(request, form: forms) -> None:
    """
    Пополнение и сохранение баланса пользователя
    :param request: запрос для извлечения id пользователя
    :param form: заполненная форма с суммой пополнения
    :return: None
    """
    customer = get_customer(user_id=request.user.id)
    customer.balance += form.cleaned_data['balance']
    customer.save(update_fields=['balance'])
    logger.info(f'User {request.user} update his balance on {form.cleaned_data["balance"]}')


def get_customer(user_id: int) -> Customer:
    """
    Функция получения профиля(Customer) пользователя
    :param user_id: id пользователя
    :return: Экземпляр Customer - профиль пользователя
    """
    return Customer.objects.select_related('user').get(user_id=user_id)


def _get_group_list() -> List:
    """
    Получение списка групп лояльности с сортировкой по кол-ву купленных товаров
    :return: список групп
    """
    group_list_cache_key = 'groups:all'
    group_list = cache.get(group_list_cache_key)
    if not group_list:
        group_list = sorted(list(CustomerGroup.objects.values()), key=lambda x: x['qty_buy'])
        cache.set(group_list_cache_key, group_list, 60 * 60)
    return group_list


def _up_level(customer: Customer) -> Union[str, None]:
    """
    Повышение уровня лояльности пользователя
    :param customer: профиль пользователя
    :return: Ничего, если уже максимальный уровень или не выполненые условия повышения;
    при повышении уровня возвращает новый уровень лояльности
    """
    group_list = _get_group_list()
    if customer.qty_buy in range(group_list[0]['qty_buy'], group_list[-1]['qty_buy'] + 1):
        for group in group_list:
            if customer.qty_buy <= group['qty_buy']:
                logger.info(f'User {customer.user} update his level to {group["name"]}')
                return group['name']
    else:
        return None


def customer_buy_products(customer: Customer, context: Dict) -> None:
    """
    Покупка товаров из корзины с вычетом общей стоимости из баланса, а также прибавлением в профиль кол-ва товаров
    :param customer: экземпляр покупателя Customer
    :param context: словарь с данными по покупке
    :return: None
    """
    customer.balance -= context['subtotal']
    customer.qty_buy += context['quantity']
    level = _up_level(customer)
    if level:
        customer.loyal_group = level
        customer.save(update_fields=['balance', 'qty_buy', 'loyal_group'])
    else:
        customer.save(update_fields=['balance', 'qty_buy'])


def write_off_goods(request) -> None:
    """
    Функция вычета купленных товаров со складов выбранных магазинов
    :param request: запрос с информацией по купленным товарам(магазины и кол-ва),
    информация подается через input-hidden шаблона страницы покупки
    :return: None
    """
    storage_list, qty_list = [], []
    for item in request.GET.values():
        storage_id, qty = item.split('~')
        storage_list.append(int(storage_id))
        qty_list.append(int(qty))
    all_storages = ProductStorage.objects.only('qty').filter(id__in=storage_list)
    for storage in enumerate(all_storages):
        storage[1].qty -= qty_list[storage[0]]
    ProductStorage.objects.bulk_update(all_storages, fields=['qty'])


def add_to_purchase_history(cart: QuerySet, user_id: int) -> None:
    """
    Занесение покупок в историю покупок
    :param cart: корзина с купленными товарами
    :param user_id: id покупателя
    :return: None
    """
    PurchaseHistory.objects.bulk_create([PurchaseHistory(product_id=item.product.id,
                                                         user_id=user_id,
                                                         qty=item.qty) for item in cart])


def get_products_in_wishlist(wishlist: List) -> QuerySet:
    """
    Получение списка товаров в wishlist'е пользователя для их отображения на странице профиля
    :param wishlist: список с id товаров
    :return: QuerySet
    """
    return Product.objects.select_related('category')\
                          .defer('description', 'date_added')\
                          .filter(id__in=wishlist)
