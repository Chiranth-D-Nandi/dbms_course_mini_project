# Owner: Person A
"""
Authentication endpoints: Registration, Login, and Profile details.
Integrates with MySQL `app_user` table and SimpleJWT token generation.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import AppUser
from .serializers import RegisterRequestSerializer, LoginRequestSerializer, AppUserSerializer
from .auth_backend import hash_password, verify_password, CustomUserWrapper
from .permissions import IsAuthenticatedCustom

def get_tokens_for_user(user: AppUser):
    wrapped = CustomUserWrapper(user)
    refresh = RefreshToken.for_user(wrapped)
    refresh["user_id"] = user.user_id
    refresh["role"] = user.role
    refresh["email"] = user.email
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid input", "details": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if AppUser.objects.filter(email=data["email"]).exists():
            return Response({"error": {"code": "EMAIL_EXISTS", "message": "Email is already registered", "details": {}}}, status=status.HTTP_409_CONFLICT)

        if AppUser.objects.filter(phone=data["phone"]).exists():
            return Response({"error": {"code": "PHONE_EXISTS", "message": "Phone number is already registered", "details": {}}}, status=status.HTTP_409_CONFLICT)

        hashed = hash_password(data["password"])
        new_user = AppUser.objects.create(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data["phone"],
            password_hash=hashed,
            role=data.get("role", "CUSTOMER"),
            is_active=True,
        )

        tokens = get_tokens_for_user(new_user)
        return Response({
            "message": "User registered successfully",
            "user": AppUserSerializer(new_user).data,
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid input", "details": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            user = AppUser.objects.using("readonly").get(email=data["email"])
        except AppUser.DoesNotExist:
            return Response({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password", "details": {}}}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"error": {"code": "USER_INACTIVE", "message": "Account has been deactivated", "details": {}}}, status=status.HTTP_403_FORBIDDEN)

        if not verify_password(data["password"], user.password_hash):
            return Response({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password", "details": {}}}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = get_tokens_for_user(user)
        return Response({
            "message": "Login successful",
            "user": AppUserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request):
        user = request.user.app_user
        return Response({
            "user": AppUserSerializer(user).data,
        }, status=status.HTTP_200_OK)
