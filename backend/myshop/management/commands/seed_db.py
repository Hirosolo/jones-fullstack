"""
Django management command to seed the database with mock data from frontend.
"""

from django.core.management.base import BaseCommand
from myshop.models import Category, Brand, ProductColor, ProductSize, Product
from django.conf import settings
import os
import re
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Seed database with mock data from frontend'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # Seed categories
        self.seed_categories()

        # Seed brands
        self.seed_brands()

        # Seed colors
        self.seed_colors()

        # Seed sizes
        self.seed_sizes()

        # Seed products
        self.seed_products()

        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))

    def seed_categories(self):
        """Seed categories from frontend"""
        self.stdout.write('Seeding categories...')

        # Hardcoded categories from frontend
        category_names = [
            'Accessories', 'Clothing', 'Footwear', 'Home Decor', 'Sale'
        ]

        for order, name in enumerate(category_names):
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'order': len(category_names) - order,
                    'desc': f'Explore our {name.lower()} collection.',
                    'meta_title': f'{name} - Jones Shop',
                    'meta_desc': f'Browse our premium {name.lower()} collection.',
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created category: {name}')
            else:
                self.stdout.write(f'  - Category already exists: {name}')

    def seed_brands(self):
        """Seed brands from frontend"""
        self.stdout.write('Seeding brands...')

        # Hardcoded brands from frontend CategoriesData.json
        brands_dict = {
            'Business': [
                'Budweiser', 'Chevrolet', 'Coca-Cola', 'Ducati', 'Grey Goose',
                'Guinness', 'Harley-Davidson', 'Indian Motorcycle', 'Jack Daniel\'s',
                'Jeep', 'Marlboro', 'Monster Energy', 'Starbucks',
                'The Famous Grouse', 'The Kraken'
            ],
            'Culture': [
                'Alpha Kappa Alpha', 'America', 'Bob Kevoian', 'Calvin and Hobbes',
                'Captain Morgan', 'Father\'s Day', 'Independence Hall', 'Mother\'s Day',
                'Peanuts', 'Route 66', 'Royal Navy', 'Smokey Bear',
                'US Marine Corps', 'US Navy', 'USA', 'Veteran Day'
            ],
            'K-Pop': [
                'Aespa', 'BTS', 'G-Dragon'
            ],
            'Movie': [
                'Avatar', 'Batman', 'Dragon Ball', 'Godzilla', 'Harry Potter',
                'James Bond 007', 'Marty Supreme', 'Naruto', 'One Piece', 'Peanut',
                'Pokémon', 'Scream', 'Star Trek', 'Star Wars', 'Stranger Things',
                'The Lord of the Rings', 'The Muppet Show', 'The Simpsons',
                'Top Gun', 'Winnie the Pooh', 'Zootopia'
            ],
            'Music': [
                'Bruce Springsteen', 'Clint Black', 'Dolly Parton', 'Elvis Presley',
                'Freddie Mercury', 'Jimmy Buffett', 'Kenny Chesney', 'Michael Jackson',
                'Prince', 'Rock the Country', 'Westlife', 'Willie Nelson'
            ],
            'Other': [
                'Animals', 'Bad Omens', 'Charlie Puth', 'Chris Brown', 'DC', 'DMX',
                'Doctor Who', 'Five Finger Death Punch', 'Foo Fighters',
                'Friday The 13th', 'G.I. Joe', 'Game of Thrones', 'Gundam',
                'House of the Dragon', 'Jujutsu Kaisen', 'Justin Bieber',
                'La La Land', 'Magic The Gathering', 'Marvel', 'Mission Impossible',
                'My Hero Academia', 'Noah Kahan', 'Pepe Aguilar', 'Phil Campbell',
                'Pirates of the Caribbean', 'Predator', 'Rat Fink', 'Slash',
                'Snoop Dogg', 'Taxi Driver', 'The Texas Chainsaw Massacre'
            ],
            'Rock Band': [
                'AC/DC', 'Aerosmith', 'Black Stone Cherry', 'Guns N\' Roses',
                'Iron Maiden', 'KISS', 'Led Zeppelin', 'Megadeth', 'Metallica',
                'Pink Floyd', 'Queen', 'RUSH', 'Sleep Token', 'The Beatles',
                'The Eagles', 'The Rolling Stones', 'Thirty Seconds to Mars',
                'Van Halen', 'Wu-Tang Clan'
            ],
            'Sport': [
                'MLB', 'NBA', 'NCAA', 'NFL', 'NHL', 'Other Sport', 'Soccer'
            ],
            'Tabletop': [
                'Dungeons & Dragons'
            ],
            'Video Game': [
                'Fallout', 'Sonic The Hedgehog', 'World of Warcraft', 'Zelda'
            ]
        }
        order = len([b for cat in brands_dict.values() for b in cat])

        for category_name, brand_list in brands_dict.items():
            for brand_name in brand_list:
                brand, created = Brand.objects.get_or_create(
                    name=brand_name,
                    defaults={
                        'order': order,
                        'desc': f'{brand_name} - Premium brand available at Jones Shop',
                        'meta_title': f'{brand_name} | Jones Shop',
                        'meta_desc': f'Discover {brand_name} products at Jones Shop. Premium quality and authentic items.',
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Created brand: {brand_name} ({category_name})')
                    order -= 1

    def seed_colors(self):
        """Seed product colors from frontend"""
        self.stdout.write('Seeding colors...')

        # Hardcoded colorways from frontend CategoriesData.json
        colorways = [
            'Black', 'White', 'Dark Mocha', 'Brown', 'University Blue Black',
            'University Blue', 'Blue', 'Chicago', 'Lucky Green', 'Pink Glaze',
            'Court Purple', 'Clay Green', 'Twist W Panda', 'Midnight Navy',
            'Yellow Toe', 'Shadow', 'Bred', 'Varsity Red', 'Black Red',
            'Fire Red', 'Denim', 'Pinksicle', 'Wolf Grey', 'Grey',
            'Multi Color', 'Signal Blue', 'Pollen'
        ]
        hex_colors = {
            'Black': '#000000',
            'White': '#FFFFFF',
            'Dark Mocha': '#5C4A3D',
            'Brown': '#8B4513',
            'University Blue Black': '#191E5C',
            'University Blue': '#003DA5',
            'Blue': '#0066FF',
            'Chicago': '#FF0000',
            'Lucky Green': '#00AA00',
            'Pink Glaze': '#FFAACC',
            'Court Purple': '#6B3FA0',
            'Clay Green': '#8FAA3D',
            'Twist W Panda': '#A9A9A9',
            'Midnight Navy': '#191970',
            'Yellow Toe': '#FFDD00',
            'Shadow': '#333333',
            'Bred': '#DC143C',
            'Varsity Red': '#FF0000',
            'Black Red': '#8B0000',
            'Fire Red': '#FF4500',
            'Denim': '#1E90FF',
            'Pinksicle': '#FF69B4',
            'Multi Color': '#FFFFFF',
            'Signal Blue': '#0080FF',
            'Pollen': '#FFFF00',
        }

        for color_name in colorways:
            color_value = color_name.lower().replace(' ', '-')
            color_code = hex_colors.get(color_name, '#CCCCCC')

            color, created = ProductColor.objects.get_or_create(
                name=color_name,
                defaults={
                    'value': color_value,
                    'color_code': color_code,
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created color: {color_name}')

    def seed_sizes(self):
        """Seed product sizes"""
        self.stdout.write('Seeding sizes...')

        sizes_data = [
            ('5.5', 'size-5.5', 0),
            ('6', 'size-6', 1),
            ('6.5', 'size-6.5', 2),
            ('7', 'size-7', 3),
            ('7.5', 'size-7.5', 4),
            ('8', 'size-8', 5),
            ('8.5', 'size-8.5', 6),
            ('9', 'size-9', 7),
            ('9.5', 'size-9.5', 8),
            ('10', 'size-10', 9),
            ('10.5', 'size-10.5', 10),
            ('11', 'size-11', 11),
            ('11.5', 'size-11.5', 12),
            ('12', 'size-12', 13),
            ('13', 'size-13', 14),
        ]

        for size_name, size_value, order in sizes_data:
            size, created = ProductSize.objects.get_or_create(
                name=size_name,
                defaults={
                    'value': size_value,
                    'order': order,
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created size: {size_name}')

    def seed_products(self):
        """Seed products from frontend MOCK_PRODUCTS"""
        self.stdout.write('Seeding products...')

        # Get default category and brand
        category = Category.objects.filter(name='Footwear').first() or Category.objects.first()
        brand = Brand.objects.first()

        if not category:
            self.stdout.write(self.style.WARNING('No category found. Create a category first.'))
            return

        # Try to load frontend mock data file
        mock_path = os.path.join(settings.BASE_DIR.parent, 'frontend', 'src', 'lib', 'mockData.ts')
        products = None

        if os.path.exists(mock_path):
            try:
                content = open(mock_path, 'r', encoding='utf-8').read()
                m = re.search(r'export\s+const\s+MOCK_PRODUCTS[^=]*=\s*(\[[\s\S]*?\]);', content)
                if m:
                    arr_text = m.group(1)

                    # Replace TypeScript enums like Gender.MEN -> "MEN"
                    arr_text = re.sub(r"\b(Gender|Category|Role)\.(\w+)", r'"\\2"', arr_text)

                    # Replace new Date().toISOString() with current ISO string
                    arr_text = re.sub(r'new\s+Date\(\)\.toISOString\(\)', '"%s"' % datetime.utcnow().isoformat(), arr_text)

                    # Quote unquoted object keys
                    arr_text = re.sub(r'(?m)^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', arr_text)

                    # Remove trailing commas before } or ]
                    arr_text = re.sub(r',\s*(\}|\])', r'\1', arr_text)

                    # Convert single quotes to double quotes
                    arr_text = arr_text.replace("'", '"')

                    # Load as JSON
                    products = json.loads(arr_text)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to parse frontend mockData.ts: {e}'))

        # Fallback if parsing failed
        if not products:
            self.stdout.write('Using fallback hardcoded products (parsing failed).')
            products = [
                {
                    'id': '1',
                    'title': 'Air Jordan High Top',
                    'price': 130.0,
                    'discount': 15,
                    'details': 'A clean high-top silhouette with premium materials and all-day comfort.',
                    'sizes': [8, 9, 10, 11, 12],
                    'color': 'Red',
                },
                {
                    'id': '2',
                    'title': 'Street Runner Mid',
                    'price': 156.0,
                    'discount': 10,
                    'details': 'Mid-top styling with a versatile profile that works with casual fits.',
                    'sizes': [6, 7, 8, 9, 10],
                    'color': 'Grey',
                },
            ]

        for p in products:
            name = p.get('title') or p.get('name')
            if not name:
                continue

            price = p.get('price') or p.get('price_origin') or 0
            discount = p.get('discount', 0) or 0
            price_promo = None
            try:
                discount_val = float(discount)
                if discount_val > 0:
                    price_promo = round(float(price) * (1 - discount_val / 100), 2)
            except Exception:
                price_promo = None

            desc = p.get('details', '')
            desc_short = (desc[:252] + '...') if len(desc) > 255 else desc

            product_category = category
            product_brand = brand

            product_obj, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'desc': desc,
                    'desc_short': desc_short or name,
                    'price_origin': float(price) if price else 0,
                    'price_promo': price_promo,
                    'stock': p.get('stock', 50),
                    'category': product_category,
                    'brand': product_brand,
                    'is_available': True,
                }
            )

            if created:
                self.stdout.write(f'  ✓ Created product: {name}')
            else:
                self.stdout.write(f'  - Product already exists: {name}')

            # Attach simple product images placeholder using mediaURLs if provided
            media_urls = p.get('mediaURLs') or p.get('mediaURLs')
            if media_urls:
                from myshop.models import ProductImage
                for idx, url in enumerate(media_urls[:5]):
                    ProductImage.objects.get_or_create(
                        product=product_obj,
                        alt=name,
                        defaults={'order': idx}
                    )

            # Create variants for sizes
            sizes = p.get('sizes') or []
            color_name = p.get('color') or ''
            color_obj = ProductColor.objects.filter(name__icontains=color_name).first() or ProductColor.objects.first()

            for size_val in sizes:
                size_obj = ProductSize.objects.filter(name=str(size_val)).first() or ProductSize.objects.first()
                if not size_obj or not color_obj:
                    continue
                from myshop.models import ProductVariant
                ProductVariant.objects.get_or_create(
                    product=product_obj,
                    size=size_obj,
                    color=color_obj,
                    defaults={
                        'price_origin': float(price) if price else None,
                        'price_promo': price_promo,
                    }
                )
