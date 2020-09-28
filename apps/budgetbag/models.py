from django.conf import settings
from django.db import models


class BudgetBag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(blank=True, max_length=250)
    description = models.TextField(blank=True)

    @staticmethod
    def budget_bag_name_generator(user):
        base_name = "My Budget Bag"
        count = BudgetBag.objects.filter(user=user, name__startswith=base_name).count()
        return f"{base_name} {count}"

    def save(self, **kwargs):
        if not self.name:
            self.name = self.budget_bag_name_generator(self.user)
        super(BudgetBag, self).save(**kwargs)

    def generate_order(self):
        pass


class BagLines(models.Model):
    product = models.ForeignKey('catalogue.Product', on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)








