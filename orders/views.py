from django.shortcuts import render, redirect
from carts.models import CartItem
from . models import Order, OrderProduct, Payment
from .forms import OrderForm
import datetime
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def payments(request):
  try:
    body = json.loads(request.body)
  except Exception as e:           #mine 
    print(e)
    return redirect('checkout')   # this method can work without @login_required 

  order = Order.objects.get(user=request.user, is_ordered = False, order_number=body['orderID'])
  # store transaction details inside payments model
  payment = Payment(
    user = request.user,
    payment_id = body['transID'],
    payment_method = body['payment_method'],
    amount_paid = order.order_total,
    status = body['status']
  )
  payment.save()

  order.payment = payment
  order.is_ordered = True
  order.save()

  # move the cart_items to OrderProduct table
  cart_items = CartItem.objects.filter(user=request.user)

  for item in cart_items:
    orderproduct          = OrderProduct()
    orderproduct.order_id = order.id
    orderproduct.payment  = payment
    orderproduct.user_id  = request.user.id
    orderproduct.product_id    = item.product_id
    orderproduct.product_price = item.product.price
    orderproduct.quantity = item.quantity
    orderproduct.ordered  = True
    orderproduct.save()
    # set the variations
    cart_item = CartItem.objects.get(id = item.id)
    product_variation = cart_item.variations.all()
    orderproduct = OrderProduct.objects.get(id=orderproduct.id)
    orderproduct.variation.set(product_variation)
    orderproduct.save()
    
    # Reduce the quantity of the sold product
    product = Product.objects.get(id=item.product.id)
    product.stock -= item.quantity
    product.save()


  # clear the cart
  CartItem.objects.filter(user=request.user).delete()


  # send order received to customer
  mail_subject = 'Thank you for your order'
  message      = render_to_string('orders/orders_received_email.html', {
        'user': request.user,
        'order': order,
    }) 
  to_email = request.user.email

  send_email = EmailMessage(mail_subject, message, to=[to_email])
  send_email.send()


  # send order no and trans ID back to sendData methon via jsonresponse
  data = {
    'order_number' : order.order_number,
    'transID'      : payment.payment_id,
  }
  return JsonResponse(data)
  # it will go back to senddata method



# generate order number
def _generate_data_number(order_id):
  yr = int( datetime.date.today().strftime('%Y') )
  dt = int( datetime.date.today().strftime('%d') )
  mt = int( datetime.date.today().strftime('%m') )
  d =  datetime.date(yr,mt,dt)
  current_date  =   d.strftime('%Y%m%d')      # 20220331 
  order_number = current_date + str(order_id)
  return order_number


@login_required(login_url='login')
def place_order(request):
  current_user = request.user

  cart_items = CartItem.objects.filter(user=current_user)   # it was giving exception if user not logged in so @login_required 
  item_count = cart_items.count()
  if item_count <=0 :
    return redirect('store')

                                                                              # same as at cart view for tax and grand total
  total=0
  tax = 0
  quantity = 0
  for cart_item in cart_items:
    total += (cart_item.product.price * cart_item.quantity)
    quantity += cart_item.quantity
  tax = (2 * total)/100
  grand_total = total + tax



  if request.method == 'POST':
    form = OrderForm(request.POST)
    print("is_valid : ", form.is_valid())
    if form.is_valid() :
      data = Order()
      data.user           = current_user
      data.first_name     = form.cleaned_data['first_name']
      data.last_name      = form.cleaned_data['last_name']
      data.email      = form.cleaned_data['email']
      data.phone          = form.cleaned_data['phone']
      data.address_line_1 = form.cleaned_data['address_line_1']
      data.address_line_2 = form.cleaned_data['address_line_2']
      data.country        = form.cleaned_data['country']
      data.state          = form.cleaned_data['state']
      data.city           = form.cleaned_data['city']
      data.order_note     = form.cleaned_data['order_note']
      
      data.order_total = grand_total
      data.tax         = tax

      data.ip          = request.META.get('REMOTE_ADDR')
      data.save()   
                                                                    # after save it will generate pk id
      order_number = _generate_data_number(data.id)
      data.order_number = order_number
      data.save()

      order      = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
      context   = {
            'order' : order,
            'cart_items' : cart_items,
            'total'      : total,
            'tax'        : tax,
            'grand_total': grand_total
      }
      print(context)

      return render(request,'orders/payments.html',context)

    else:
      for field in form:
        print("Field Error:", field.name,  field.errors)


  return redirect('payments')


@login_required(login_url='login')
def order_complete(request):
  order_number = request.GET.get('order_number')
  transID = request.GET.get('payment_id')

  try:
    order= Order.objects.get(order_number=order_number, is_ordered=True)
    ordered_products = OrderProduct.objects.filter(order_id=order.id)
    payment = Payment.objects.get(payment_id=transID)

    # subtotal=0
    # for item in ordered_products:
    #   subtotal += (item.product.price * item.quantity)
    # print(subtotal)

    subtotal = order.order_total - order.tax
    context = {
      'order' : order,
      'ordered_products' : ordered_products,
      'order_number' : order.order_number,
      'payment'       : payment,
      'subtotal'    :  subtotal
    }
    return render(request,'orders/order_complete.html', context)

  except (Payment.DoesNotExist,Order.DoesNotExist,Payment.DoesNotExist) as e :
    print(e)
    return redirect('home')
