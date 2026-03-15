from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

class SellerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_seller:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class ModeratorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.user_type == 'admin')

class VerificationRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return not self.request.user.is_authenticated or not self.request.user.is_verified