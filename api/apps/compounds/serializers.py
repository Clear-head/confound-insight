from rest_framework import serializers

from .models import Compound


class CompoundListSerializer(serializers.ModelSerializer):
    """화합물 목록 조회용 시리얼라이저"""

    has_structure = serializers.SerializerMethodField(
        help_text="구조 데이터 존재 여부"
    )
    product_count = serializers.SerializerMethodField(
        help_text="해당 화합물을 포함하는 제품 수"
    )

    class Meta:
        model = Compound
        fields = [
            "id",
            "standard_name",
            "cid",
            "molecular_formula",
            "molecular_weight",
            "is_valid",
            "has_structure",
            "product_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_has_structure(self, obj):
        """구조 데이터 존재 여부"""
        return obj.has_structure_data()

    def get_product_count(self, obj):
        """화합물이 포함된 제품 수 (주성분 기준)"""
        return obj.products.filter(is_main_active=True).count()


class CompoundDetailSerializer(serializers.ModelSerializer):
    """화합물 상세 조회용 시리얼라이저"""

    related_products = serializers.SerializerMethodField(
        help_text="화합물 포함 제품 목록 (최대 10개)"
    )
    has_fingerprint = serializers.SerializerMethodField(
        help_text="분자 지문 데이터 존재 여부"
    )
    similarity_count = serializers.SerializerMethodField(
        help_text="유사도 분석 결과 수"
    )

    class Meta:
        model = Compound
        fields = [
            "id",
            "standard_name",
            "cid",
            "smiles",
            "inchi",
            "inchi_key",
            "molecular_formula",
            "molecular_weight",
            "iupac_name",
            "fingerprint_type",
            "is_valid",
            "validation_error",
            "has_fingerprint",
            "similarity_count",
            "related_products",
            "created_at",
            "updated_at",
            "pubchem_last_fetched",
        ]
        read_only_fields = [
            "id",
            "fingerprint_type",
            "validation_error",
            "is_valid",
            "created_at",
            "updated_at",
            "pubchem_last_fetched",
        ]

    def get_related_products(self, obj):
        """화합물이 포함된 제품 목록 (최대 10개)"""
        product_ingredients = obj.products.select_related("product")[:10]
        return [
            {
                "id": pi.product.id,
                "product_name": pi.product.product_name,
                "is_main_active": pi.is_main_active,
            }
            for pi in product_ingredients
        ]

    def get_has_fingerprint(self, obj):
        """분자 지문 존재 여부"""
        return obj.fingerprint_morgan is not None

    def get_similarity_count(self, obj):
        """유사도 분석 결과 수 (대상 + 비교 합계)"""
        target_count = obj.similarities_as_target.count()
        comparison_count = obj.similarities_as_comparison.count()
        return target_count + comparison_count


class CompoundCreateSerializer(serializers.ModelSerializer):
    """화합물 생성용 시리얼라이저"""

    class Meta:
        model = Compound
        fields = [
            "standard_name",
            "cid",
            "smiles",
            "inchi",
            "inchi_key",
            "molecular_formula",
            "molecular_weight",
            "iupac_name",
        ]

    def validate_standard_name(self, value):
        """표준 성분명 유효성 검증"""
        if Compound.objects.filter(standard_name=value).exists():
            raise serializers.ValidationError(
                f"이미 존재하는 표준 성분명입니다: {value}"
            )
        if len(value) < 2:
            raise serializers.ValidationError(
                "표준 성분명은 최소 2자 이상이어야 합니다."
            )
        return value

    def validate_cid(self, value):
        """PubChem CID 유효성 검증"""
        if value is None:
            return value
        if Compound.objects.filter(cid=value).exists():
            raise serializers.ValidationError(
                f"이미 존재하는 CID입니다: {value}"
            )
        if value <= 0:
            raise serializers.ValidationError(
                "CID는 양의 정수여야 합니다."
            )
        return value

    def validate_smiles(self, value):
        """SMILES 문자열 기본 검증"""
        if value is None or value == "":
            return value
        # 기본적인 SMILES 문자 검증 (RDKit 없이)
        invalid_chars = set(value) - set(
            "CNOPSFIBrcnopsfibl0123456789"
            "=#@+\\/-[]().%*"
        )
        if invalid_chars:
            raise serializers.ValidationError(
                f"유효하지 않은 SMILES 문자가 포함되어 있습니다: {invalid_chars}"
            )
        return value


class CompoundUpdateSerializer(serializers.ModelSerializer):
    """화합물 수정용 시리얼라이저"""

    class Meta:
        model = Compound
        fields = [
            "standard_name",
            "cid",
            "smiles",
            "inchi",
            "inchi_key",
            "molecular_formula",
            "molecular_weight",
            "iupac_name",
        ]

    def validate_standard_name(self, value):
        """표준 성분명 중복 검증 (자기 자신 제외)"""
        instance = self.instance
        if Compound.objects.filter(standard_name=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(
                f"이미 존재하는 표준 성분명입니다: {value}"
            )
        return value

    def validate_cid(self, value):
        """CID 중복 검증 (자기 자신 제외)"""
        if value is None:
            return value
        instance = self.instance
        if Compound.objects.filter(cid=value).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(
                f"이미 존재하는 CID입니다: {value}"
            )
        return value


class CompoundSearchSerializer(serializers.ModelSerializer):
    """화합물 검색 결과용 시리얼라이저"""

    match_type = serializers.SerializerMethodField(
        help_text="매칭 타입 [EXACT, PARTIAL, CID]"
    )

    class Meta:
        model = Compound
        fields = [
            "id",
            "standard_name",
            "cid",
            "molecular_formula",
            "molecular_weight",
            "is_valid",
            "match_type",
        ]

    def get_match_type(self, obj):
        """검색 매칭 타입 반환"""
        # context에서 검색어와 검색 타입 가져오기
        search_query = self.context.get("search_query", "")
        search_type = self.context.get("search_type", "name")

        if search_type == "cid":
            return "CID"

        if not search_query:
            return "UNKNOWN"

        # 정확히 일치하면 EXACT, 아니면 PARTIAL
        if obj.standard_name.lower() == search_query.lower():
            return "EXACT"
        return "PARTIAL"


class CompoundPubChemSerializer(serializers.ModelSerializer):
    """PubChem 데이터 동기화용 시리얼라이저"""

    class Meta:
        model = Compound
        fields = [
            "cid",
            "smiles",
            "inchi",
            "inchi_key",
            "molecular_formula",
            "molecular_weight",
            "iupac_name",
            "pubchem_last_fetched",
        ]
        read_only_fields = ["pubchem_last_fetched"]


class CompoundBulkCreateSerializer(serializers.Serializer):
    """화합물 대량 생성용 시리얼라이저"""

    compounds = CompoundCreateSerializer(many=True)

    def create(self, validated_data):
        compounds_data = validated_data.get("compounds", [])
        created = []
        for compound_data in compounds_data:
            compound = Compound.objects.create(**compound_data)
            created.append(compound)
        return created