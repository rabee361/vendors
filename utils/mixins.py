from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from utils.types import UserType

class SellerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_seller

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        
        # If authenticated but not a seller, redirect to their respective home
        user_type = self.request.user.user_type
        if user_type == UserType.ADMIN:
            return redirect('moderator_stats')
        return redirect('home')

class ModeratorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not self.request.user.user_type == UserType.ADMIN:
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
            elif user_type == UserType.ADMIN:
                return redirect('moderator_stats')
        return super().handle_no_permission()
