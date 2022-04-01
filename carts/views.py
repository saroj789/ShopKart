from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from django.http import HttpResponse

from django.core.exceptions import ObjectDoesNotExist

# _ for making pvt fun
def _get_cart_id(request):
  cart_id = request.session.session_key
  if not cart_id:
    cart_id = request.session.create()
  return cart_id


# Create your views here.

def add_cart(request,product_id):

  product = Product.objects.get(id=product_id) #get the product
  product_variation = []

  # for color and size
  if request.method == "POST":
    for key,val in request.POST.items():
      try :
        variation = Variation.objects.get(product=product,variation_category__iexact=key, variation_value__iexact= val)
        product_variation.append(variation )
      except :
        pass

  try:
    cart = Cart.objects.get( cart_id=_get_cart_id(request) ) # get the cart using cart_id present in session
  except Cart.DoesNotExist:
    cart =Cart.objects.create( 
      cart_id = _get_cart_id(request) 
      )  # if user does not hsve cart lets create it and save it
  cart.save()  

  is_cart_item_exists =  CartItem.objects.filter(product=product, cart=cart).exists()
  print("is_cart_item_exists : ",is_cart_item_exists)

  if is_cart_item_exists:
    cart_items = CartItem.objects.filter(product=product, cart=cart)   # save product as CartItem in Cart

    #existing variation -> db
    # currunt Variation -> product_variation
    # cart_item_id  -> db

    ex_var_list =  []
    cart_items_id = []

    for item in cart_items:
      existing_variations = item.variations.all()
      ex_var_list.append( list(existing_variations))
      cart_items_id.append(item.id)

    if product_variation in ex_var_list:
      # increate the cart_item quantity
      print('inside')
      index= ex_var_list.index(product_variation)
      item_id = cart_items_id[index]
      item = CartItem.objects.get(product=product,id=item_id )
      item.quantity += 1
      item.save()
   
    else:
      # create new cart_item
      cart_item = CartItem.objects.create(
        product = product,  
        quantity = 1, 
        cart= cart    
        )
      if len(product_variation) > 0:
        cart_item.variations.clear()
        # for item in product_variation:
        #   cart_item.variations.add(item)
        cart_item.variations.add(*product_variation)
      cart_item.save()
  else:
    # create new cart_item
      cart_item = CartItem.objects.create(
        product = product,  
        quantity = 1, 
        cart= cart    
        )
      if len(product_variation) > 0:
        cart_item.variations.clear()
        cart_item.variations.add(*product_variation)
      cart_item.save()

  return redirect('cart')

 

def remove_cart(request,product_id,cart_item_id):
  cart = Cart.objects.get( cart_id = _get_cart_id(request) )
  product = get_object_or_404(Product, id=product_id)

  try :
    cart_item = CartItem.objects.get(product=product,cart=cart, id= cart_item_id)
    if cart_item.quantity > 1:
      cart_item.quantity -= 1
      cart_item.save()
    else:
      cart_item.delete()
  except:
    pass
    
  return redirect("cart")

  

def remove_cart_item(request,product_id,cart_item_id):
  cart = Cart.objects.get( cart_id = _get_cart_id(request) )
  product = get_object_or_404(Product, id=product_id)
  cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
  cart_item.delete()
  return redirect("cart")


def cart(request,total=0, quantity=0, cart_items=None):
  tax = grand_total = 0
  try: 
    cart = Cart.objects.get( cart_id=_get_cart_id(request) )
    cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('-id')
    
    for cart_item in cart_items:
      total += (cart_item.product.price * cart_item.quantity )
      quantity  +=  cart_item.quantity
    
    tax = (2 * total) / 100   # 2 % tax 
    grand_total = total + tax
  except ObjectDoesNotExist:
    pass

  context = {"total"  : total, 
          "quantity" : quantity, 
          "cart_items" : cart_items,
          'tax'   : tax,
          "grand_total" : grand_total
        }

  return render(request,'store/cart.html',context)
 