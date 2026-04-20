from rest_framework import serializers

from accounts.serializers import UserSerializer
from discovery.serializers import (
    LeadDiscoveryAnswerReadSerializer,
)

from .models import (
    ActivityTimeline,
    Lead,
    Note,
    Tag,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class NoteSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source="created_by", read_only=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "lead",
            "content",
            "created_by",
            "created_by_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ActivityTimelineSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source="user", read_only=True)

    class Meta:
        model = ActivityTimeline
        fields = [
            "id",
            "lead",
            "user",
            "user_detail",
            "activity_type",
            "description",
            "created_at",
        ]


class SimpleActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityTimeline
        fields = ["activity_type", "description"]


class LeadSerializer(serializers.ModelSerializer):
    notes = NoteSerializer(many=True, read_only=True)
    activities = ActivityTimelineSerializer(many=True, read_only=True)
    discovery_answers = LeadDiscoveryAnswerReadSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    def _handle_tags(self, instance, tag_names):
        if tag_names is not None:
            tags = []
            for name in tag_names:
                # Check if a tag already exists that contains this name (case-insensitive)
                tag = Tag.objects.filter(name__icontains=name).first()
                if not tag:
                    tag = Tag.objects.create(name=name)
                tags.append(tag)
            instance.tags.set(tags)

    def create(self, validated_data):
        tag_names = validated_data.pop("tag_names", None)
        lead = super().create(validated_data)
        self._handle_tags(lead, tag_names)
        return lead

    def update(self, instance, validated_data):
        tag_names = validated_data.pop("tag_names", None)
        lead = super().update(instance, validated_data)
        self._handle_tags(lead, tag_names)
        return lead

    class Meta:
        model = Lead
        fields = [
            "id",
            "full_name",
            "email",
            "phone_number",
            "source",
            "estimate_value",
            "status",
            "assigned_to",
            "created_by",
            "created_at",
            "updated_at",
            "notes",
            "activities",
            "discovery_answers",
            "tags",
            "tag_names",
            "rating",
        ]
        read_only_fields = ["created_at", "updated_at"]


class LeadListSerializer(serializers.ModelSerializer):
    assigned_to = serializers.StringRelatedField()
    tags = TagSerializer(many=True, read_only=True)
    last_activity = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            "id",
            "full_name",
            "last_activity",
            "email",
            "phone_number",
            "assigned_to",
            "tags",
            "rating",
        ]

    def get_last_activity(self, obj):
        last_activity = obj.activities.first()
        if last_activity:
            return SimpleActivitySerializer(last_activity).data
        return None


class LeadDetailSerializer(LeadSerializer):
    assigned_to_detail = UserSerializer(source="assigned_to", read_only=True)
    created_by_detail = UserSerializer(source="created_by", read_only=True)

    class Meta(LeadSerializer.Meta):
        fields = LeadSerializer.Meta.fields + [
            "assigned_to_detail",
            "created_by_detail",
        ]


class LeadPipelineSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = ["id", "full_name", "estimate_value", "assigned_to_name"]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None
