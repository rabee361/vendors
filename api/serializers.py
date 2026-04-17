import uuid
from collections import OrderedDict
from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Avg, Count, Prefetch
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from base.models import Offer, Order, OrderItem, Product
from utils.types import OrderStatus
from utils.validators import SyrianPhoneValidator

User = get_user_model()


class APILoginSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True, trim_whitespace=False)

	def validate(self, attrs):
		credentials = {
			User.USERNAME_FIELD: attrs['email'],
			'password': attrs['password'],
		}
		user = authenticate(request=self.context.get('request'), **credentials)

		if not user:
			raise serializers.ValidationError('Invalid email or password.')

		if not user.is_active:
			raise serializers.ValidationError('This account is inactive.')

		attrs['user'] = user
		return attrs

	def create(self, validated_data):
		user = validated_data['user']
		token, _ = Token.objects.get_or_create(user=user)
		return {
			'token': token.key,
			'user': {
				'id': user.pk,
				'email': user.email,
				'full_name': user.first_name,
				'user_type': user.user_type,
			},
		}


class ProductListSerializer(serializers.ModelSerializer):
	current_price = serializers.SerializerMethodField()

	class Meta:
		model = Product
		fields = [
			'id',
			'name',
            'current_price'
		]

	def get_current_price(self, obj):
		active_offer = self._get_active_offer(obj)
		if active_offer:
			return active_offer.get_discounted_price()
		return obj.price

	@staticmethod
	def _get_active_offer(product):
		active_offers = getattr(product, 'active_offers', None)
		if active_offers:
			return active_offers[0]
		return None


class OrderItemInputSerializer(serializers.Serializer):
	product_id = serializers.IntegerField(min_value=1)
	quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
	email = serializers.EmailField()
	full_name = serializers.CharField(max_length=150)
	phone = serializers.CharField(max_length=20, validators=[SyrianPhoneValidator()])
	city = serializers.CharField(max_length=100)
	address = serializers.CharField(max_length=255)
	notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
	items = OrderItemInputSerializer(many=True)

	def validate_items(self, value):
		if not value:
			raise serializers.ValidationError('At least one item is required.')
		return value

	def create(self, validated_data):
		merged_items = self._merge_items(validated_data['items'])
		product_ids = list(merged_items.keys())

		with transaction.atomic():
			products = self._get_locked_products(product_ids)
			products_by_id = {product.pk: product for product in products}

			missing_ids = [product_id for product_id in product_ids if product_id not in products_by_id]
			if missing_ids:
				raise serializers.ValidationError({
					'items': f'Products not found: {missing_ids}'
				})

			grouped_items = OrderedDict()
			for product_id, quantity in merged_items.items():
				product = products_by_id[product_id]
				if not product.is_active:
					raise serializers.ValidationError({
						'items': f'Product {product.pk} is inactive and cannot be ordered.'
					})

				if product.stock < quantity:
					raise serializers.ValidationError({
						'items': f'Insufficient stock for product {product.pk}. Available quantity: {product.stock}.'
					})

				current_price = self._get_current_price(product)
				vendor_id = product.tenant.pk
				line_total = current_price * quantity

				if vendor_id not in grouped_items:
					grouped_items[vendor_id] = {
						'vendor': product.tenant,
						'subtotal': Decimal('0.00'),
						'items': [],
					}

				grouped_items[vendor_id]['items'].append({
					'product': product,
					'quantity': quantity,
					'unit_price': current_price,
					'line_total': line_total,
				})
				grouped_items[vendor_id]['subtotal'] += line_total

			created_orders = []
			for vendor_data in grouped_items.values():
				order = Order.objects.create(
					tenant=vendor_data['vendor'],
					order_number=self._generate_order_number(),
					total=vendor_data['subtotal'],
					discount_amount=Decimal('0.00'),
					full_name=validated_data['full_name'],
					email=validated_data['email'],
					phone=validated_data['phone'],
					city=validated_data['city'],
					address=validated_data['address'],
					notes=validated_data.get('notes') or '',
					status=OrderStatus.PREPARING,
				)

				response_items = []
				for item in vendor_data['items']:
					product = item['product']
					quantity = item['quantity']
					product.stock -= quantity
					product.save(update_fields=['stock'])

					OrderItem.objects.create(
						tenant=vendor_data['vendor'],
						order=order,
						product=product,
						quantity=quantity,
						price_at_order=item['unit_price'],
					)

					response_items.append({
						'product_id': product.pk,
						'product_name': product.name,
						'quantity': quantity,
						'unit_price': item['unit_price'],
						'line_total': item['line_total'],
					})

				created_orders.append({
					'id': order.pk,
					'order_number': order.order_number,
					'vendor_id': vendor_data['vendor'].id,
					'vendor_name': vendor_data['vendor'].store_name,
					'subtotal': order.total,
					'discount_amount': order.discount_amount,
					'shipping_cost': order.shipping_cost,
					'total_cost': order.total_cost,
					'items': response_items,
				})

		grand_total = sum((order['total_cost'] for order in created_orders), Decimal('0.00'))
		return {
			'orders_count': len(created_orders),
			'grand_total': grand_total,
			'orders': created_orders,
		}

	@staticmethod
	def _merge_items(items):
		merged = OrderedDict()
		for item in items:
			product_id = item['product_id']
			merged[product_id] = merged.get(product_id, 0) + item['quantity']
		return merged

	@staticmethod
	def _get_locked_products(product_ids):
		today = timezone.now().date()
		active_offers = Offer.objects.filter(
			is_active=True,
			start_date__lte=today,
			end_date__gte=today,
		).order_by('created_at')

		return list(
			Product.objects.select_for_update()
			.select_related('tenant', 'tenant__category', 'category')
			.prefetch_related(Prefetch('offers', queryset=active_offers, to_attr='active_offers'))
			.filter(id__in=product_ids)
		)

	@staticmethod
	def _get_current_price(product):
		active_offers = getattr(product, 'active_offers', None)
		if active_offers:
			return active_offers[0].get_discounted_price()
		return product.price

	@staticmethod
	def _generate_order_number():
		while True:
			order_number = uuid.uuid4().hex[:8].upper()
			if not Order.objects.filter(order_number=order_number).exists():
				return order_number


def get_product_list_queryset():
	today = timezone.now().date()
	active_offers = Offer.objects.filter(
		is_active=True,
		start_date__lte=today,
		end_date__gte=today,
	).order_by('created_at')

	return (
		Product.objects.filter(is_active=True)
		.select_related('tenant', 'tenant__category', 'category')
		.prefetch_related(Prefetch('offers', queryset=active_offers, to_attr='active_offers'))
		.order_by('-created_at')
	)
