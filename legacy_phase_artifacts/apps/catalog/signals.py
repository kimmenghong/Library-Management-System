from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Book, BookCopy


def synchronize_book_status(book_id):
    statuses = set(
        BookCopy.objects.filter(book_id=book_id).values_list("status", flat=True)
    )
    if BookCopy.AVAILABLE in statuses or not statuses:
        status = Book.AVAILABLE
    elif BookCopy.BORROWED in statuses:
        status = Book.BORROWED
    elif BookCopy.UNDER_REPAIR in statuses:
        status = Book.UNDER_REPAIR
    elif BookCopy.DAMAGED in statuses:
        status = Book.DAMAGED
    else:
        status = Book.LOST
    Book.objects.filter(pk=book_id).exclude(status=status).update(status=status)


@receiver(post_save, sender=BookCopy)
def synchronize_after_copy_save(sender, instance, **kwargs):
    synchronize_book_status(instance.book_id)


@receiver(post_delete, sender=BookCopy)
def synchronize_after_copy_delete(sender, instance, **kwargs):
    synchronize_book_status(instance.book_id)
