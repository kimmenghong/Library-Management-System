from django.test.runner import DiscoverRunner


class LibraryDiscoverRunner(DiscoverRunner):
    """Run the corrected assignment app when no explicit test label is supplied."""

    def build_suite(self, test_labels=None, **kwargs):
        labels = test_labels or ["apps.library"]
        return super().build_suite(test_labels=labels, **kwargs)
