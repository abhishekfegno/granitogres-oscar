from collections import defaultdict

from django.core.management import BaseCommand

from efficient_apriori import apriori

from apps.basket.models import Basket, Line as BasketLine
from apps.catalogue.models import ProductRecommendation, CartSpecificProductRecommendation, Product

from apps.order.models import Line as OrderLine


class Command(BaseCommand):

    def get_basket_lines(self):
        basket_lines_as_dict = BasketLine.objects.filter(basket__status=Basket.OPEN).values('basket', 'product')
        basket_lines = defaultdict(list)
        for item in basket_lines_as_dict:
            basket_lines[item['basket']].append(item['product'])
        basket_lines = {key: set(value) for key, value in basket_lines.items()}
        return basket_lines

    def formatted_product_data(self):
        product_lines = OrderLine.objects.all().values('order', 'stockrecord__product')
        group_by_order = defaultdict(list)
        for item in product_lines:
            group_by_order[item['order']].append(item['stockrecord__product'])
        product_data = [tuple(lines) for lines in group_by_order.values()]
        return product_data

    def get_parent_product_mapping(self):
        dataset = Product.objects.filter(structure__in=[Product.STANDALONE, Product.CHILD]).values('structure', 'parent', 'id')
        return {p['id']: p['id'] if p['structure'] == Product.STANDALONE else p['parent'] for p in dataset}

    def handle(self, *args, **options):

        recommendations = []
        cart_recommendations = []

        basket_lines = self.get_basket_lines()
        product_data = self.formatted_product_data()
        parent_product = self.get_parent_product_mapping()

        # "old_recommendations" to be deleted after successful running of the whole script.
        old_recommendations = list(ProductRecommendation.objects.all().values_list('pk', flat=True))
        old_cart_recommendations = list(CartSpecificProductRecommendation.objects.all().values_list('pk', flat=True))

        freq_item_set, rules = apriori(
            product_data,
            min_support=0.1,
            min_confidence=0.1)

        print("freq_item_set", freq_item_set)
        print("rules", rules)
        print("parent_product", parent_product)
        # rules_rhs = filter(lambda rule: len(rule.lhs) == 2 and len(rule.rhs) == 1, rules)

        for rule in sorted(rules, key=lambda rule: rule.lift):
            print(rule)  # Prints the rule and its confidence, support, lift, ...
            if len(rule.lhs) == 1:
                # add this to ProductRecommendationClass
                for rec in rule.rhs:
                    recommendations.append(
                        ProductRecommendation(
                            primary_id=parent_product[rule.lhs[0]],
                            recommendation_id=parent_product[rec],
                            ranking=rule.lift
                        )
                    )
            else:
                # add this to CartRecommendationClass
                for basket_id, basket_products_set in basket_lines.items():
                    if set(rule.rhs).issubset(basket_products_set):
                        for rec in rule.rhs:
                            cart_recommendations.append(
                                CartSpecificProductRecommendation(
                                    primary_id=basket_id,
                                    recommendation_id=parent_product[rec],
                                    ranking=len(rule.lhs)*rule.lift
                                )
                            )
        ProductRecommendation.objects.filter().delete()
        CartSpecificProductRecommendation.objects.filter().delete()
        ProductRecommendation.objects.bulk_create(recommendations, ignore_conflicts=True)
        CartSpecificProductRecommendation.objects.bulk_create(cart_recommendations, ignore_conflicts=True)



