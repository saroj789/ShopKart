from .models import Cart, CartItem
from .views import _get_cart_id
from django.core.exceptions import ObjectDoesNotExist


def counter(request):
  cart_count = 0
  if 'admin' in request.path:
    return {}
  else:
    try:
      cart = Cart.objects.get( cart_id=_get_cart_id(request) )
      cart_items = CartItem.objects.filter(cart=cart, is_active=True)

      for cart_item in cart_items:
        cart_count  += cart_item.quantity
    except ObjectDoesNotExist :
      cart_count = 0
  return dict(cart_count = cart_count)