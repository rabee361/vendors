from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Q, Count
from django.urls import reverse_lazy
from ..models import Vendor, Product, Order, CustomUser, Buyer, StoreCategory
from ..forms import CategoryForm, ModeratorForm, ModeratorLoginForm, ModeratorVendorForm
from utils.mixins import ModeratorRequiredMixin
from django.contrib.auth import login, logout


class ModeratorVendorsView(ModeratorRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q')
        if query:
            vendors = Vendor.objects.filter(
                Q(store_name__icontains=query) | 
                Q(category__name__icontains=query)
            )
        else:
            vendors = Vendor.objects.all()
        
        vendors = vendors.order_by('-created_at')
        return render(request, 'moderator/vendors.html', {'vendors': vendors})

class ModeratorVendorUpdateView(ModeratorRequiredMixin, View):
    template_name = 'moderator/vendor_form.html'

    def get(self, request, pk):
        instance = get_object_or_404(Vendor, pk=pk)
        form = ModeratorVendorForm(instance=instance)
        return render(request, self.template_name, {'form': form, 'object': instance})

    def post(self, request, pk):
        instance = get_object_or_404(Vendor, pk=pk)
        form = ModeratorVendorForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('moderator_vendors')
        return render(request, self.template_name, {'form': form, 'object': instance})

class ModeratorVendorDeleteView(ModeratorRequiredMixin, View):
    def get(self, request, pk):
        instance = get_object_or_404(Vendor, pk=pk)
        user = instance.user
        instance.delete()
        user.delete()
        return redirect('moderator_vendors')

class ModeratorStatsView(ModeratorRequiredMixin, View):
    def get(self, request):
        total_vendors = Vendor.objects.count()
        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        total_buyers = Buyer.objects.count()
        latest_vendors = Vendor.objects.order_by('-created_at')[:5]
        
        # Category distribution
        categories = StoreCategory.objects.annotate(vendor_count=Count('vendor'))
        total_v = total_vendors or 1
        category_data = []
        for cat in categories:
            percentage = round((cat.vendor_count / total_v) * 100)
            category_data.append({
                'name': cat.name,
                'count': cat.vendor_count,
                'percentage': percentage
            })
        category_distribution = sorted(category_data, key=lambda x: x['count'], reverse=True)[:5]
        
        context = {
            'total_vendors': total_vendors,
            'total_products': total_products,
            'total_orders': total_orders,
            'total_buyers': total_buyers,
            'latest_vendors': latest_vendors,
            'category_distribution': category_distribution,
        }
        return render(request, 'moderator/stats.html', context)

class ModeratorLoginView(View):
    def get(self, request):
        form = ModeratorLoginForm()
        return render(request, 'moderator/login.html', {
            'form': form
        })

    def post(self, request):
        form = ModeratorLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            return redirect('moderator_dashboard')
        
        return render(request, 'moderator/login.html', {
            'form': form
        })

class ModeratorLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('moderator_login')

class ModeratorListView(ModeratorRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q')
        qs = CustomUser.objects.filter(user_type='admin')
        if query:
            qs = qs.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query)
            )
        moderators = qs.order_by('-date_joined')
        return render(request, 'moderator/moderators.html', {'moderators': moderators})

class ModeratorAddView(ModeratorRequiredMixin, View):
    template_name = 'moderator/moderator_form.html'
    
    def get(self, request):
        form = ModeratorForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ModeratorForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'admin'
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data.get('password'))
            user.save()
            return redirect('moderator_list')
        return render(request, self.template_name, {'form': form})

class ModeratorUpdateView(ModeratorRequiredMixin, View):
    template_name = 'moderator/moderator_form.html'

    def get(self, request, pk):
        instance = get_object_or_404(CustomUser, pk=pk, user_type='admin')
        form = ModeratorForm(instance=instance)
        return render(request, self.template_name, {'form': form, 'object': instance})

    def post(self, request, pk):
        instance = get_object_or_404(CustomUser, pk=pk, user_type='admin')
        form = ModeratorForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data.get('password'))
            user.save()
            return redirect('moderator_list')
        return render(request, self.template_name, {'form': form, 'object': instance})

class ModeratorDeleteView(ModeratorRequiredMixin, View):
    def get(self, request, pk):
        instance = get_object_or_404(CustomUser, pk=pk, user_type='admin')
        instance.delete()
        return redirect('moderator_list')

class ModeratorCategoriesView(ModeratorRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q')
        if query:
            categories = StoreCategory.objects.filter(name__icontains=query)
        else:
            categories = StoreCategory.objects.all()
        categories = categories.order_by('name')
        return render(request, 'moderator/categories.html', {'categories': categories})

class ModeratorCategoryAddView(ModeratorRequiredMixin, View):
    template_name = 'moderator/category_form.html'

    def get(self, request):
        form = CategoryForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('moderator_categories')
        return render(request, self.template_name, {'form': form})

class ModeratorCategoryUpdateView(ModeratorRequiredMixin, View):
    template_name = 'moderator/category_form.html'

    def get(self, request, pk):
        instance = get_object_or_404(StoreCategory, pk=pk)
        form = CategoryForm(instance=instance)
        return render(request, self.template_name, {'form': form, 'object': instance})

    def post(self, request, pk):
        instance = get_object_or_404(StoreCategory, pk=pk)
        form = CategoryForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('moderator_categories')
        return render(request, self.template_name, {'form': form, 'object': instance})

class ModeratorCategoryDeleteView(ModeratorRequiredMixin, View):
    def get(self, request, pk):
        instance = get_object_or_404(StoreCategory, pk=pk)
        instance.delete()
        return redirect('moderator_categories')
