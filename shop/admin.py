from PIL import Image

from django.contrib import admin
from django.forms import ModelForm

from .models import *

from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ProductAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        help_text = f'Load image with sizes from {Product.MIN_RESOLUTION} to {Product.MAX_RESOLUTION} '
        self.fields['image'].help_text = mark_safe(f'<span style="color:#417690; font-size:12px;">{help_text}</span>')

    def clean_image(self):
        image = self.cleaned_data['image']
        img = Image.open(image)
        min_width, min_height = Product.MIN_RESOLUTION
        max_width, max_height = Product.MAX_RESOLUTION
        if image.size > Product.MAX_IMAGE_SIZE:
            raise ValidationError(
                _('File must be size less than 3MB')
            )
        if img.height < min_height or img.width < min_width:
            raise ValidationError(
                _('resolution image is too small.')
            )
        if img.height > max_height or img.width > max_width:
            raise ValidationError(
                _('resolution image is too big.')
            )
        return image


class ProductImagesInline(admin.StackedInline):
    model = ProductImages
    extra = 0


class ProductStorageInline(admin.StackedInline):
    model = ProductStorage
    extra = 0


@admin.register(Product)
class ProductAdminForm(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['title', 'category', 'date_added', 'rating', 'price']
    list_filter = ['category', 'date_added']
    list_display_links = ['title', ]
    inlines = [ProductImagesInline, ProductStorageInline]
    save_on_top = True


class CategoryProductsInline(admin.TabularInline):
    model = Product
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategoryProductsInline]


@admin.register(ProductStorage)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'shop', 'qty']
    list_filter = ['shop', 'product']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'rating', 'product']
    list_filter = ['product']


@admin.register(CartProduct)
class CartProductAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'qty']
    list_filter = ['user']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product']
    list_filter = ['user']


@admin.register(PurchaseHistory)
class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'purchase_date', 'qty']


admin.site.register(Shop)
