from django.shortcuts import redirect
from functools import wraps

def seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('seller_auth')
        if not hasattr(request.user, 'vendor_profile'):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
