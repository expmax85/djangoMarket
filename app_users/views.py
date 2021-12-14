from typing import Callable

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from .forms import RegisterForm, UpBalanceForm, CustomerEditForm
from .services import create_customer, edit_customer, edit_balance, get_customer, \
    get_products_in_wishlist, customer_buy_products, write_off_goods, add_to_purchase_history
from shop.mixins import ProductsMixin
import logging


logger = logging.getLogger(__name__)


class UserLogin(LoginView):
    template_name = 'app_users/login.html'
    success_url = '/'

    def get_success_url(self):
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        logger.info(f'User {self.request.user} has authenticate on the site')
        return str(self.success_url)


class UserLogout(LogoutView):
    template_name = 'app_users/logout.html'
    next_page = '/users/login'


class RegisterView(View):
    """
    Страница регистрации нового пользователя
    """
    @classmethod
    def get(cls, request) -> Callable:
        form = RegisterForm()
        return render(request, 'app_users/register.html', context={'form': form})

    @classmethod
    def post(cls, request) -> Callable:
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = create_customer(form=form)
            login(request, user)
            return redirect(reverse('main_page'))
        form = RegisterForm()
        return render(request, 'app_users/register.html', context={'form': form})


class AccountInfoView(LoginRequiredMixin, ProductsMixin, View):
    """
    Информация об аккаунте
    """
    login_url = '/users/login/'
    template_name = 'app_users/customer_account.html'

    def get(self, request) -> Callable:
        context = dict()
        user_id = request.user.id
        user_list = self.get_wishlist(user_id)
        context['customer'] = get_customer(user_id)
        if user_list['wishlist']:
            context['products'] = get_products_in_wishlist(user_list['wishlist'])
            context['wishlist'] = user_list
        else:
            context['products'] = None
            context['wishlist'] = 0
        context = {**context, **self.get_cart(user_id)}
        return render(request, 'app_users/customer_account.html', context=context)


class CheckoutView(LoginRequiredMixin, ProductsMixin, View):
    """
    Страница оплаты товаров в корзине
    """
    login_url = '/users/login/'

    def get(self, request) -> Callable:
        context = self.get_cart(request.user.id, shops=True)
        context = {**context, **self.get_wishlist(request.user.id)}
        return render(request, 'app_users/checkout.html', context=context)


class TopUpBalanceView(LoginRequiredMixin, ProductsMixin, View):
    """
    Страница пополнения баланса
    """
    login_url = '/users/login/'

    def get(self, request) -> Callable:
        context = dict()
        user_id = request.user.id
        context['customer'] = get_customer(user_id=user_id)
        context['form'] = UpBalanceForm()
        context = {**context, **self.get_cart(user_id), **self.get_wishlist(user_id)}
        return render(request, 'app_users/upbalance.html', context=context)

    @classmethod
    def post(cls, request) -> Callable:
        form = UpBalanceForm(request.POST)
        if form.is_valid():
            edit_balance(request, form)
        return redirect(reverse('account'))


class CustomerEditView(LoginRequiredMixin, ProductsMixin, View):
    """
    Страница редактирования профиля
    """
    login_url = '/users/login/'

    def get(self, request) -> Callable:
        context = dict()
        user_id = request.user.id
        context['customer'] = get_customer(user_id=user_id)
        context['form'] = CustomerEditForm()
        context = {**context, **self.get_cart(user_id),
                              **self.get_wishlist(user_id)}
        return render(request, 'app_users/edit_customer_info.html', context=context)

    @classmethod
    def post(cls, request) -> Callable:
        form = CustomerEditForm(request.POST, request.FILES)
        if form.is_valid():
            edit_customer(request, form)
        return redirect(reverse('account'))


class PayOrderView(LoginRequiredMixin, ProductsMixin, View):
    """
    Страница покупки товаров из корзины
    """
    login_url = '/users/login/'

    @classmethod
    def get(cls, request) -> Callable:
        user_id = request.user.id
        customer = get_customer(user_id=user_id)
        context = cls.get_cart(user_id=user_id)
        if context['subtotal'] <= customer.balance:
            with transaction.atomic():
                write_off_goods(request)
                add_to_purchase_history(context['cart'], user_id)
                customer_buy_products(customer, context)
                context['cart'] = cls.clear_cart(user_id=user_id)
                logger.info(f'User {request.user} purchased {context["quantity"]} unit(s)')
        context = {**context, **cls.get_wishlist(user_id=user_id)}
        return render(request, 'app_users/pay_order.html', context=context)
