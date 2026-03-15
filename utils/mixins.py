from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class SellerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_seller:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class ModeratorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.user_type == 'admin')

class VerificationRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_verified:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)