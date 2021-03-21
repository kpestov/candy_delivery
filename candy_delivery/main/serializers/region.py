from rest_framework import serializers

from ..models import Region


class RegionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = Region
        fields = ('id', )

    def to_representation(self, instance):
        return instance.id
