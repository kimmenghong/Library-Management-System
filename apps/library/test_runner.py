from django.conf import settings
from django.test import override_settings
from django.test.runner import DiscoverRunner


class LibraryDiscoverRunner(DiscoverRunner):
    """Run the corrected assignment app when no explicit test label is supplied."""

    def setup_test_environment(self, **kwargs):
        storages = {
            **settings.STORAGES,
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
        self._storage_override = override_settings(STORAGES=storages)
        self._storage_override.enable()
        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        self._storage_override.disable()

    def build_suite(self, test_labels=None, **kwargs):
        labels = test_labels or ["apps.library"]
        return super().build_suite(test_labels=labels, **kwargs)
