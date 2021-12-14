from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.db import models


User = get_user_model()


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_('user'))
    phone_valid = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message=' '.join([str(_('Phone number must be entered in the format:')), '+999999999',
                                                   str(_('Up to 15 digits allowed.'))]))
    phone = models.CharField(max_length=16, verbose_name=_('phone number'), validators=[phone_valid],
                             null=True, blank=True)
    city = models.CharField(max_length=40, verbose_name=_('city'),
                            null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, verbose_name=_('balance'), default=0)
    loyal_group = models.CharField(max_length=50, verbose_name=_('group of loyalty'), default='None')
    qty_buy = models.PositiveIntegerField(verbose_name=_('quantity buying'), default=0)

    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')

    def __str__(self):
        return str(self.user)


class CustomerGroup(models.Model):
    name = models.CharField(_('name'), max_length=50)
    qty_buy = models.PositiveIntegerField()

    class Meta:
        verbose_name = _('group of loyalty')
        verbose_name_plural = _('groups of loyalty')

    def __str__(self):
        return self.name
