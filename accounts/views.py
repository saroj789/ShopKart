from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from orders.models import Order, OrderProduct

# varification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from .decorators import unauthenticated_user

# CHECK CART  
from carts.models import Cart, CartItem
from carts.views import _get_cart_id

# check is login request come from checkout
import requests


# Create your views here.
@unauthenticated_user
def register(request):
  if request.method == "POST":
    form = RegistrationForm(request.POST)

    
    if form.is_valid():
      first_name    = form.cleaned_data['first_name']
      last_name     = form.cleaned_data['last_name']
      email         = form.cleaned_data['email']
      phone_number  = form.cleaned_data['phone_nuber']
      password      = form.cleaned_data['password']
      username      = email.split('@')[0]

      user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password ) 
      user.phone_nuber =  phone_number
      # user.save() 

      # user activation
      current_site = get_current_site(request)
      mail_subject = 'Please activate your account'
      message      = render_to_string('accounts/account_verification_email.html', {
                  'user': user,
                  'domain': current_site,
                  'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                  'token': default_token_generator.make_token(user),
              }) 
      to_email = email
      send_email = EmailMessage(mail_subject, message, to=[to_email])

      #sometimes send email has some issue on production srver(smtplib.SMTPAuthenticationError)
      try:
        send_email.send()
        user.save()                                 # after succesfully email sent then save user
      except Exception as e:
        print('Exception : ',e)
        messages.success(request,'Some issue while creating account, please try after sometime.')
        return redirect('register')

      return redirect('/accounts/login?command=varification&email='+email)

    # do not handle else cond of is_valid(), othewiser forms.error will not work.
    # django auto handle, check user already exist or not and other thing
  
  else:
    form = RegistrationForm()
  context = {
    "form" : form
  }

  return render(request,'accounts/register.html', context)




@unauthenticated_user
def login(request):
  if request.method == "POST":
    email = request.POST['email']
    password = request.POST['password']

    user= auth.authenticate(email=email, password=password)

    if user is not None:
      #check if there is cartitems before login if yes assign to current user
      try:
        cart  = Cart.objects.get(cart_id=_get_cart_id(request))
        is_cart_item_exists =  CartItem.objects.filter(cart=cart).exists()

        if is_cart_item_exists:
          cart_items = CartItem.objects.filter(cart=cart)

          # getting the product variation list by cart_id
          variation_based_on_cart =  []
          for item in cart_items:
            variation = item.variations.all()
            variation_based_on_cart.append( list(variation))


          #  get the cart_item from user to access his product variation
          cart_items    = CartItem.objects.filter(user=user)

          # getting the product varient based on user and their id
          variation_based_on_user   = []
          cart_items_id = []
          for item in cart_items:
            existing_variations = item.variations.all()
            variation_based_on_user.append( list(existing_variations))
            cart_items_id.append(item.id)

          # now variation_based_on_card =[ 2, 4 ,6, 5]
          # variation_based_on_user =    [1,2,7,4,0]

          # get the common product_variation
          for pr in variation_based_on_cart:
            if pr in variation_based_on_user:     # same product varient already in user based cart item (or varient) then increase quantity of item
              index = variation_based_on_cart.index(pr)
              item_id = cart_items_id[index]
              item = CartItem.objects.get(id=item_id)
              item.quantity += 1
              item.user = user
              item.save()

            else:                             # product varient in cart_id_based cart but not in user based then assign it user 
              cart_items = CartItem.objects.filter(cart=cart)
              for item in cart_items:
                item.user = user
                item.save()

      except Exception as e:
        print("exception : ",e)
      #end cartitem check


      auth.login(request,user)
      messages.success(request, 'You are logged in.')

      # check prev url (if it comes from checkout page)
      url = request.META.get("HTTP_REFERER")
      try:
        query = requests.utils.urlparse(url).query       # query=    next= /cart/checkout/
        params =  dict(  x.split('=') for x in query.split('&'))     #param :  {'next': '/cart/checkout'}
        if 'next' in params:
          nextPage = params['next']
          return redirect(nextPage)
      except Exception as e:
        print("exception : ",e)

      return redirect('dashboard')
    else:
      messages.error(request, "Invalid login credentials")
      return redirect('login')


  return render(request,'accounts/login.html')


@login_required(login_url='login')
def logout(request):
  auth.logout(request)
  messages.success(request, 'You are logged out')
  return redirect('login')


def activate(request,uidb64,token):
  try:
    uid= urlsafe_base64_decode(uidb64).decode()
    user = Account._default_manager.get(pk=uid)
  except(TypeError, ValueError, Account.DoesNotExist):
    user = None
  
  if user is not None and default_token_generator.check_token(user, token):
    user.is_active = True
    user.save()
    messages.success(request, "Congratulations! Your acccount is activated")
    return redirect('login')
  else:
    messages.error(request, "Invalid activation link")
    return redirect('register')


@login_required(login_url='login')
def dashboard(request):
  orders = Order.objects.order_by('-created_at').filter(user__id=request.user.id, is_ordered=True )
  orders_count = orders.count()

  try:
    userprofile = UserProfile.objects.get(user_id = request.user.id)
  except Exception as e:
    userprofile = None

  context={
    'orders_count': orders_count,
    'userprofile' : userprofile
  }
  return render(request,'accounts/dashboard.html', context)


# @unauthenticated_user
def forgotPassword(request):
  if request.method == 'POST':
    email = request.POST['email']
    if Account.objects.filter(email=email).exists():
      user = Account.objects.get(email__iexact=email)    #  case insensitive search

      # reset password email
      current_site = get_current_site(request)
      mail_subject = 'Reset Your Password'
      message      = render_to_string('accounts/reset_password_email.html', {
                  'user': user,
                  'domain': current_site,
                  'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                  'token': default_token_generator.make_token(user),
              }) 
      to_email = email
      send_email = EmailMessage(mail_subject, message, to=[to_email])

      # sometimes send email has some issue like (smtplib.SMTPAuthenticationError)
      try:
        send_email.send()
        messages.success(request, 'password reset link has been sent to your email address.')
      except Exception as e:
        print('Exception : ',e)
        messages.error(request,'We are unable to send password reset link , please try after sometime.')

      return redirect('login')

    else:
      messages.error(request, 'Account does not exist')
      return redirect('forgotPassword')

  return render(request,'accounts/forgotPassword.html')


def resetpassword_validate(request,uidb64,token):
  try:
    uid= urlsafe_base64_decode(uidb64).decode()
    user = Account._default_manager.get(pk=uid)
  except(TypeError, ValueError, Account.DoesNotExist):
    user = None
  
  if user is not None and default_token_generator.check_token(user, token):
    request.session['uid'] = uid
    messages.success(request, "Please reset your password")
    return redirect('resetPassword')
  else:
    messages.error(request, "This link has been expired")
    return redirect('forgotPassword')


def resetPassword(request):
  if request.method == 'POST':
    password = request.POST['password']
    confirm_password = request.POST['confirm_password']

    if password == confirm_password: 
      try :                                   #mine
        uid = request.session.get('uid')
        user = Account.objects.get(pk=uid)
        print(uid,user)
        user.set_password(password)
        user.save()
        messages.success(request,'Password reset successfull')
        return redirect(login)
      except Exception as e :
        print('Exception : ',e)                                                           #mine
        messages.error(request,'something went wrong ! try to reset again')
        return redirect('forgotPassword')

    else:
      messages.error(request,'Password do not match!')
      return redirect('resetPassword')
  else:
    return render(request, 'accounts/resetPassword.html')



@login_required(login_url='login')
def my_orders(request):
  orders = Order.objects.filter(user__id=request.user.id, is_ordered=True).order_by('-created_at')
  context = {
    'orders' : orders
  }
  return render(request,'accounts/myorders.html', context)



@login_required(login_url='login')
def edit_profile(request):
  userprofile = get_object_or_404(UserProfile, user=request.user)
  if request.method == "POST":
    user_form = UserForm(request.POST, instance=request.user)
    profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
    if user_form.is_valid() and profile_form.is_valid():
      user_form.save()
      profile_form.save()

      messages.success(request,'Your profile has been updated')
      return redirect('edit_profile')
  else:
    user_form    = UserForm(instance=request.user)
    profile_form = UserProfileForm(instance= userprofile )

  context = {
    'user_form'   : user_form,
    'profile_form': profile_form,
    'userprofile' : userprofile   # passing only for profile pic
  }
  return render(request,'accounts/edit_profile.html', context)




@login_required(login_url='login')
def change_password(request):
  if request.method == "POST":
    current_password = request.POST['current_password']
    new_password = request.POST['new_password']
    confirm_password = request.POST['confirm_password']

    user = Account.objects.get(username__exact=request.user.username)
    if new_password==confirm_password:
      success = user.check_password(current_password)
      if success:
        user.set_password(new_password)
        user.save()
        messages.success(request,"Password updated successfully. ")
        
        # to logout user  # django will auto logout and redirect to login when we change password
        return redirect('home')
      else:
        messages.error(request,"Please enter valid current password.")
        return redirect('change_password')
    else:
        messages.error(request," confirm Password does not match.")
        return redirect('change_password')
    
  return render(request,'accounts/change_password.html')
  




@login_required(login_url='login')
def order_detail(request, order_id):
  order_detail = OrderProduct.objects.filter(order__order_number = order_id)
  order = Order.objects.get(order_number = order_id)
  subtotal = order.order_total - order.tax
  context = {
    'order_detail'  : order_detail,
    'order'         : order,
    'subtotal'      : subtotal
  }
  return render(request,'accounts/order_detail.html', context)
