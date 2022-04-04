from .models import Cart, CartItem
from .views import _get_cart_id
from django.core.exceptions import ObjectDoesNotExist


def counter(request):
  cart_count = 0
  if 'admin' in request.path:
    return {}
  else:
    try:
      if request.user.is_authenticated:
        cart_items = CartItem.objects.all().filter(user=request.user, is_active=True)
      else:
        cart = Cart.objects.filter(cart_id=_get_cart_id(request) )
        cart_items = CartItem.objects.all().filter(cart=cart[:1], is_active=True)

      for cart_item in cart_items:
        cart_count  += cart_item.quantity
    except ObjectDoesNotExist :
      cart_count = 0
  return dict(cart_count = cart_count)