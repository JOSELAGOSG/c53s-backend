from django.db import models
from django.urls import reverse
from datetime import date, timedelta


class Brand(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('factory:brand-detail', args=[self.pk])
    

class Product(models.Model):
    UNIT_MEASUREMENT_CHOICES = [('unidad', 'un'), ('kilo', 'kg'), ('gramo', 'gr'), ('pote', 'pt')]
    name = models.CharField(max_length=100, unique=True)
    brand = models.ForeignKey(Brand, related_name='product', on_delete=models.PROTECT)
    unit_measurement = models.CharField(choices=UNIT_MEASUREMENT_CHOICES, max_length=2)
    soon_to_expire_weeks = models.IntegerField()

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('factory:product-detail', args=[self.pk])
    
    # How much of the product is in the factory
    def get_total_amount_in_warehouse(self):
        total_amount = self.boxes.aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total_amount
    
    def get_total_amount_withdrawn(self):
        ''' 
            Cambiar logica de esta funcion con nuevo modelo RETIRO
        '''
        pass
    

    # Get monetary value related info

    def get_total_value_in_factory(self):
        value = 0 
        for box in self.boxes.all():
            value += box.get_price_with_taxes()
        return(value)
    
    def get_total_value_withdrawn(self):
        ''' 
            Cambiar logica de esta funcion con nuevo modelo RETIRO
        '''
        pass

    # Get amount of boxes in factory
    def get_boxes_amount_in_factory(self):
        return self.boxes.count()
    
    # Get amount soon to expire

    def get_amount_soon_to_expire_in_factory(self):
        amount = 0
        for box in self.boxes.all():
            if box.soon_to_expire():
                amount += box.amount
        return amount

class Provider(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    phone = models.IntegerField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('factory:provider-detail', args=[self.pk])
    

class Purchase(models.Model):
    date = models.DateField()
    provider = models.ForeignKey(Provider, related_name='purchase', on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('factory:purchase-detail', args=[self.pk])
    
    def get_create_item_url(self):
        return reverse('factory:item-create', args=[self.pk])
    
    def get_total_price(self):
        price = 0 
        for item in self.item.all():
            price += item.get_total_price()
        
        return price
    
    def get_total_price_with_taxes(self):
        price = self.get_total_price()
        return round(price * 1.19)
    
    def get_total_amount(self):
        amount = 0
        for item in self.item.all():
            amount += item.boxes_quantity * item.amount_per_box
        return amount
    
    class Meta:
        ordering = ['-date']


class PurchaseItem(models.Model):
    product = models.ForeignKey(Product, related_name='purchase_item', on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, related_name='item', on_delete=models.CASCADE)
    boxes_quantity = models.IntegerField()
    amount_per_box_kg = models.IntegerField()
    price_per_box = models.IntegerField()

    def __str__(self):
        return f'Compra: {self.purchase.pk} | Item: {self.pk}'
    
    def get_total_price(self):
        return self.price_per_box * self.boxes_quantity

    def get_price_per_kg(self):
        if self.amount_per_box_kg != 0:
            return  round(self.price_per_box / self.amount_per_box_kg )
        

class Box(models.Model):
    product = models.ForeignKey(Product, related_name='boxes', on_delete=models.CASCADE)
    purchase_item = models.ForeignKey('PurchaseItem', related_name='boxes', on_delete=models.CASCADE)
    amount = models.IntegerField()
    price = models.IntegerField()
    expiration_date = models.DateField(null=True)

    class Meta:
        ordering = ['expiration_date']
        indexes = [
            models.Index(fields=['id']),
        ]

    def __str__(self):
        return f'Box:{self.pk}|Product:{self.product.name}'

    def get_price_with_taxes(self):
        return round(self.price * 1.19)

    def soon_to_expire(self):
        if self.expiration_date:
            now = date.today() 
            if self.expiration_date - now <= timedelta(weeks=self.product.soon_to_expire_weeks):
                return True
        return False

    def get_absolute_url(self):
        return reverse('factory:box-detail', args=[self.pk])
    
    def get_withdraw_url(self):
        return reverse('factory:box-withdraw', args=[self.pk])

    def get_expiration_url(self):
        return reverse('factory:box-expiration', args=[self.pk])

    def withdraw(self):
        Withdrawal.objects.create(product=self.product, amount=self.amount, withdrawal_date=date.today())
        self.delete()


class Withdrawal(models.Model):
    product = models.ForeignKey(Product, related_name='withdrawals', on_delete=models.CASCADE)
    amount = models.IntegerField()
    withdrawal_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-withdrawal_date']
        indexes = [
            models.Index(fields=['id']),
        ]

    def __str__(self):
        return f'Withdrawal:{self.pk}|Product:{self.product.name}'
    
class Recipe(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    instructions = models.TextField()

class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
