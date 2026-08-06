"""
Root conftest.py — pytest picks this up automatically.
No env-var patching needed; config.settings.test provides all defaults.
"""


def pytest_configure(config):
    """
    Work around Django 4.2 / Python 3.14 incompatibility.

    Python 3.14 added object.__copy__, which changes how copy.copy(super())
    behaves inside BaseContext.__copy__: the super() proxy is now copied
    as-is (returning the proxy itself) rather than delegating to the
    subclass. Patching BaseContext.__copy__ with a correct implementation
    fixes this for all subclasses (Context, RequestContext, etc.).
    """
    from django.template.context import BaseContext

    def _patched_base_copy(self):
        duplicate = type(self).__new__(type(self))
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _patched_base_copy


