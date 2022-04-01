from django.db import models
from category.models import Category
from django.urls import reverse

# Create your models here.
class Product(models.Model):
  product_name = models.CharField(max_length=200, unique=True)
  slug         = models.SlugField(max_length=200, unique=True)
  Description = models.TextField(max_length=500, blank=True)
  price         = models.IntegerField()
  image         = models.ImageField( upload_to='photos/products')
  stock         = models.IntegerField()
  is_available  = models.BooleanField(default=True)
  category      = models.ForeignKey(Category, on_delete=models.CASCADE)
  created_date  = models.DateTimeField(auto_now_add=True)
  modified_date  = models.DateTimeField(auto_now=True)



  class Meta:
      verbose_name = ("Product")
      verbose_name_plural = ("Products")

  def __str__(self):
      return self.product_name

  def get_url(self):
      return reverse("product_detail", kwargs={"category_slug": self.category.slug,"product_slug":self.slug})




class VariationManager(models.Manager):
  def colors(self):
    return super(VariationManager, self).filter(variation_category='color', is_active=True)
  def sizes(self):
    return super(VariationManager, self).filter(variation_category='size', is_active=True)
        


variation_category_choice = (
    ('color', 'color'),
    ("size", "size")
)

class Variation(models.Model):
  product             = models.ForeignKey(Product, on_delete=models.CASCADE)
  variation_category  = models.CharField(max_length=100, choices=variation_category_choice )
  variation_value     = models.CharField(max_length=100)
  is_active           = models.BooleanField(default=True)
  created_date        = models.DateTimeField(auto_now_add=True)

  objects = VariationManager()   # telling the model that we have created model for you
  
  def __str__(self):
    return self.variation_value