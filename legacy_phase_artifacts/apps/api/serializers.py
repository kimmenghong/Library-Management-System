from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import Permission, Role
from apps.activity.models import ActivityLog, AuditLog
from apps.announcements.models import Announcement
from apps.catalog.models import Author, Book, BookCopy, BookLocation, Category, Publisher, Shelf
from apps.circulation.models import BorrowRecord, BorrowingPolicy, RenewalRecord, Reservation, ReturnRecord
from apps.circulation.services import borrow_book, renew_borrow, reserve_book, return_book
from apps.digital_library.models import DigitalBook, DigitalBookCategory, validate_digital_file
from apps.fines.models import Fine, Payment
from apps.fines.services import create_fine, record_payment
from apps.import_export.models import ExportJob, ImportJob
from apps.import_export.services import import_books_from_job
from apps.members.models import LibrarianProfile, Member, StaffProfile, StudentProfile, TeacherProfile
from apps.notifications.models import EmailReminder, Notification
from apps.notifications.services import create_notification
from apps.reviews.models import BookReview
from apps.settings_app.models import BackupRecord, BackupSchedule, LibraryProfile, SystemSetting
from apps.status_tracking.models import BookStatusLog, DamagedBook, LostBook, RepairRecord
from apps.status_tracking.services import (
    create_repair_record,
    report_damaged_book,
    report_lost_book,
    update_damaged_record,
    update_lost_record,
    update_repair_status,
)
from apps.support.models import FAQ, Feedback, SupportTicket


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "role_name",
            "phone",
            "address",
            "avatar",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
            "password",
        ]
        read_only_fields = ["last_login", "date_joined"]
        extra_kwargs = {"is_superuser": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


class FullCleanModelSerializer(serializers.ModelSerializer):
    """Apply model-level cross-field rules to REST writes as well as HTML forms."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance or self.Meta.model()
        for field, value in attrs.items():
            model_field = self.Meta.model._meta.get_field(field)
            if model_field.many_to_many:
                continue
            setattr(instance, field, value)
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc
        return attrs


class MemberSerializer(FullCleanModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = "__all__"
        read_only_fields = ["member_code", "created_at", "updated_at"]


class StudentProfileSerializer(FullCleanModelSerializer):
    class Meta:
        model = StudentProfile
        fields = "__all__"


class TeacherProfileSerializer(FullCleanModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = "__all__"


class StaffProfileSerializer(FullCleanModelSerializer):
    class Meta:
        model = StaffProfile
        fields = "__all__"


class LibrarianProfileSerializer(FullCleanModelSerializer):
    class Meta:
        model = LibrarianProfile
        fields = "__all__"


class AuthorSerializer(FullCleanModelSerializer):
    class Meta:
        model = Author
        fields = "__all__"
        read_only_fields = ["slug", "created_at", "updated_at"]


class PublisherSerializer(FullCleanModelSerializer):
    class Meta:
        model = Publisher
        fields = "__all__"
        read_only_fields = ["slug", "created_at", "updated_at"]


class CategorySerializer(FullCleanModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["slug", "created_at", "updated_at"]


class ShelfSerializer(FullCleanModelSerializer):
    class Meta:
        model = Shelf
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class BookLocationSerializer(FullCleanModelSerializer):
    class Meta:
        model = BookLocation
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class BookSerializer(FullCleanModelSerializer):
    author_names = serializers.CharField(read_only=True)
    total_copies = serializers.IntegerField(read_only=True)
    available_copies = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = "__all__"
        read_only_fields = ["status", "created_at", "updated_at", "created_by", "updated_by"]

    def validate_publication_year(self, value):
        if value and (value < 1000 or value > timezone.now().year + 1):
            raise serializers.ValidationError("Publication year is outside the valid range.")
        return value


class BookCopySerializer(FullCleanModelSerializer):
    class Meta:
        model = BookCopy
        fields = "__all__"
        read_only_fields = ["copy_code", "qr_code", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        shelf = attrs.get("shelf") or getattr(self.instance, "shelf", None)
        location = attrs.get("location") or getattr(self.instance, "location", None)
        if shelf and location and location.shelf_id != shelf.id:
            raise serializers.ValidationError("Book location must belong to the selected shelf.")
        return attrs


class BorrowingPolicySerializer(FullCleanModelSerializer):
    class Meta:
        model = BorrowingPolicy
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class BorrowRecordSerializer(serializers.ModelSerializer):
    borrow_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=False)

    class Meta:
        model = BorrowRecord
        fields = "__all__"
        read_only_fields = [
            "borrowed_by",
            "status",
            "return_date",
            "renewal_count",
            "fine_rate_per_day",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        try:
            return borrow_book(
                member=validated_data["member"],
                book_copy=validated_data["book_copy"],
                borrowed_by=request.user,
                borrow_date=validated_data.get("borrow_date"),
                due_date=validated_data.get("due_date"),
                notes=validated_data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class ReturnRecordSerializer(serializers.ModelSerializer):
    return_date = serializers.DateField(required=False)

    class Meta:
        model = ReturnRecord
        fields = "__all__"
        read_only_fields = ["returned_by", "fine_amount", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        try:
            return return_book(
                borrow_record=validated_data["borrow_record"],
                returned_by=request.user,
                return_date=validated_data.get("return_date"),
                book_condition=validated_data.get("book_condition", ReturnRecord.GOOD),
                remarks=validated_data.get("remarks", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class RenewalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RenewalRecord
        fields = "__all__"
        read_only_fields = ["renewed_by", "old_due_date", "new_due_date", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        try:
            return renew_borrow(
                borrow_record=validated_data["borrow_record"],
                renewed_by=request.user,
                remarks=validated_data.get("remarks", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = "__all__"
        read_only_fields = [
            "reserved_date",
            "ready_date",
            "expiry_date",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        member = attrs.get("member")
        if request and member and not (
            request.user.is_superuser
            or request.user.has_role(
                "super_admin", "admin", "librarian", "assistant_librarian"
            )
        ) and member.user_id != request.user.pk:
            raise serializers.ValidationError(
                {"member": "You can only reserve books for your own member account."}
            )
        return attrs

    def create(self, validated_data):
        try:
            return reserve_book(
                member=validated_data["member"],
                book=validated_data["book"],
                notes=validated_data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class FineSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    reason = serializers.ChoiceField(choices=Fine.REASON_CHOICES, default=Fine.OTHER)

    class Meta:
        model = Fine
        fields = "__all__"
        read_only_fields = [
            "paid_amount",
            "status",
            "created_by",
            "updated_by",
            "waived_by",
            "waived_at",
            "waiver_reason",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        try:
            return create_fine(
                member=validated_data["member"],
                borrow_record=validated_data.get("borrow_record"),
                amount=validated_data["amount"],
                reason=validated_data.get("reason", Fine.LATE_RETURN),
                description=validated_data.get("description", ""),
                created_by=self.context["request"].user,
            )
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or exc.messages
            raise serializers.ValidationError(detail)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = [
            "member",
            "status",
            "received_by",
            "voided_by",
            "voided_at",
            "void_reason",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        try:
            return record_payment(
                fine=validated_data["fine"],
                amount_paid=validated_data["amount_paid"],
                payment_method=validated_data.get("payment_method", Payment.CASH),
                payment_date=validated_data.get("payment_date", timezone.localdate()),
                reference_number=validated_data.get("reference_number", ""),
                notes=validated_data.get("notes", ""),
                received_by=self.context["request"].user,
            )
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or exc.messages
            raise serializers.ValidationError(detail)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = [
            "status",
            "deduplication_key",
            "is_email_sent",
            "email_sent_at",
            "read_at",
            "archived_at",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        try:
            return create_notification(
                recipient=validated_data["recipient"],
                title=validated_data["title"],
                message=validated_data["message"],
                notification_type=validated_data.get(
                    "notification_type", Notification.SYSTEM
                ),
                channel=validated_data.get("channel", Notification.IN_APP),
                priority=validated_data.get("priority", Notification.NORMAL),
                related_borrow_record=validated_data.get("related_borrow_record"),
                related_book_copy=validated_data.get("related_book_copy"),
                created_by=self.context["request"].user,
            )
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or exc.messages
            raise serializers.ValidationError(detail)


class EmailReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailReminder
        fields = "__all__"
        read_only_fields = [
            "status",
            "attempt_number",
            "attempted_at",
            "sent_at",
            "error_message",
            "created_at",
            "updated_at",
        ]


def _request_user(serializer):
    request = serializer.context.get("request")
    return request.user if request and request.user.is_authenticated else None


def _validate_status_relationships(attrs, instance=None):
    book_copy = attrs.get("book_copy") or getattr(instance, "book_copy", None)
    borrow_record = attrs.get("borrow_record") or getattr(instance, "borrow_record", None)
    member = attrs.get("member") or getattr(instance, "member", None)
    if borrow_record and book_copy and borrow_record.book_copy_id != book_copy.pk:
        raise serializers.ValidationError({"borrow_record": "Borrow record must belong to the selected book copy."})
    if borrow_record and member and borrow_record.member_id != member.pk:
        raise serializers.ValidationError({"member": "Member must match the selected borrow record."})
    return attrs


class BookStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookStatusLog
        fields = "__all__"
        read_only_fields = [
            "book",
            "book_copy",
            "previous_status",
            "new_status",
            "reason",
            "notes",
            "changed_by",
            "created_at",
            "updated_at",
        ]


class LostBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostBook
        fields = "__all__"
        read_only_fields = ["reported_by", "reported_date", "created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("status") in LostBook.RESOLVED_STATUSES and not attrs.get("resolved_date"):
            attrs["resolved_date"] = timezone.localdate()
        return _validate_status_relationships(attrs, self.instance)

    def create(self, validated_data):
        return report_lost_book(
            book_copy=validated_data["book_copy"],
            reported_by=validated_data.pop("reported_by", None) or _request_user(self),
            borrow_record=validated_data.get("borrow_record"),
            member=validated_data.get("member"),
            replacement_cost=validated_data.get("replacement_cost", 0),
            description=validated_data.get("description", ""),
        )

    def update(self, instance, validated_data):
        return update_lost_record(
            instance,
            status=validated_data.get("status", instance.status),
            replacement_cost=validated_data.get("replacement_cost", instance.replacement_cost),
            description=validated_data.get("description", instance.description),
            resolution_notes=validated_data.get("resolution_notes", instance.resolution_notes),
            resolved_date=validated_data.get("resolved_date", instance.resolved_date),
            changed_by=_request_user(self),
        )


class DamagedBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamagedBook
        fields = "__all__"
        read_only_fields = ["reported_by", "reported_date", "created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("status") in DamagedBook.RESOLVED_STATUSES and not attrs.get("resolved_date"):
            attrs["resolved_date"] = timezone.localdate()
        return _validate_status_relationships(attrs, self.instance)

    def create(self, validated_data):
        return report_damaged_book(
            book_copy=validated_data["book_copy"],
            reported_by=validated_data.pop("reported_by", None) or _request_user(self),
            borrow_record=validated_data.get("borrow_record"),
            member=validated_data.get("member"),
            severity=validated_data.get("severity", DamagedBook.MINOR),
            estimated_repair_cost=validated_data.get("estimated_repair_cost", 0),
            description=validated_data.get("description", ""),
        )

    def update(self, instance, validated_data):
        return update_damaged_record(
            instance,
            status=validated_data.get("status", instance.status),
            severity=validated_data.get("severity", instance.severity),
            estimated_repair_cost=validated_data.get("estimated_repair_cost", instance.estimated_repair_cost),
            description=validated_data.get("description", instance.description),
            resolution_notes=validated_data.get("resolution_notes", instance.resolution_notes),
            resolved_date=validated_data.get("resolved_date", instance.resolved_date),
            changed_by=_request_user(self),
        )


class RepairRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairRecord
        fields = "__all__"
        read_only_fields = ["sent_by", "sent_date", "created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        book_copy = attrs.get("book_copy") or getattr(self.instance, "book_copy", None)
        damage_record = attrs.get("damage_record") or getattr(self.instance, "damage_record", None)
        if damage_record and book_copy and damage_record.book_copy_id != book_copy.pk:
            raise serializers.ValidationError({"damage_record": "Damage record must belong to the selected book copy."})
        if attrs.get("status") == RepairRecord.COMPLETED and not attrs.get("completed_date"):
            attrs["completed_date"] = timezone.localdate()
        return attrs

    def create(self, validated_data):
        return create_repair_record(
            book_copy=validated_data["book_copy"],
            sent_by=validated_data.pop("sent_by", None) or _request_user(self),
            damage_record=validated_data.get("damage_record"),
            vendor=validated_data.get("vendor", ""),
            expected_return_date=validated_data.get("expected_return_date"),
            repair_cost=validated_data.get("repair_cost", 0),
            notes=validated_data.get("notes", ""),
        )

    def update(self, instance, validated_data):
        return update_repair_status(
            instance,
            status=validated_data.get("status", instance.status),
            changed_by=_request_user(self),
            completed_date=validated_data.get("completed_date", instance.completed_date),
            notes=validated_data.get("notes", instance.notes),
            vendor=validated_data.get("vendor", instance.vendor),
            expected_return_date=validated_data.get("expected_return_date", instance.expected_return_date),
            repair_cost=validated_data.get("repair_cost", instance.repair_cost),
        )


class DigitalBookCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalBookCategory
        fields = "__all__"


class DigitalBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalBook
        fields = "__all__"
        read_only_fields = ["file_type", "download_count", "uploaded_by", "created_at", "updated_at"]

    def validate_file(self, value):
        validate_digital_file(value)
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(f"File is too large. Maximum size is {max_size // (1024 * 1024)} MB.")
        return value

    def validate(self, attrs):
        is_public = attrs.get("is_public", getattr(self.instance, "is_public", False))
        allowed_roles = attrs.get("allowed_roles")
        if not is_public:
            has_roles = bool(allowed_roles) if allowed_roles is not None else bool(self.instance and self.instance.allowed_roles.exists())
            if not has_roles:
                raise serializers.ValidationError("Restricted digital books require at least one allowed role.")
        if attrs.get("file") and Path(attrs["file"].name).suffix.lower() not in {".pdf", ".epub", ".mobi", ".azw3", ".txt"}:
            raise serializers.ValidationError("Unsupported digital book file type.")
        return attrs


class BookReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookReview
        fields = "__all__"
        read_only_fields = ["moderated_by", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        if not request.user.has_role_permission("reviews.moderate_review"):
            member = getattr(request.user, "member_profile", None)
            if not member:
                raise serializers.ValidationError("Your user account is not linked to a member profile.")
            validated_data["member"] = member
        return super().create(validated_data)


class AnnouncementSerializer(serializers.ModelSerializer):
    is_visible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"
        read_only_fields = ["email_sent", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        publish_date = attrs.get("publish_date", getattr(self.instance, "publish_date", None))
        expire_date = attrs.get("expire_date", getattr(self.instance, "expire_date", None))
        if publish_date and expire_date and expire_date < publish_date:
            raise serializers.ValidationError("Expire date must be after publish date.")
        return attrs


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        if request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"
        read_only_fields = ["user", "is_reviewed", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        if request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)


class LibraryProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryProfile
        fields = "__all__"


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = "__all__"


class BackupScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupSchedule
        fields = "__all__"


class BackupRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRecord
        fields = "__all__"
        read_only_fields = ["created_by", "created_at"]


class ImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportJob
        fields = "__all__"
        read_only_fields = ["status", "total_rows", "success_rows", "failed_rows", "message", "created_by", "created_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        job = super().create(validated_data)
        import_books_from_job(job)
        return job


class ExportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportJob
        fields = "__all__"
        read_only_fields = ["created_by", "created_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = "__all__"
        read_only_fields = ["id", "user", "action", "module", "description", "method", "path", "status_code", "ip_address", "user_agent", "created_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = ["id", "user", "app_label", "model_name", "object_id", "object_repr", "action_type", "old_values", "new_values", "ip_address", "created_at"]
