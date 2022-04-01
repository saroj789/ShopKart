from django.shortcuts import render, get_object_or_404, redirect
from store.models import Product
from category.models import Category

from carts.views import _get_cart_id
from carts.models import CartItem

from django.core.paginator import  Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
# Create your views here.

def store(request, category_slug=None):
  category = None
  products   = None

  if category_slug != None:
    category = get_object_or_404(Category,slug=category_slug)
    products    = Product.objects.filter(category=category,is_available=True).order_by('id')
    product_count = products.count()

    # paginator
    paginator      =  Paginator(products, 1) 
    page           =  request.GET.get('page')
    paged_product  =  paginator.get_page(page)
  else:
    products = Product.objects.filter(is_available=True).order_by('id')
    product_count  = products.count()

    # paginator
    paginator      =  Paginator(products, 6) 
    page           =  request.GET.get('page')
    paged_product  =  paginator.get_page(page)

  context= {
    'products'     :paged_product,
    'product_count':product_count
    }
  return render(request,'store/store.html',context)


def product_detail(request,category_slug, product_slug):
  try:
    single_product = Product.objects.get( category__slug=category_slug, slug=product_slug)
    in_cart = CartItem.objects.filter( cart__cart_id=_get_cart_id(request) , product=single_product ).exists()
  except Exception as e:
    raise e

  context = {'single_product': single_product,
              'in_cart'     :  in_cart
            }
  return render(request,'store/product_detail.html',context)


def search(request):
  if 'keyword' in request.GET:
    keyword = request.GET['keyword']
    print('hii',keyword)
    if keyword :
      # ? complex query
      products = Product.objects.order_by('-created_date').filter( Q(Description__icontains = keyword) | Q(product_name__icontains = keyword)  )
      product_count  = products.count()
    else:
      return redirect('store')
  else:
      return redirect('store')
  context= {
          'products': products,
          "product_count" : product_count
        }
  return render(request,'store/store.html',context)