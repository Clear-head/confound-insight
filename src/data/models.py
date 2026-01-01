from django.db import models


# 1. 의약품 제품 정보 (products 앱)
class Product(models.Model):
    product_name = models.CharField(max_length=255)
    permit_number = models.CharField(max_length=50, unique=True)
    manufacturer = models.CharField(max_length=255, null=True, blank=True)
    is_combination = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'products'
        db_table = 'products'


# 2. 화합물/주성분 정보 (compounds 앱)
class Compound(models.Model):
    standard_name = models.CharField(max_length=255, unique=True)
    cid = models.IntegerField(unique=True, null=True, blank=True)
    smiles = models.TextField(null=True, blank=True)
    molecular_formula = models.CharField(max_length=100, null=True, blank=True)
    molecular_weight = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    iupac_name = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'compounds'
        db_table = 'compounds'


# 3. 제품-성분 매핑
class ProductIngredient(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='ingredients')
    compound = models.ForeignKey('compounds.Compound', on_delete=models.SET_NULL, null=True, related_name='products')

    raw_ingredient_name = models.CharField(max_length=255)
    content = models.CharField(max_length=100, null=True, blank=True)
    is_main_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'products'
        db_table = 'product_ingredients'


# 4. 화합물 간 구조 유사도 분석 결과
class SimilarityAnalysis(models.Model):
    target_compound = models.ForeignKey(
        'compounds.Compound',
        on_delete=models.CASCADE,
        related_name='similarities_as_target'
    )
    similar_compound = models.ForeignKey(
        'compounds.Compound',
        on_delete=models.CASCADE,
        related_name='similarities_as_comparison'
    )
    similarity_score = models.FloatField()
    analysis_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'analysis'
        db_table = 'compound_similarities'
        unique_together = ('target_compound', 'similar_compound')