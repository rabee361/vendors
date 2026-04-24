from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from utils.types import UserType

from ..forms import BuyerProfileForm
from ..models import Order


class BuyerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
	def test_func(self):
		return self.request.user.is_authenticated and self.request.user.is_buyer

	def handle_no_permission(self):
		if not self.request.user.is_authenticated:
			return redirect('login')

		if self.request.user.user_type == UserType.SELLER:
			return redirect('vendor_dashboard')

		if self.request.user.user_type == UserType.ADMIN:
			return redirect('moderator_stats')

		return redirect('home')


class BuyerStatsView(BuyerRequiredMixin, View):
	template_name = 'buyer/index.html'

	def get(self, request):
		context = {
			'stats': {
				'orders_count': 18,
				'saved_products_count': 42,
				'ratings_count': 11,
				'active_cart_items': 7,
				'available_coupons_count': 5,
			},
			'insights': {
				'favorite_store': 'متجر النخبة',
				'last_order_number': 'A4B7C9',
				'next_reward': 'خصم 15% على الطلب القادم',
			},
		}
		return render(request, self.template_name, context)


class BuyerProfileView(BuyerRequiredMixin, View):
	template_name = 'buyer/profile.html'

	def get(self, request):
		form = BuyerProfileForm(instance=request.user)
		return render(request, self.template_name, {'form': form})

	def post(self, request):
		form = BuyerProfileForm(request.POST, request.FILES, instance=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'تم تحديث بيانات الحساب بنجاح.')
			return redirect('buyer_profile')
		return render(request, self.template_name, {'form': form})


class BuyerOrdersView(BuyerRequiredMixin, View):
	template_name = 'buyer/orders.html'

	def get(self, request):
		query = request.GET.get('q')
		orders = Order.objects.select_related('tenant').filter(email=request.user.email)

		if query:
			orders = orders.filter(order_number__icontains=query)

		orders = orders.order_by('-created_at')
		return render(request, self.template_name, {'orders': orders})


class BuyerOrderDetailView(BuyerRequiredMixin, View):
	template_name = 'buyer/order_detail.html'

	def get(self, request, pk):
		order = get_object_or_404(
			Order.objects.select_related('tenant').prefetch_related('items__product', 'items__product__category'),
			pk=pk,
			email=request.user.email,
		)
		return render(request, self.template_name, {'order': order})


class BuyerOrderDeleteView(BuyerRequiredMixin, View):
	def get(self, request, pk):
		order = get_object_or_404(Order, pk=pk, email=request.user.email)
		order.delete()
		messages.success(request, 'تم حذف الطلب بنجاح.')
		return redirect('buyer_orders')
