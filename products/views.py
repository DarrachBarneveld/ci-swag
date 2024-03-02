"""Product Views"""

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, Category
from .forms import ProductForm  



from .utils import filter_and_sort_products


def all_products(request):
    """ A view to show all products, including sorting and search queries """

    products = Product.objects.all()

    filtered_products, query, categories, sort, direction, category = \
        filter_and_sort_products(products=products, request=request)

    context = {
        'products': filtered_products,
        'search_term': query,
        'current_categories': categories,
        'sort': sort,
        'direction': direction,
        'query': query,
        'category': category
    }

    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """ A view to show individual product details """

    product = get_object_or_404(Product, pk=product_id)
    related_products = (
        Product.objects.filter(category=product.category)
        .exclude(pk=product.id)
    )
    # Create pagination if too many related products
    paginator = Paginator(related_products, 4)
    page = request.GET.get('page')

    try:
        related_products = paginator.page(page)
    except PageNotAnInteger:
        related_products = paginator.page(1)
    except EmptyPage:
        # If empty page deliver last page.
        related_products = paginator.page(paginator.num_pages)

    context = {
        'product': product,
        'related_products': related_products

    }

    return render(request, 'products/product_detail.html', context)


class AddProductPage(LoginRequiredMixin, generic.CreateView):
    """
    A view for adding products to the stor
  
    """
    template_name = "products/add_product.html"
    success_url = "/"
    form_class = ProductForm

    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Product created successfully! Review in progress!")
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(
            self.request,
            "Product creation failed. Please check your input.")
        return response
