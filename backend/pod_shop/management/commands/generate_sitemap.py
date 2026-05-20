"""Django management command to generate sitemap.xml for pod_shop.

Writes to: <project_root>/static/sitemap.xml by default.

Usage:
    python manage.py generate_sitemap [--output PATH]

"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import os


from pod_shop.models import Product, Category, Brand, Tag
from articles.models import Article


def prettify_xml(elem):
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


class Command(BaseCommand):
    help = 'Generate sitemap.xml for pod_shop (products, categories, brands, tags)'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, help='Output file path for sitemap.xml')

    def handle(self, *args, **options):
        output = options.get('output') or os.path.join(settings.BASE_DIR, 'static', 'sitemap.xml')
        host = getattr(settings, 'SITE_BASE_URL', 'https://jones.com')

        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

        # Add homepage
        url = SubElement(urlset, 'url')
        loc = SubElement(url, 'loc')
        loc.text = host + '/'
        priority = SubElement(url, 'priority')
        priority.text = '1.0'

        # Products: only active (status='A')
        products = Product.objects.filter(status='A').order_by('-updated_at')
        for p in products:
            u = SubElement(urlset, 'url')
            l = SubElement(u, 'loc')
            l.text = host + p.url()
            pr = SubElement(u, 'priority')
            pr.text = '1.0'
            # lastmod
            if getattr(p, 'updated_at', None):
                lastmod = SubElement(u, 'lastmod')
                lastmod.text = p.updated_at.isoformat()

        # Categories
        for c in Category.objects.all().order_by('-order'):
            u = SubElement(urlset, 'url')
            l = SubElement(u, 'loc')
            l.text = host + c.url()
            pr = SubElement(u, 'priority')
            pr.text = '0.7'

        # Brands
        for b in Brand.objects.all().order_by('-order'):
            u = SubElement(urlset, 'url')
            l = SubElement(u, 'loc')
            l.text = host + b.url()
            pr = SubElement(u, 'priority')
            pr.text = '0.6'

        # Tags
        for t in Tag.objects.all().order_by('name'):
            u = SubElement(urlset, 'url')
            l = SubElement(u, 'loc')
            l.text = host + t.url()
            pr = SubElement(u, 'priority')
            pr.text = '0.5'

        # Articles (bài viết đã xuất bản)
        articles = Article.objects.filter(status='published').order_by('-published_at')
        for a in articles:
            u = SubElement(urlset, 'url')
            l = SubElement(u, 'loc')
            l.text = host + a.url()
            pr = SubElement(u, 'priority')
            pr.text = '0.7'
            # lastmod
            if getattr(a, 'updated_at', None):
                lastmod = SubElement(u, 'lastmod')
                lastmod.text = a.updated_at.isoformat()

        xml_str = prettify_xml(urlset)

        # Ensure output dir exists
        out_dir = os.path.dirname(output)
        os.makedirs(out_dir, exist_ok=True)

        with open(output, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        self.stdout.write(self.style.SUCCESS(f'Sitemap generated at {output}'))
