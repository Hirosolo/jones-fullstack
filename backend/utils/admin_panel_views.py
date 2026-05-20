"""
Django Admin Panel Views for Product and Article Management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
import json
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.shortcuts import resolve_url
from django.contrib.auth import logout

from myshop.models import Product, Category, Brand, Tag
from articles.models import Article, ArticleCategory, ArticleTag


def is_admin_user(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class AdminLoginView(LoginView):
    """Custom LoginView that ignores any `next` parameter and redirects
    to the configured `LOGIN_REDIRECT_URL` (admin dashboard).
    """

    def get_success_url(self):
        return resolve_url(settings.LOGIN_REDIRECT_URL)


@require_http_methods(["GET", "POST"])
def admin_logout(request):
    """Log out the user and redirect to the admin login page."""
    logout(request)
    return redirect('admin:login')


@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Main admin dashboard"""
    products_count = Product.objects.count()
    articles_count = Article.objects.count()
    
    context = {
        'products_count': products_count,
        'articles_count': articles_count,
    }
    return render(request, 'admin/dashboard.html', context)


# ==================== PRODUCT MANAGEMENT ====================

@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
def product_list(request):
    """List all products with search and pagination"""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    page = request.GET.get('page', 1)
    
    products = Product.objects.select_related('category', 'brand').prefetch_related('tags')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(slug__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    products = products.order_by('-updated_at')
    
    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(page)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    }
    return render(request, 'admin/product_list.html', context)


@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        try:
            product = Product(
                name=request.POST.get('name'),
                desc=request.POST.get('desc'),
                desc_short=request.POST.get('desc_short'),
                price_origin=float(request.POST.get('price_origin', 0)),
                price_promo=float(request.POST.get('price_promo')) if request.POST.get('price_promo') else None,
                stock=int(request.POST.get('stock', 0)),
                is_available=request.POST.get('is_available') == 'on',
                seller_notes=request.POST.get('seller_notes', ''),
                meta_title=request.POST.get('meta_title', '')[:60],
                meta_desc=request.POST.get('meta_desc', '')[:145],
                admin_notes=request.POST.get('admin_notes', ''),
            )
            
            category_id = request.POST.get('category')
            if category_id:
                product.category_id = category_id
            
            brand_id = request.POST.get('brand')
            if brand_id:
                product.brand_id = brand_id
            
            product.save()
            
            # Add tags
            tag_ids = request.POST.getlist('tags')
            if tag_ids:
                product.tags.set(tag_ids)
            
            return redirect('admin:product_detail', pk=product.id)
        except Exception as e:
            context = {
                'error': str(e),
                'categories': Category.objects.all(),
                'brands': Brand.objects.all(),
                'tags': Tag.objects.all(),
            }
            return render(request, 'admin/product_form.html', context)
    
    context = {
        'categories': Category.objects.all(),
        'brands': Brand.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'admin/product_form.html', context)


@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
def product_detail(request, pk):
    """View product details"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.desc = request.POST.get('desc')
            product.desc_short = request.POST.get('desc_short')
            product.price_origin = float(request.POST.get('price_origin', 0))
            product.price_promo = float(request.POST.get('price_promo')) if request.POST.get('price_promo') else None
            product.stock = int(request.POST.get('stock', 0))
            product.is_available = request.POST.get('is_available') == 'on'
            product.seller_notes = request.POST.get('seller_notes', '')
            product.meta_title = request.POST.get('meta_title', '')[:60]
            product.meta_desc = request.POST.get('meta_desc', '')[:145]
            product.admin_notes = request.POST.get('admin_notes', '')
            
            category_id = request.POST.get('category')
            product.category_id = category_id if category_id else None
            
            brand_id = request.POST.get('brand')
            product.brand_id = brand_id if brand_id else None
            
            product.save()
            
            # Update tags
            tag_ids = request.POST.getlist('tags')
            product.tags.set(tag_ids)
            
            return redirect('admin:product_detail', pk=product.id)
        except Exception as e:
            context = {
                'product': product,
                'categories': Category.objects.all(),
                'brands': Brand.objects.all(),
                'tags': Tag.objects.all(),
                'error': str(e),
            }
            return render(request, 'admin/product_form.html', context)
    
    context = {
        'product': product,
        'categories': Category.objects.all(),
        'brands': Brand.objects.all(),
        'tags': Tag.objects.all(),
    }
    return render(request, 'admin/product_form.html', context)


@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
@require_http_methods(["POST"])
def product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('admin:product_list')


# ==================== ARTICLE MANAGEMENT ====================

@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
def article_list(request):
    """List all articles with search and pagination"""
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    page = request.GET.get('page', 1)
    
    articles = Article.objects.select_related('category').prefetch_related('tags')
    
    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(slug__icontains=query) |
            Q(code__icontains=query)
        )
    
    if status:
        articles = articles.filter(status=status)
    
    articles = articles.order_by('-updated_at')
    
    paginator = Paginator(articles, 20)
    page_obj = paginator.get_page(page)
    
    context = {
        'page_obj': page_obj,
        'articles': page_obj.object_list,
        'query': query,
        'status': status,
    }
    return render(request, 'admin/article_list.html', context)


@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
def article_create(request):
    """Create new article"""
    if request.method == 'POST':
        try:
            article = Article(
                title=request.POST.get('title'),
                excerpt=request.POST.get('excerpt', ''),
                content=request.POST.get('content', ''),
                featured_image_url=request.POST.get('featured_image_url', ''),
                author_name=request.POST.get('author_name', ''),
                status=request.POST.get('status', 'draft'),
                featured=request.POST.get('featured') == 'on',
                meta_title=request.POST.get('meta_title', '')[:60],
                meta_desc=request.POST.get('meta_desc', '')[:145],
            )
            
            category_id = request.POST.get('category')
            if category_id:
                article.category_id = category_id
            
            article.save()
            
            # Add tags
            tag_ids = request.POST.getlist('tags')
            if tag_ids:
                article.tags.set(tag_ids)
            
            return redirect('admin:article_detail', pk=article.id)
        except Exception as e:
            context = {
                'error': str(e),
                'categories': ArticleCategory.objects.all(),
                'tags': ArticleTag.objects.all(),
            }
            return render(request, 'admin/article_form.html', context)
    
    context = {
        'categories': ArticleCategory.objects.all(),
        'tags': ArticleTag.objects.all(),
    }
    return render(request, 'admin/article_form.html', context)


@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
def article_detail(request, pk):
    """View/Edit article details"""
    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        try:
            article.title = request.POST.get('title')
            article.excerpt = request.POST.get('excerpt', '')
            article.content = request.POST.get('content', '')
            article.featured_image_url = request.POST.get('featured_image_url', '')
            article.author_name = request.POST.get('author_name', '')
            article.status = request.POST.get('status', 'draft')
            article.featured = request.POST.get('featured') == 'on'
            article.meta_title = request.POST.get('meta_title', '')[:60]
            article.meta_desc = request.POST.get('meta_desc', '')[:145]
            
            category_id = request.POST.get('category')
            article.category_id = category_id if category_id else None
            
            article.save()
            
            # Update tags
            tag_ids = request.POST.getlist('tags')
            article.tags.set(tag_ids)
            
            return redirect('admin:article_detail', pk=article.id)
        except Exception as e:
            context = {
                'article': article,
                'categories': ArticleCategory.objects.all(),
                'tags': ArticleTag.objects.all(),
                'error': str(e),
            }
            return render(request, 'admin/article_form.html', context)
    
    context = {
        'article': article,
        'categories': ArticleCategory.objects.all(),
        'tags': ArticleTag.objects.all(),
    }
    return render(request, 'admin/article_form.html', context)


@login_required(login_url='admin:login')
@user_passes_test(is_admin_user)
@require_http_methods(["POST"])
def article_delete(request, pk):
    """Delete article"""
    article = get_object_or_404(Article, pk=pk)
    article.delete()
    return redirect('admin:article_list')
