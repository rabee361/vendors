from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from utils.types import UserType

class SellerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_seller:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class ModeratorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.user_type == 'admin':
            return redirect('moderator_login')
        return super().dispatch(request, *args, **kwargs)

class UserAlreadyLoggedInMixin(UserPassesTestMixin):
    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            user_type = self.request.user.user_type
            if user_type == UserType.SELLER:
                return redirect('vendor_dashboard')
            elif user_type == UserType.BUYER:
                return redirect('home')
        return super().handle_no_permission()
