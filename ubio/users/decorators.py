from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test


def login_required(fn=None,
                   redirect_field_name=REDIRECT_FIELD_NAME,
                   login_url=None):
    """Decorator for views that checks that the user is logged in and active,
    redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_active,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if fn:
        return actual_decorator(fn)
    return actual_decorator


def admin_required(fn=None,
                   redirect_field_name=REDIRECT_FIELD_NAME,
                   login_url=None):
    """Decorator for views that checks that the user is logged in,
    active and is a superuser (administrator/chair), and redirecting to the
    login page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_active and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if fn:
        return actual_decorator(fn)
    return actual_decorator
