"""
Root conftest.py — pytest picks this up automatically.
No env-var patching needed; config.settings.test provides all defaults.
"""


def pytest_configure(config):
    """
    Work around Django/Python 3.14 compatibility issue.
    Patch django.template.context.Context.__copy__ to handle the super() issue.
    """
    import copy
    from django.template.context import Context

    original_copy = Context.__copy__

    def patched_copy(self):
        """Override __copy__ to work around Python 3.14 super() bug."""
        # Create a new instance and copy the dicts directly
        new_context = Context.__new__(Context)
        new_context.dicts = self.dicts[:]
        return new_context

    Context.__copy__ = patched_copy
