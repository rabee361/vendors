from django.views.generic import ListView, TemplateView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count
from ..models import Vendor, Product, Order, CustomUser, Buyer, StoreCategory
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django import forms


class ModeratorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.user_type == 'admin')

class ModeratorVendorsView(ModeratorRequiredMixin, ListView):
    model = Vendor
    template_name = 'moderator/vendors.html'
    context_object_name = 'vendors'
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Vendor.objects.filter(
                Q(store_name__icontains=query) | 
                Q(category__name__icontains=query)
            )
        return Vendor.objects.all().order_by('-created_at')

class ModeratorStatsView(ModeratorRequiredMixin, TemplateView):
    template_name = 'moderator/stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_vendors'] = Vendor.objects.count()
        context['total_products'] = Product.objects.count()
        context['total_orders'] = Order.objects.count()
        context['total_buyers'] = Buyer.objects.count()
        context['latest_vendors'] = Vendor.objects.order_by('-created_at')[:5]
        
        # Category distribution
        categories = StoreCategory.objects.annotate(vendor_count=Count('vendor'))
        total_v = context['total_vendors'] or 1
        category_data = []
        for cat in categories:
            percentage = round((cat.vendor_count / total_v) * 100)
            category_data.append({
                'name': cat.name,
                'count': cat.vendor_count,
                'percentage': percentage
            })
        context['category_distribution'] = sorted(category_data, key=lambda x: x['count'], reverse=True)[:5]
        
        return context

class ModeratorListView(ModeratorRequiredMixin, ListView):
    model = CustomUser
    template_name = 'moderator/moderators.html'
    context_object_name = 'moderators'
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        qs = CustomUser.objects.filter(user_type='admin')
        if query:
            qs = qs.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query)
            )
        return qs.order_by('-date_joined')

class ModeratorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'avatar']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and password != confirm_password:
            raise forms.ValidationError("كلمات المرور غير متطابقة.")
        return cleaned_data

class ModeratorAddView(ModeratorRequiredMixin, CreateView):
    model = CustomUser
    form_class = ModeratorForm
    template_name = 'moderator/add_moderator.html'
    success_url = reverse_lazy('moderator_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.user_type = 'admin'
        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data.get('password'))
        user.save()
        return super().form_valid(form)

class ModeratorUpdateView(ModeratorRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ModeratorForm
    template_name = 'moderator/update_moderator.html'
    success_url = reverse_lazy('moderator_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data.get('password'))
        user.save()
        return super().form_valid(form)

class ModeratorDeleteView(ModeratorRequiredMixin, DeleteView):
    model = CustomUser
    success_url = reverse_lazy('moderator_list')
    # Usually handled via HTMX or simple POST
