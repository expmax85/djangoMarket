from PIL import Image

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model


User = get_user_model()


class MinResolutionError(Exception):
    pass


class MaxResolutionError(Exception):
    pass


class MaxSizeImageError(Exception):
    pass


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('category'))
    slug = models.SlugField(unique=True, primary_key=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name


class Product(models.Model):

    MAX_RESOLUTION = (1000, 1000)
    MIN_RESOLUTION = (300, 300)
    MAX_IMAGE_SIZE = 3145728

    title = models.CharField(max_length=255, verbose_name=_('name'))
    category = models.ForeignKey(Category, to_field='slug', verbose_name=_('category'),
                                 on_delete=models.CASCADE, related_name='related_products')
    date_added = models.DateField(verbose_name=_('date added'), auto_now_add=True)
    slug = models.SlugField(unique=True)
    rating = models.FloatField(verbose_name=_('rating'), blank=True, null=True, default=5)
    image = models.ImageField(upload_to='product_img/', verbose_name=_('image'))
    description = models.TextField(verbose_name=_('description'), null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name=_('price'))
    storage = models.ManyToManyField('Shop', through='ProductStorage')

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        img = Image.open(self.image)
        min_width, min_height = self.MIN_RESOLUTION
        max_width, max_height = self.MAX_RESOLUTION
        if img.height < min_height or img.width < min_width:
            raise MinResolutionError(
                _('resolution image is too small.')
            )
        if img.height > max_height or img.width > max_width:
            raise MaxResolutionError(
                _('resolution image is too big.')
            )
        super().save(args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'category': self.category_id, 'slug': self.slug})


class ProductImages(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_image')
    images = models.ImageField(upload_to='product_img/', verbose_name=_('image'))

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')

    def __str__(self):
        return f'images for product {self.product}'


class Shop(models.Model):
    name_shop = models.CharField(max_length=255, verbose_name=_('name by shop'))
    slug = models.SlugField(unique=True, primary_key=True)
    url = models.URLField(verbose_name=_('url shop'), null=True, default='')
    storage = models.ManyToManyField('Product', through='ProductStorage')

    class Meta:
        verbose_name = _('shop')
        verbose_name_plural = _('shops')

    def __str__(self):
        return self.name_shop


class ProductStorage(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='related_storage')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_storage')
    qty = models.PositiveSmallIntegerField(verbose_name=_('quantity'))

    class Meta:
        verbose_name = _('storage')
        verbose_name_plural = _('storages')

    def __str__(self):
        return f'storage {self.shop} by {self.product}'


class Review(models.Model):
    user_name = models.CharField(max_length=50, verbose_name=_('username'))
    email = models.EmailField(verbose_name=_('email'))
    text_review = models.TextField(verbose_name=_('text review'))
    date_review = models.DateTimeField(verbose_name=_('date review'), auto_now_add=True)
    rating = models.IntegerField(verbose_name=_('rating'), null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('related reviews'),
                                related_name='related_reviews')

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')

    def __str__(self):
        return f'review for {self.product}'


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='related_user')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_products')

    class Meta:
        verbose_name = _('wishlist')
        verbose_name_plural = _('wishlists')

    def __str__(self):
        return f'wishlist for {self.user}'


class CartProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="related_cart")
    qty = models.IntegerField(default=1, verbose_name=_('quantity'))
    summary_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name=_('price'), default=0)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

    def __str__(self):
        return f"product {self.product} for cart"


class PurchaseHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='history_product')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('customer'), related_name='buyer')
    purchase_date = models.DateField(auto_now_add=True)
    qty = models.IntegerField()

    class Meta:
        verbose_name = _('purchase')
        verbose_name_plural = _('purchases')

    def __str__(self):
        return f'purchase by {self.purchase_date}'
