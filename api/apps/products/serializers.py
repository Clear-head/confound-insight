from rest_framework import serializers

from apps.products.models import Product, ProductIngredient


class ProductIngredientSerializer(serializers.ModelSerializer):
    """제품-성분 매핑 시리얼라이저"""

    compound_name = serializers.CharField(
        source='compound.standard_name',
        read_only=True,
        help_text="정규화된 화합물 표준명"
    )
    compound_cid = serializers.IntegerField(
        source='compound.cid',
        read_only=True,
        help_text="PubChem CID"
    )

    class Meta:
        model = ProductIngredient
        fields = [
            'id',
            'raw_ingredient_name',
            'compound',
            'compound_name',
            'compound_cid',
            'content',
            'unit',
            'is_main_active',
            'ingredient_type',
            'normalization_status',
            'normalization_error',
        ]
        read_only_fields = [
            'id',
            'normalization_status',
            'normalization_error',
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """제품 목록용 간소화된 시리얼라이저"""

    ingredient_count = serializers.SerializerMethodField(
        help_text="성분 개수"
    )
    main_ingredients = serializers.SerializerMethodField(
        help_text="주성분 목록 (최대 3개)"
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'product_name',
            'permit_number',
            'manufacturer',
            'is_combination',
            'ingredient_count',
            'main_ingredients',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_ingredient_count(self, obj):
        """성분 개수 반환"""
        return obj.ingredients.filter(is_main_active=True).count()

    def get_main_ingredients(self, obj):
        """주요 성분 3개 반환"""
        ingredients = obj.ingredients.filter(
            is_main_active=True
        ).select_related('compound')[:3]

        return [
            {
                'name': ing.raw_ingredient_name,
                'compound': ing.compound.standard_name if ing.compound else None
            }
            for ing in ingredients
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """제품 상세 정보용 시리얼라이저 (성분 포함)"""

    ingredients = ProductIngredientSerializer(
        many=True,
        read_only=True,
        help_text="제품에 포함된 모든 성분"
    )
    active_ingredient_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'product_name',
            'permit_number',
            'manufacturer',
            'is_combination',
            'source',
            'last_synced_at',
            'active_ingredient_count',
            'ingredients',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'source',
            'last_synced_at',
            'created_at',
            'updated_at',
        ]

    def get_active_ingredient_count(self, obj):
        """주성분 개수"""
        return obj.ingredients.filter(is_main_active=True).count()


class ProductCreateSerializer(serializers.ModelSerializer):
    """제품 생성용 시리얼라이저"""

    class Meta:
        model = Product
        fields = [
            'product_name',
            'permit_number',
            'manufacturer',
            'is_combination',
        ]

    def validate_permit_number(self, value):
        """허가번호 중복 확인"""
        if Product.objects.filter(permit_number=value).exists():
            raise serializers.ValidationError(
                f"허가번호 '{value}'는 이미 존재합니다."
            )
        return value

    def validate_product_name(self, value):
        """제품명 검증"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "제품명은 최소 2자 이상이어야 합니다."
            )
        return value.strip()


class ProductUpdateSerializer(serializers.ModelSerializer):
    """
        제품 수정용 시리얼라이저
        허가번호 수정 불가
    """

    class Meta:
        model = Product
        fields = [
            'product_name',
            'manufacturer',
            'is_combination',
        ]