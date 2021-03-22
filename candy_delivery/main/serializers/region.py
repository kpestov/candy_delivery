from typing import Iterable

from rest_framework import serializers

from ..models import Region


class RegionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = Region
        fields = ('id', )

    def to_representation(self, instance):
        return instance.id

    @staticmethod
    def bulk_create_regions(validated_items, obj_key: str):
        region_ids = []
        for validated_item_data in validated_items:
            regions = validated_item_data.get(obj_key)
            if isinstance(regions, Iterable):
                region_ids.extend(regions)
            else:
                region_ids.append(regions)

        Region.create_new_regions(set(region_ids))
