from django.core.management.base import BaseCommand
from django.core.cache import cache
from pod_shop.models import Product, Category, Brand
from django.test import RequestFactory
from pod_shop.api.views.product.listing import featured_products_view, best_selling_products_view


class Command(BaseCommand):
    help = 'Warm up the cache with frequently accessed data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting cache warmup...'))
        
        # Clear existing cache
        cache.clear()
        
        # Create a fake request for API calls
        factory = RequestFactory()
        request = factory.get('/', HTTP_HOST='jones.com')
        request.user = None
        
        try:
            # Pre-cache featured products
            self.stdout.write('Warming up featured products...')
            featured_products_view(request)
            
            # Pre-cache best selling products  
            self.stdout.write('Warming up best selling products...')
            best_selling_products_view(request)
            
            # Pre-cache categories
            self.stdout.write('Warming up categories...')
            categories = list(Category.objects.all())
            cache.set('active_categories', categories, 60 * 30)  # 30 minutes
            
            # Pre-cache brands
            self.stdout.write('Warming up brands...')
            brands = list(Brand.objects.all())
            cache.set('active_brands', brands, 60 * 30)  # 30 minutes
            
            self.stdout.write(
                self.style.SUCCESS('Cache warmup completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Cache warmup failed: {str(e)}')
            )