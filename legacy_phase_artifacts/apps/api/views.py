from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils import timezone
from rest_framework import routers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import Permission, Role
from apps.activity.models import ActivityLog, AuditLog
from apps.announcements.models import Announcement
from apps.announcements.services import send_announcement_email
from apps.catalog.models import Author, Book, BookCopy, BookLocation, Category, Publisher, Shelf
from apps.circulation.models import BorrowRecord, BorrowingPolicy, RenewalRecord, Reservation, ReturnRecord
from apps.circulation.services import update_reservation_status
from apps.digital_library.models import DigitalBook, DigitalBookCategory
from apps.fines.models import Fine, Payment
from apps.fines.services import void_payment, waive_fine
from apps.import_export.models import ExportJob, ImportJob
from apps.members.models import LibrarianProfile, Member, StaffProfile, StudentProfile, TeacherProfile
from apps.notifications.models import EmailReminder, Notification
from apps.notifications.services import retry_notification_email
from apps.reviews.models import BookReview
from apps.settings_app.models import BackupRecord, BackupSchedule, LibraryProfile, SystemSetting
from apps.status_tracking.models import BookStatusLog, DamagedBook, LostBook, RepairRecord
from apps.support.models import FAQ, Feedback, SupportTicket

from .auth import LibraryTokenObtainPairSerializer
from .permissions import HasRolePermission
from .serializers import (
    ActivityLogSerializer,
    AnnouncementSerializer,
    AuditLogSerializer,
    AuthorSerializer,
    BackupRecordSerializer,
    BackupScheduleSerializer,
    BookCopySerializer,
    BookLocationSerializer,
    BookReviewSerializer,
    BookSerializer,
    BookStatusLogSerializer,
    BorrowingPolicySerializer,
    BorrowRecordSerializer,
    CategorySerializer,
    DamagedBookSerializer,
    DigitalBookCategorySerializer,
    DigitalBookSerializer,
    EmailReminderSerializer,
    ExportJobSerializer,
    FAQSerializer,
    FeedbackSerializer,
    FineSerializer,
    ImportJobSerializer,
    LibrarianProfileSerializer,
    LibraryProfileSerializer,
    LostBookSerializer,
    MemberSerializer,
    NotificationSerializer,
    PaymentSerializer,
    PermissionSerializer,
    PublisherSerializer,
    RenewalRecordSerializer,
    RepairRecordSerializer,
    ReservationSerializer,
    ReturnRecordSerializer,
    RoleSerializer,
    ShelfSerializer,
    StaffProfileSerializer,
    StudentProfileSerializer,
    SupportTicketSerializer,
    SystemSettingSerializer,
    TeacherProfileSerializer,
    UserSerializer,
)


class LibraryTokenObtainPairView(TokenObtainPairView):
    serializer_class = LibraryTokenObtainPairSerializer


class RolePermissionModelViewSet(viewsets.ModelViewSet):
    permission_classes = [HasRolePermission]
    search_fields = []
    ordering_fields = "__all__"


class RolePermissionReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [HasRolePermission]
    search_fields = []
    ordering_fields = "__all__"


def raise_drf_validation(exc):
    detail = exc.message_dict if hasattr(exc, "message_dict") else getattr(exc, "messages", [str(exc)])
    raise DRFValidationError(detail)


class UserViewSet(RolePermissionModelViewSet):
    queryset = UserSerializer.Meta.model.objects.select_related("role").all()
    serializer_class = UserSerializer
    permission_map = {
        "view": "accounts.view_user",
        "create": "accounts.add_user",
        "update": "accounts.edit_user",
        "destroy": "accounts.delete_user",
    }
    search_fields = ["username", "email", "first_name", "last_name"]


class RoleViewSet(RolePermissionModelViewSet):
    queryset = Role.objects.prefetch_related("permissions").all()
    serializer_class = RoleSerializer
    permission_map = {
        "view": "accounts.view_role",
        "create": "accounts.add_role",
        "update": "accounts.edit_role",
        "destroy": "accounts.delete_role",
    }
    search_fields = ["name", "slug"]


class PermissionViewSet(RolePermissionModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_map = {
        "view": "accounts.view_permission",
        "create": "accounts.add_permission",
        "update": "accounts.edit_permission",
        "destroy": "accounts.delete_permission",
    }
    search_fields = ["name", "codename", "module"]


class MemberViewSet(RolePermissionModelViewSet):
    queryset = Member.objects.select_related("user").all()
    serializer_class = MemberSerializer
    permission_map = {
        "view": "members.view_member",
        "create": "members.add_member",
        "update": "members.edit_member",
        "destroy": "members.delete_member",
    }
    search_fields = ["member_code", "user__username", "user__email", "user__first_name", "user__last_name"]


class MemberProfilePermissionMixin:
    permission_map = {
        "view": "members.view_member",
        "create": "members.edit_member",
        "update": "members.edit_member",
        "destroy": "members.delete_member",
    }


class StudentProfileViewSet(MemberProfilePermissionMixin, RolePermissionModelViewSet):
    queryset = StudentProfile.objects.select_related("member__user").all()
    serializer_class = StudentProfileSerializer
    search_fields = ["student_id", "department", "member__member_code"]


class TeacherProfileViewSet(MemberProfilePermissionMixin, RolePermissionModelViewSet):
    queryset = TeacherProfile.objects.select_related("member__user").all()
    serializer_class = TeacherProfileSerializer
    search_fields = ["teacher_id", "faculty", "department", "member__member_code"]


class StaffProfileViewSet(MemberProfilePermissionMixin, RolePermissionModelViewSet):
    queryset = StaffProfile.objects.select_related("member__user").all()
    serializer_class = StaffProfileSerializer
    search_fields = ["staff_id", "department", "position", "member__member_code"]


class LibrarianProfileViewSet(MemberProfilePermissionMixin, RolePermissionModelViewSet):
    queryset = LibrarianProfile.objects.select_related("member__user").all()
    serializer_class = LibrarianProfileSerializer
    search_fields = ["librarian_id", "department", "member__member_code"]


class AuthorViewSet(RolePermissionModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_map = {
        "view": "catalog.view_book",
        "create": "catalog.manage_author",
        "update": "catalog.manage_author",
        "destroy": "catalog.manage_author",
    }
    search_fields = ["name", "nationality"]


class PublisherViewSet(RolePermissionModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_map = {
        "view": "catalog.view_book",
        "create": "catalog.manage_publisher",
        "update": "catalog.manage_publisher",
        "destroy": "catalog.manage_publisher",
    }
    search_fields = ["name", "contact_email"]


class CategoryViewSet(RolePermissionModelViewSet):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer
    permission_map = {
        "view": "catalog.view_book",
        "create": "catalog.manage_category",
        "update": "catalog.manage_category",
        "destroy": "catalog.manage_category",
    }
    search_fields = ["name", "code"]


class ShelfViewSet(RolePermissionModelViewSet):
    queryset = Shelf.objects.all()
    serializer_class = ShelfSerializer
    permission_map = {
        "view": "catalog.view_book",
        "create": "catalog.manage_location",
        "update": "catalog.manage_location",
        "destroy": "catalog.manage_location",
    }
    search_fields = ["shelf_code", "name", "floor", "section"]


class BookLocationViewSet(RolePermissionModelViewSet):
    queryset = BookLocation.objects.select_related("shelf").all()
    serializer_class = BookLocationSerializer
    permission_map = {
        "view": "catalog.view_book",
        "create": "catalog.manage_location",
        "update": "catalog.manage_location",
        "destroy": "catalog.manage_location",
    }
    search_fields = ["label", "shelf__shelf_code", "aisle", "row"]


class BookViewSet(RolePermissionModelViewSet):
    serializer_class = BookSerializer
    permission_map = {
        "view": "catalog.view_book",
        "create": "catalog.add_book",
        "update": "catalog.edit_book",
        "destroy": "catalog.delete_book",
    }
    search_fields = ["title", "subtitle", "isbn", "book_code", "authors__name", "publisher__name", "category__name"]

    def get_queryset(self):
        queryset = Book.objects.select_related("publisher", "category").prefetch_related("authors", "copies")
        params = self.request.query_params
        if params.get("author"):
            queryset = queryset.filter(authors__id=params["author"])
        if params.get("publisher"):
            queryset = queryset.filter(publisher_id=params["publisher"])
        if params.get("category"):
            queryset = queryset.filter(category_id=params["category"])
        if params.get("shelf"):
            queryset = queryset.filter(copies__shelf_id=params["shelf"])
        if params.get("availability"):
            queryset = queryset.filter(copies__status=params["availability"])
        if params.get("publication_year"):
            if params["publication_year"].isdigit():
                queryset = queryset.filter(publication_year=params["publication_year"])
            else:
                queryset = queryset.none()
        if params.get("language"):
            queryset = queryset.filter(language__icontains=params["language"])
        if params.get("barcode"):
            queryset = queryset.filter(copies__barcode__icontains=params["barcode"])
        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class BookCopyViewSet(RolePermissionModelViewSet):
    queryset = BookCopy.objects.select_related("book", "shelf", "location").all()
    serializer_class = BookCopySerializer
    permission_map = {
        "view": "catalog.view_book",
        "create": "catalog.manage_copy",
        "update": "catalog.manage_copy",
        "destroy": "catalog.manage_copy",
    }
    search_fields = ["copy_code", "barcode", "book__title", "book__book_code"]


class BorrowingPolicyViewSet(RolePermissionModelViewSet):
    queryset = BorrowingPolicy.objects.all()
    serializer_class = BorrowingPolicySerializer
    permission_map = {
        "view": "circulation.manage_policy",
        "create": "circulation.manage_policy",
        "update": "circulation.manage_policy",
        "destroy": "circulation.manage_policy",
    }


class BorrowRecordViewSet(RolePermissionModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = BorrowRecordSerializer
    permission_map = {
        "view": "circulation.view_borrow",
        "create": "circulation.create_borrow",
        "update": "circulation.create_borrow",
        "destroy": "circulation.create_borrow",
    }
    search_fields = ["member__member_code", "book_copy__copy_code", "book_copy__book__title"]

    def get_queryset(self):
        queryset = BorrowRecord.objects.select_related("member__user", "book_copy__book", "borrowed_by")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(member__user=self.request.user)
        return queryset


class ReturnRecordViewSet(RolePermissionModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = ReturnRecordSerializer
    permission_map = {
        "view": "circulation.view_borrow",
        "create": "circulation.return_book",
        "update": "circulation.return_book",
        "destroy": "circulation.return_book",
    }

    def get_queryset(self):
        queryset = ReturnRecord.objects.select_related("borrow_record__member__user", "borrow_record__book_copy__book", "returned_by")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(borrow_record__member__user=self.request.user)
        return queryset


class RenewalRecordViewSet(RolePermissionModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = RenewalRecordSerializer
    permission_map = {
        "view": "circulation.view_borrow",
        "create": "circulation.renew_borrow",
        "update": "circulation.renew_borrow",
        "destroy": "circulation.renew_borrow",
    }

    def get_queryset(self):
        queryset = RenewalRecord.objects.select_related("borrow_record__member__user", "borrow_record__book_copy__book", "renewed_by")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(borrow_record__member__user=self.request.user)
        return queryset


class ReservationViewSet(RolePermissionModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = ReservationSerializer
    permission_map = {
        "view": "circulation.manage_reservation",
        "create": "circulation.manage_reservation",
        "update": "circulation.manage_reservation",
        "destroy": "circulation.manage_reservation",
        "reservation_status": "circulation.manage_reservation",
    }
    search_fields = ["member__member_code", "book__title", "book__book_code"]

    def get_queryset(self):
        queryset = Reservation.objects.select_related("member__user", "book")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(member__user=self.request.user)
        return queryset

    @action(detail=True, methods=["post"], url_path="status")
    def reservation_status(self, request, pk=None):
        reservation = self.get_object()
        status = request.data.get("status")
        if request.user.has_role("student", "teacher", "staff") and status != Reservation.CANCELLED:
            return Response(
                {"status": ["Members may only cancel their own reservations."]},
                status=400,
            )
        try:
            reservation = update_reservation_status(
                reservation,
                status,
                changed_by=request.user,
                notes=request.data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            return Response({"status": exc.messages}, status=400)
        return Response(self.get_serializer(reservation).data)


class FineViewSet(RolePermissionModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = FineSerializer
    permission_map = {
        "view": "fines.view_fine",
        "create": "fines.manage_fine",
        "update": "fines.manage_fine",
        "destroy": "fines.manage_fine",
        "waive": "fines.manage_fine",
    }
    search_fields = ["member__member_code", "description", "reason"]

    def get_queryset(self):
        queryset = Fine.objects.select_related("member__user", "borrow_record", "created_by")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(member__user=self.request.user)
        return queryset

    @action(detail=True, methods=["post"])
    def waive(self, request, pk=None):
        try:
            fine = waive_fine(
                fine=self.get_object(),
                waived_by=request.user,
                reason=request.data.get("reason", ""),
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": getattr(exc, "messages", [str(exc)])},
                status=400,
            )
        return Response(self.get_serializer(fine).data)


class PaymentViewSet(RolePermissionModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = PaymentSerializer
    permission_map = {
        "view": "fines.view_payment",
        "create": "fines.receive_payment",
        "update": "fines.receive_payment",
        "destroy": "fines.receive_payment",
        "void": "fines.receive_payment",
    }
    search_fields = ["member__member_code", "reference_number"]

    def get_queryset(self):
        queryset = Payment.objects.select_related("fine", "member__user", "received_by")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(member__user=self.request.user)
        return queryset

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        try:
            payment = void_payment(
                payment=self.get_object(),
                voided_by=request.user,
                reason=request.data.get("reason", ""),
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": getattr(exc, "messages", [str(exc)])},
                status=400,
            )
        return Response(self.get_serializer(payment).data)


class NotificationViewSet(RolePermissionModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = NotificationSerializer
    permission_map = {
        "view": "notifications.view_notification",
        "create": "notifications.send_notification",
        "update": "notifications.send_notification",
        "destroy": "notifications.send_notification",
        "mark_read": "notifications.view_notification",
        "archive": "notifications.view_notification",
        "retry_email": "notifications.send_notification",
    }
    search_fields = ["title", "message", "recipient__member_code"]

    def get_queryset(self):
        queryset = Notification.objects.select_related("recipient__user", "related_borrow_record", "related_book_copy", "created_by")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(recipient__user=self.request.user)
        return queryset

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_object().mark_read()
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        notification = self.get_object().archive()
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post"], url_path="retry-email")
    def retry_email(self, request, pk=None):
        try:
            attempt = retry_notification_email(self.get_object())
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=400)
        return Response(EmailReminderSerializer(attempt).data)


class EmailReminderViewSet(RolePermissionReadOnlyViewSet):
    serializer_class = EmailReminderSerializer
    permission_map = {"view": "notifications.view_notification"}
    search_fields = ["email_to", "subject"]

    def get_queryset(self):
        queryset = EmailReminder.objects.select_related("notification", "member__user", "borrow_record")
        if self.request.user.has_role("student", "teacher", "staff") and not self.request.user.is_superuser:
            queryset = queryset.filter(member__user=self.request.user)
        return queryset


class BookStatusLogViewSet(RolePermissionReadOnlyViewSet):
    queryset = BookStatusLog.objects.all()
    serializer_class = BookStatusLogSerializer
    permission_map = {"view": "status_tracking.view_status"}
    search_fields = ["book__title", "book_copy__copy_code", "reason"]

    def get_queryset(self):
        return BookStatusLog.objects.select_related("book", "book_copy", "changed_by").visible_to(self.request.user)


class LostBookViewSet(RolePermissionModelViewSet):
    queryset = LostBook.objects.all()
    serializer_class = LostBookSerializer
    permission_map = {
        "view": "status_tracking.manage_lost",
        "create": "status_tracking.manage_lost",
        "update": "status_tracking.manage_lost",
        "destroy": "status_tracking.manage_lost",
    }
    search_fields = ["book_copy__book__title", "book_copy__copy_code", "member__member_code"]

    def get_queryset(self):
        return LostBook.objects.select_related("book_copy__book", "borrow_record", "member__user", "reported_by")

    def perform_create(self, serializer):
        try:
            serializer.save(reported_by=self.request.user)
        except DjangoValidationError as exc:
            raise_drf_validation(exc)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as exc:
            raise_drf_validation(exc)


class DamagedBookViewSet(RolePermissionModelViewSet):
    queryset = DamagedBook.objects.all()
    serializer_class = DamagedBookSerializer
    permission_map = {
        "view": "status_tracking.manage_damaged",
        "create": "status_tracking.manage_damaged",
        "update": "status_tracking.manage_damaged",
        "destroy": "status_tracking.manage_damaged",
    }
    search_fields = ["book_copy__book__title", "book_copy__copy_code", "member__member_code"]

    def get_queryset(self):
        return DamagedBook.objects.select_related("book_copy__book", "borrow_record", "member__user", "reported_by")

    def perform_create(self, serializer):
        try:
            serializer.save(reported_by=self.request.user)
        except DjangoValidationError as exc:
            raise_drf_validation(exc)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as exc:
            raise_drf_validation(exc)


class RepairRecordViewSet(RolePermissionModelViewSet):
    queryset = RepairRecord.objects.all()
    serializer_class = RepairRecordSerializer
    permission_map = {
        "view": "status_tracking.manage_repair",
        "create": "status_tracking.manage_repair",
        "update": "status_tracking.manage_repair",
        "destroy": "status_tracking.manage_repair",
    }
    search_fields = ["book_copy__book__title", "book_copy__copy_code", "vendor"]

    def get_queryset(self):
        return RepairRecord.objects.select_related("book_copy__book", "damage_record", "sent_by")

    def perform_create(self, serializer):
        try:
            serializer.save(sent_by=self.request.user)
        except DjangoValidationError as exc:
            raise_drf_validation(exc)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as exc:
            raise_drf_validation(exc)


class DigitalBookCategoryViewSet(RolePermissionModelViewSet):
    queryset = DigitalBookCategory.objects.all()
    serializer_class = DigitalBookCategorySerializer
    permission_map = {
        "view": "digital.view_digital_book",
        "create": "digital.manage_digital_book",
        "update": "digital.manage_digital_book",
        "destroy": "digital.manage_digital_book",
    }
    search_fields = ["name", "description"]


class DigitalBookViewSet(RolePermissionModelViewSet):
    serializer_class = DigitalBookSerializer
    permission_map = {
        "view": "digital.view_digital_book",
        "create": "digital.manage_digital_book",
        "update": "digital.manage_digital_book",
        "destroy": "digital.manage_digital_book",
    }
    search_fields = ["title", "description", "book__title", "category__name"]

    def get_queryset(self):
        queryset = DigitalBook.objects.select_related("book", "category", "uploaded_by").prefetch_related("allowed_roles")
        if self.request.user.has_role_permission("digital.manage_digital_book"):
            return queryset
        role_filter = Q(is_public=True, is_active=True)
        if self.request.user.role_id:
            role_filter |= Q(allowed_roles=self.request.user.role, is_active=True)
        return queryset.filter(role_filter).distinct()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class BookReviewViewSet(RolePermissionModelViewSet):
    serializer_class = BookReviewSerializer
    permission_map = {
        "view": "reviews.view_review",
        "create": "reviews.add_review",
        "update": "reviews.moderate_review",
        "destroy": "reviews.moderate_review",
    }
    search_fields = ["book__title", "member__member_code", "review_text"]

    def get_queryset(self):
        queryset = BookReview.objects.select_related("book", "member__user", "moderated_by")
        if self.request.user.has_role_permission("reviews.moderate_review"):
            return queryset
        return queryset.filter(Q(status=BookReview.APPROVED) | Q(member__user=self.request.user)).distinct()

    def perform_update(self, serializer):
        serializer.save(moderated_by=self.request.user)


class AnnouncementViewSet(RolePermissionModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_map = {
        "view": "announcements.view_announcement",
        "create": "announcements.manage_announcement",
        "update": "announcements.manage_announcement",
        "destroy": "announcements.manage_announcement",
    }
    search_fields = ["title", "content"]

    def get_queryset(self):
        queryset = Announcement.objects.prefetch_related("target_roles")
        if self.request.user.has_role_permission("announcements.manage_announcement"):
            return queryset
        now = timezone.now()
        queryset = queryset.filter(status=Announcement.PUBLISHED, publish_date__lte=now).filter(
            Q(expire_date__isnull=True) | Q(expire_date__gte=now)
        )
        if self.request.user.role_id:
            queryset = queryset.filter(Q(target_roles=self.request.user.role) | Q(target_roles__isnull=True))
        return queryset.distinct()

    def perform_create(self, serializer):
        announcement = serializer.save(created_by=self.request.user)
        if announcement.status == Announcement.PUBLISHED and announcement.send_email:
            send_announcement_email(announcement)

    def perform_update(self, serializer):
        announcement = serializer.save()
        if announcement.status == Announcement.PUBLISHED and announcement.send_email and not announcement.email_sent:
            send_announcement_email(announcement)


class FAQViewSet(RolePermissionModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_map = {
        "view": "support.add_ticket",
        "create": "support.manage_support",
        "update": "support.manage_support",
        "destroy": "support.manage_support",
    }
    search_fields = ["question", "answer", "category"]


class SupportTicketViewSet(RolePermissionModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_map = {
        "view": "support.view_ticket",
        "create": "support.add_ticket",
        "update": "support.manage_support",
        "destroy": "support.manage_support",
    }
    search_fields = ["subject", "message", "user__username"]

    def get_queryset(self):
        queryset = SupportTicket.objects.select_related("user", "assigned_to")
        if not self.request.user.has_role_permission("support.manage_support"):
            queryset = queryset.filter(user=self.request.user)
        return queryset


class FeedbackViewSet(RolePermissionModelViewSet):
    serializer_class = FeedbackSerializer
    permission_map = {
        "view": "support.manage_support",
        "create": "support.add_ticket",
        "update": "support.manage_support",
        "destroy": "support.manage_support",
    }
    search_fields = ["name", "email", "message"]

    def get_queryset(self):
        queryset = Feedback.objects.select_related("user")
        if not self.request.user.has_role_permission("support.manage_support"):
            queryset = queryset.filter(user=self.request.user)
        return queryset


class LibraryProfileViewSet(RolePermissionModelViewSet):
    queryset = LibraryProfile.objects.all()
    serializer_class = LibraryProfileSerializer
    permission_map = {
        "view": "settings.manage_settings",
        "create": "settings.manage_settings",
        "update": "settings.manage_settings",
        "destroy": "settings.manage_settings",
    }


class SystemSettingViewSet(RolePermissionModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_map = {
        "view": "settings.manage_settings",
        "create": "settings.manage_settings",
        "update": "settings.manage_settings",
        "destroy": "settings.manage_settings",
    }
    search_fields = ["key", "description"]


class BackupScheduleViewSet(RolePermissionModelViewSet):
    queryset = BackupSchedule.objects.all()
    serializer_class = BackupScheduleSerializer
    permission_map = {
        "view": "settings.manage_backup",
        "create": "settings.manage_backup",
        "update": "settings.manage_backup",
        "destroy": "settings.manage_backup",
    }


class BackupRecordViewSet(RolePermissionReadOnlyViewSet):
    queryset = BackupRecord.objects.select_related("created_by").all()
    serializer_class = BackupRecordSerializer
    permission_map = {"view": "settings.manage_backup"}
    search_fields = ["file_name", "message"]


class ImportJobViewSet(RolePermissionModelViewSet):
    queryset = ImportJob.objects.select_related("created_by").all()
    serializer_class = ImportJobSerializer
    permission_map = {
        "view": "import_export.view_import_export",
        "create": "import_export.import_data",
        "update": "import_export.import_data",
        "destroy": "import_export.import_data",
    }


class ExportJobViewSet(RolePermissionModelViewSet):
    queryset = ExportJob.objects.select_related("created_by").all()
    serializer_class = ExportJobSerializer
    permission_map = {
        "view": "import_export.view_import_export",
        "create": "import_export.export_data",
        "update": "import_export.export_data",
        "destroy": "import_export.export_data",
    }


class ActivityLogViewSet(RolePermissionReadOnlyViewSet):
    queryset = ActivityLog.objects.select_related("user").all()
    serializer_class = ActivityLogSerializer
    permission_map = {"view": "activity.view_activity"}
    search_fields = ["action", "module", "path", "user__username"]


class AuditLogViewSet(RolePermissionReadOnlyViewSet):
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_map = {"view": "activity.view_audit"}
    search_fields = ["app_label", "model_name", "object_repr", "user__username"]


router = routers.DefaultRouter()
router.register("users", UserViewSet)
router.register("roles", RoleViewSet)
router.register("permissions", PermissionViewSet)
router.register("members", MemberViewSet)
router.register("student-profiles", StudentProfileViewSet)
router.register("teacher-profiles", TeacherProfileViewSet)
router.register("staff-profiles", StaffProfileViewSet)
router.register("librarian-profiles", LibrarianProfileViewSet)
router.register("authors", AuthorViewSet)
router.register("publishers", PublisherViewSet)
router.register("categories", CategoryViewSet)
router.register("shelves", ShelfViewSet)
router.register("locations", BookLocationViewSet)
router.register("books", BookViewSet, basename="book")
router.register("book-copies", BookCopyViewSet)
router.register("borrowing-policies", BorrowingPolicyViewSet)
router.register("borrow-records", BorrowRecordViewSet, basename="borrow-record")
router.register("return-records", ReturnRecordViewSet, basename="return-record")
router.register("renewal-records", RenewalRecordViewSet, basename="renewal-record")
router.register("reservations", ReservationViewSet, basename="reservation")
router.register("fines", FineViewSet, basename="fine")
router.register("payments", PaymentViewSet, basename="payment")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("email-reminders", EmailReminderViewSet, basename="email-reminder")
router.register("book-status-logs", BookStatusLogViewSet)
router.register("lost-books", LostBookViewSet)
router.register("damaged-books", DamagedBookViewSet)
router.register("repair-records", RepairRecordViewSet)
router.register("digital-categories", DigitalBookCategoryViewSet)
router.register("digital-books", DigitalBookViewSet, basename="digital-book")
router.register("reviews", BookReviewViewSet, basename="review")
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("faqs", FAQViewSet)
router.register("support-tickets", SupportTicketViewSet, basename="support-ticket")
router.register("feedback", FeedbackViewSet, basename="feedback")
router.register("library-profile", LibraryProfileViewSet)
router.register("system-settings", SystemSettingViewSet)
router.register("backup-schedules", BackupScheduleViewSet)
router.register("backup-records", BackupRecordViewSet)
router.register("import-jobs", ImportJobViewSet)
router.register("export-jobs", ExportJobViewSet)
router.register("activity-logs", ActivityLogViewSet)
router.register("audit-logs", AuditLogViewSet)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_overview(request):
    return Response(
        {
            "name": "Library Management System API",
            "version": "1.0",
            "auth": {
                "token": request.build_absolute_uri("/api/auth/token/"),
                "refresh": request.build_absolute_uri("/api/auth/token/refresh/"),
            },
            "endpoints": {
                "dashboard": request.build_absolute_uri("/api/dashboard/"),
                **{
                    prefix: request.build_absolute_uri(f"/api/{prefix}/")
                    for prefix, _, _ in router.registry
                },
            },
        }
    )
