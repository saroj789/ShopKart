from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from django.core.exceptions import ObjectDoesNotExist

# _ for making pvt fun
def _get_cart_id(request):
  cart_id = request.session.session_key
  if not cart_id:
    cart_id = request.session.create()
  return cart_id


# Create your views here.

def add_cart(request,product_id):

  current_user  = request.user
  product = Product.objects.get(id=product_id) #get the product

  print('is_user authenticated : ',current_user.is_authenticated)

  # (same as unauthenticating(see below), only change - cart to user)
  # IF USER IS AUTHENTICATED  
  if current_user.is_authenticated:
    product_variation = []

    # get the variation object : color and size  of current product,and append in product_variation
    if request.method == "POST":
      for key,val in request.POST.items():
        try :
          variation = Variation.objects.get(product=product,variation_category__iexact=key, variation_value__iexact= val)
          product_variation.append(variation )
        except Exception as e :
          print('Exception : ',e)

    #  check cart_items with this product (doesnt matter varient)
    is_cart_item_exists =  CartItem.objects.filter(product=product, user=current_user).exists()

    # print("Product : ",product,' product_variation : ',product_variation, "  is_cart_item_exists : ", is_cart_item_exists)
    #  if product already have in cart_item
    if is_cart_item_exists:
      cart_items = CartItem.objects.filter(product=product, user=current_user)   # save product as CartItem in Cart # get cartitems with all varient of same product

      ex_var_list =  []
      cart_items_id = []

      # get the  existing  all cart_item.id and variation object of product
      for item in cart_items:
        existing_variations = item.variations.all()
        ex_var_list.append( list(existing_variations))
        cart_items_id.append(item.id)

      # print('ex_var_list : ',ex_var_list, " cart_items_id : ",cart_items_id)
      # if product_variation is in existing product variation ,get the cart_item  using itemid and increase quantity 
      if product_variation in ex_var_list:
        index= ex_var_list.index(product_variation)
        item_id = cart_items_id[index]
        item = CartItem.objects.get(product=product,id=item_id )
        item.quantity += 1
        item.save()
        # print('item : ',item, item.quantity)

      # create new cart_item and add variation
      else:
        cart_item = CartItem.objects.create(
          product = product,  
          quantity = 1, 
          user  =  current_user   
          )
        if len(product_variation) > 0:
          cart_item.variations.clear()
          cart_item.variations.add(*product_variation)
        cart_item.save()


    # product does not have cart_item
    else:
      # create new cart_item
        cart_item = CartItem.objects.create(
          product = product,  
          quantity = 1, 
          user  =  current_user  
          )
        if len(product_variation) > 0:
          cart_item.variations.clear()
          cart_item.variations.add(*product_variation)
        cart_item.save()

    return redirect('cart')



  #  IF USER IS NOT AUTHENTICATED 
  else:

    product_variation = []

    # for color and size
    if request.method == "POST":
      for key,val in request.POST.items():
        try :
          variation = Variation.objects.get(product=product,variation_category__iexact=key, variation_value__iexact= val)
          product_variation.append(variation )
        except Exception as e :
          print('Exception : ',e)

    try:
      cart = Cart.objects.get( cart_id=_get_cart_id(request) ) # get the cart using cart_id present in session
    except Cart.DoesNotExist:
      cart =Cart.objects.create( 
        cart_id = _get_cart_id(request) 
        )                                         # if user does not hsve cart lets create it and save it with session key
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
 
  product = get_object_or_404(Product, id=product_id)

  try :
    # for auth user # no use of cart in cartitem model
    if request.user.is_authenticated:
      cart_item = CartItem.objects.get(product=product,user=request.user, id= cart_item_id)

    #  search cart_item based on cart
    else:
      cart = Cart.objects.get( cart_id = _get_cart_id(request) )
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
  product = get_object_or_404(Product, id=product_id)

  if request.user.is_authenticated:
      cart_item = CartItem.objects.get(product=product,user=request.user, id= cart_item_id)
  else:
    cart = Cart.objects.get( cart_id = _get_cart_id(request) )
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
  cart_item.delete()
  return redirect("cart")


def cart(request,total=0, quantity=0, cart_items=None):
  tax = grand_total = 0
  try: 
    
    # cartitems based on user
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True).order_by('-id')
    else:
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
 


@login_required(login_url='login')
def checkout(request):
  # same as cart   
  total=0; quantity=0; cart_items=None
  tax = grand_total = 0
  try: 

    #  user is already looged so all cartitems have assigned user(if they are added before login, they have cart also & who is added after login they dont have cart)
    # so we can get all cartitems using:

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True).order_by('-id')
    # this is never gonna execute b/z be used decorator login_required
    else:
      cart = Cart.objects.get( cart_id=_get_cart_id(request) )
      cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('-id')
    
    for cart_item in cart_items:
      total += (cart_item.product.price * cart_item.quantity )
      quantity  +=  cart_item.quantity
    
    tax = (2 * total) / 100   # 2 % tax 
    grand_total = total + tax
  except Exception as e:
    print('Exception at checkout : ',e)

  context = {"total"  : total, 
          "quantity" : quantity, 
          "cart_items" : cart_items,
          'tax'   : tax,
          "grand_total" : grand_total
        }

  return render(request,'store/checkout.html',context)