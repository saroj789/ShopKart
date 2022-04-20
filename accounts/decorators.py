from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages, auth


def unauthenticated_user(view_fun):
  def wrapper_fun(request, *args):
    if request.user.is_authenticated:
      messages.error(request, 'you are already authorized!')
      return redirect('home')
    else:
      return view_fun(request,*args)

  return wrapper_fun