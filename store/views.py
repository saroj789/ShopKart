from django.shortcuts import render, get_object_or_404, redirect
from store.models import Product, ReviewRating, ProductGallery
from category.models import Category

from carts.views import _get_cart_id
from carts.models import CartItem

from django.core.paginator import  Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib import messages
from .forms import ReviewForm
from orders.models import OrderProduct

# Create your views here.

def store(request, category_slug=None):
  category = None
  products   = None

  if category_slug != None:
    category = get_object_or_404(Category,slug=category_slug)
    products    = Product.objects.filter(category=category,is_available=True).order_by('id')
    product_count = products.count()

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
    print('exception : ',e)
    # raise e
    return redirect('store')


  # check user has purchased before or not (for giving option to give rating and review)
  if request.user.is_authenticated:  
    try:
      ordered_product = OrderProduct.objects.filter(user=request.user,product_id=single_product.id).exists()

    except OrderProduct.DoesNotExist:
      ordered_product =None
  else:
    ordered_product =None


  # get all reviws and avg rating
  reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)     # make it false when you daont want to show that review

  # get product_gallery
  product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

  context = {'single_product': single_product,
              'in_cart'     :  in_cart,
              'ordered_product': ordered_product,
              'reviews'   :  reviews,
              'product_gallery' :  product_gallery
            }
  return render(request,'store/product_detail.html',context)


def search(request):
  if 'keyword' in request.GET:
    keyword = request.GET['keyword']
    
    if keyword :
      #  complex query
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


def submit_review(request,product_id):
  url = request.META.get('HTTP_REFERER')
  if request.method == "POST":
    print('rating: ', request.POST['rating'])
    try:
      review = ReviewRating.objects.get(user__id= request.user.id, product__id= product_id)
      form = ReviewForm(request.POST, instance= review)
      form.save()
      # if we pass the instance then if there is already review then it will update it.
      # if we not pass instance it will create new review
      messages.success(request,"Thank you! Your review has been updated")
      return redirect(url)
    except ReviewRating.DoesNotExist :
      form = ReviewForm(request.POST)

      if form.is_valid():
        data = ReviewRating()
        data.subject = form.cleaned_data['subject']
        data.rating = form.cleaned_data['rating']
        print('data rating', data.rating ,' ', form.cleaned_data['rating'])
        data.review = form.cleaned_data['review']
        data.ip     = request.META.get('REMOTE_ADDR')
        data.product_id = product_id
        data.user_id = request.user.id
        data.save()
        messages.success(request,"Thank you! Your review has been updated")
        return redirect(url)

  return redirect('store')

