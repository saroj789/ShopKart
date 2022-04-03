from django.shortcuts import render, redirect
from .forms import RegistrationForm
from .models import Account

from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse

# varification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# from django.core import mail
from django.core.mail import send_mail


# Create your views here.

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
      user.save() 

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
      # try:
        # send_email = EmailMessage(subject=mail_subject, body=message, from_email='raj7574645@gmail.com', to=[to_email])
      # except Exception as e:
        # print("errpe : ",e)
      send_email.send()

      # messages.success(request,'Thank you for registering with us. We have sent you a varification mail to your email address. Please varify it.')
      return redirect('/accounts/login?command=varification&email='+email)


    # do not handle else cond of is_valid(), othewiser forms.error will not work.
    # django auto handle, check user already exist or anot and other thing

    # else:
    #   messages.error(request,'Invalid form')
    #   return redirect('register')
    
  
  else:
    form = RegistrationForm()
  context = {
    "form" : form
  }

  return render(request,'accounts/register.html', context)




def login(request):
  if request.method == "POST":
    email = request.POST['email']
    password = request.POST['password']

    user= auth.authenticate(email=email, password=password)

    if user is not None:
      auth.login(request,user)
      messages.success(request, 'You are logged in.')
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
  return render(request,'accounts/dashboard.html')



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
      send_email.send()

      messages.success(request, 'passwor reset email has been sent to your email address.')
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
      except:                                                             #mine
        messages.error(request,'something went wrong ! try to reset again')
        return redirect('forgotPassword')

    else:
      messages.error(request,'Password do not match!')
      return redirect('resetPassword')
  else:
    return render(request, 'accounts/resetPassword.html')
