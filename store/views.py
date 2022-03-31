from django.shortcuts import render, get_object_or_404
from store.models import Product
from category.models import Category
# Create your views here.

def store(request, category_slug=None):
  category = None
  products   = None

  if category_slug != None:
    category = get_object_or_404(Category,slug=category_slug)
    print(category)
    products    = Product.objects.filter(category=category,is_available=True)
    product_count = products.count()
  else:
    products = Product.objects.all().filter(is_available=True)
    product_count = products.count()
  context= {
    'products'     :products,
    'product_count':product_count
    }
  return render(request,'store/store.html',context)


def product_detail(request,category_slug, product_slug):
  try:
    single_product = Product.objects.get( category__slug=category_slug, slug=product_slug)
  except Exception as e:
    raise e
  # category = None
  # product=None

  # if product_slug:
  #   category = get_object_or_404(Category,slug=category_slug)
  #   product    = Product.objects.filter(category=category,slug=product_slug,is_available=True)
  # else:
  #   product    = Product.objects.all()

  context = {'single_product': single_product}
  return render(request,'store/product_detail.html',context)