import random

from django.core.management.base import BaseCommand
from shop.models import Product, Category


class Command(BaseCommand):

    def handle(self, *args, **options):
        last = Product.objects.last()
        categories = list(Category.objects.values_list('slug', flat=True))
        Product.objects.bulk_create([
                                Product(title=''.join(['product_', str(i)]),
                                        category_id=random.choice(categories),
                                        slug=''.join(['product_', str(i)]),
                                        price=random.randrange(2000, 50000, 1500))
                                    for i in range(int(last.id) + 1, 1500)
                                    ])
        self.stdout.write(self.style.SUCCESS('Successfully added products'))
