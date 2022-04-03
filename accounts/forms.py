from django import forms
from .models import Account


class RegistrationForm(forms.ModelForm):
  password = forms.CharField( widget=forms.PasswordInput( attrs={
                    'placeholder' : 'Enter Password',
            } ) )
  confirm_password = forms.CharField( widget=forms.PasswordInput( attrs={
                    'placeholder' : 'Confirm Password'
            } ) )
  class Meta :
    model  = Account
    fields = ['first_name', 'last_name', 'email', 'phone_nuber', 'password' ]



  #  giving class name to all class
  def __init__(self, *args, **kwargs):
    super(RegistrationForm, self).__init__(*args,**kwargs)
    for field in self.fields:
      classes = self.fields[field].widget.attrs.get('class','')   # check if some classes have,if no class attr , assign it ' '.
      self.fields[field].widget.attrs['class'] =  classes + 'form-control'

    
    #  we can assign the class name to all the fields by defining the field as password and class attrs value
    # but we cant do it if we have lot of fields

    # setting placeholders
    self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
    self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
    self.fields['email'].widget.attrs['placeholder'] = 'Enter Email Address'
    self.fields['phone_nuber'].widget.attrs['placeholder'] = 'Enter Phone Number'


  def clean(self):
    cleaned_data = super(RegistrationForm, self).clean()
    password = cleaned_data.get('password')
    confirm_password = cleaned_data.get('confirm_password')
    print('cleane method')
    if password != confirm_password:
      # raise forms.ValidationError('Password does not match!')
      #   
      # Note that any errors raised by your Form.clean() override will not be associated with any field in particular.
      # They go into a special “field” (called __all__), which you can access via the non_field_errors() method 
      # if you need to. If you want to attach errors to a specific field in the form, you need to call add_error().
      self.add_error('password',forms.ValidationError('Password does not match!')  )

    print(self.errors, self.non_field_errors )
    
