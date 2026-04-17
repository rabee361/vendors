from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import APILoginSerializer, OrderCreateSerializer, ProductListSerializer, get_product_list_queryset


class APILoginAPIView(APIView):
	permission_classes = [AllowAny]
	authentication_classes = []

	def post(self, request, *args, **kwargs):
		serializer = APILoginSerializer(data=request.data, context={'request': request})
		serializer.is_valid(raise_exception=True)
		payload = serializer.save()
		return Response(payload, status=status.HTTP_200_OK)


class ProductListAPIView(APIView):
	authentication_classes = [TokenAuthentication]

	def get(self, request, *args, **kwargs):
		serializer = ProductListSerializer(
			get_product_list_queryset(),
			many=True,
			context={'request': request},
		)
		return Response(serializer.data, status=status.HTTP_200_OK)


class OrderCreateAPIView(APIView):
	authentication_classes = [TokenAuthentication]

	def post(self, request, *args, **kwargs):
		serializer = OrderCreateSerializer(data=request.data, context={'request': request})
		serializer.is_valid(raise_exception=True)
		created_orders = serializer.save()
		return Response(created_orders, status=status.HTTP_201_CREATED)
