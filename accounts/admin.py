from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account,UserProfile
from django.utils.html import format_html

# Register your models here.

class AccountAdmin(UserAdmin):
  list_display = ("email", 'first_name', 'last_name', 'username', 'is_active', 'date_joined', "last_login")
  list_display_links = ("email", 'username')
  readonly_fields = ('last_login', "date_joined")
  ordering = ('-date_joined',)

  filter_horizontal = ()
  list_filter       = ()
  fieldsets         = ()

class UserProfileAdmin(admin.ModelAdmin):

  def thumbnail(self,object):
    return format_html('<img src="{}" class="img-xs icon rounded-circle" alt="user profile picture" width="30"/>'.format(object.profile_picture.url) )
  thumbnail.short_description = "Profile_Picture"

  list_display = ('thumbnail', 'user', 'city', 'state', 'country')


admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

