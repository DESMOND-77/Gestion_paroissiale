import logging
import traceback
from datetime import timedelta

from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.base_view import BaseAPIView
from core.response import standardized_response
from accounts.models import User, UserActivity

from accounts.serializers import (
    ChangePasswordSerializer,
    UserActivitySerializer,
    UserSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordResetSerializer,
    ConfirmPasswordResetSerializer,
    TokenRefreshSerializer,
    LogoutSerializer,
)

from .services import AuthenticationService

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class UserRegistrationView(BaseAPIView):
    """User registration endpoint."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        operation_description="Créer un nouveau compte utilisateur",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Enregistrement réussi",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user": openapi.Schema(type=openapi.TYPE_OBJECT),
                                "tokens": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "access_token": openapi.Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                        "refresh_token": openapi.Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                    },
                                ),
                                "message": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Erreur de validation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
        tags=["Authentication"],
    )

    def post(self, request):
        try:
            email = request.data.get("email")
            password = request.data.get("password")
            # Support both old (first_name/last_name) and new (prenom/nom) parameter names
            prenom = request.data.get("prenom") or request.data.get("first_name")
            nom = request.data.get("nom") or request.data.get("last_name")

            # use service layer for registration logic
            success, response_data, status_code = AuthenticationService.register(
                email=email,
                password=password,
                prenom=prenom,
                nom=nom,
                request_meta=request.META,
            )

            # create response based on service layer result

            response = Response(
                standardized_response(**response_data),
                status=status_code,
            )
            # set refresh token cookie of registration was successful and cookie security is enable
            if (
                success
                and status_code in (200, 201)
                and settings.JWT_AUTH_COOKIE_SECURE
            ):
                tokens = response_data.get("data", {}).get("tokens", {})
                if "refresh_token" in tokens and "refresh_expires_in" in tokens:
                    refresh_token = tokens["refresh_token"]
                    cookie_max_age = tokens["refresh_expires_in"]
                    response.set_cookie(
                        key=settings.JWT_COOKIE_NAME,
                        value=refresh_token,
                        expires=timezone.now() + timedelta(seconds=cookie_max_age),
                        secure=settings.JWT_AUTH_COOKIE_SECURE,
                        httponly=True,
                        samesite="Strict",
                        path="/",
                        domain=settings.SESSION_COOKIE_DOMAIN,
                    )

            if success:
                get_token(request)  # Ensure CSRF token is set

            # Log activity
            user = User.objects.filter(email=email).first()
            if user:
                UserActivity.objects.create(
                    user=user,
                    action="Register",
                    details="Enrollement au système",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
            return response
        except Exception as e:
            logger.error(f"Error in UserRegistrationView: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                standardized_response(
                    success=False, error="Registration failed,please try again."
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserLoginView(APIView):
    """API endpoint for user login with enhanced security features"""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        operation_description="Connecter un utilisateur et obtenir les tokens JWT",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Connexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user": openapi.Schema(type=openapi.TYPE_OBJECT),
                                "tokens": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "access_token": openapi.Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                        "refresh_token": openapi.Schema(
                                            type=openapi.TYPE_STRING
                                        ),
                                    },
                                ),
                            },
                        ),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            401: openapi.Response(
                description="Identifiants invalides ou compte verrouillé"
            ),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        try:

            email = request.data.get("email")
            password = request.data.get("password")
            device_info = request.data.get("device_info", {})
            # use service layer for authentication logic
            success, response_data, status_code = AuthenticationService.login(
                request,
                email=email,
                password=password,
                device_info=device_info,
                request_meta=request.META,
            )

            # create response based on service layer result
            response = Response(
                standardized_response(**response_data), status=status_code
            )

            # set refresh token cookie if login was successful nd cookie security is enable
            if success and status_code == 200 and settings.JWT_AUTH_COOKIE_SECURE:
                tokens = response_data.get("data", {}).get("tokens", {})
                if "refresh_token" in tokens and "refresh_expires_in" in tokens:
                    response.set_cookie(
                        key=settings.JWT_COOKIE_NAME,
                        value=tokens["refresh_token"],
                        expires=timezone.now()
                        + timedelta(seconds=tokens["refresh_expires_in"]),
                        secure=True,
                        httponly=True,
                        path="/",
                        domain=settings.SESSION_COOKIE_DOMAIN,
                    )
            # set CSRF token for added security
            if success:
                get_token(request)

            # Log activity
            user = User.objects.filter(email=email).first()
            if user:
                UserActivity.objects.create(
                    user=user,
                    action="login",
                    details="Connexion au système",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
            return response
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                standardized_response(
                    success=False,
                    error="An unexpected error occurred. Please try again",
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    required_role = "student"

    def get(self, request):
        user = request.user
        user_serializer = UserSerializer(user)
        return Response(
            standardized_response(
                data={"user": user_serializer.data},
                message="Bienvenue sur le tableau de bord.",
            ),
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(BaseAPIView):
    """
    API endpoint for refreshing JWT tokens with robust security measures
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        operation_description="Rafraîchir le JWT access token avec le refresh token",
        request_body=TokenRefreshSerializer,
        responses={
            200: openapi.Response(
                description="Token rafraîchi avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "refresh_token": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                            },
                        ),
                    },
                ),
            ),
            401: openapi.Response(description="Token invalide ou expiré"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        try:

            # first try to get refresh token from request body
            refresh_token = request.data.get("refresh_token")
            # if not in body, try get from HTTP-only cookie
            if not refresh_token and settings.JWT_AUTH_COOKIE_SECURE:
                refresh_token = request.COOKIES.get(settings.JWT_COOKIE_NAME)

            # use service layer for token refresh logic

            success, response_data, status_code = AuthenticationService.RefreshToken(
                refresh_token
            )

            # create response object
            response = Response(
                standardized_response(**response_data), status=status_code
            )

            # HTTP-only cookie if enable and refresh was successful
            if success and status_code == 200 and settings.JWT_AUTH_COOKIE_SECURE:
                tokens = response_data.get("data", {})
                if "refresh" in tokens and "refresh_expires_in" in tokens:
                    response.set_cookie(
                        key=settings.JWT_COOKIE_NAME,
                        value=tokens["refresh"],
                        expires=timezone.now()
                        + timedelta(seconds=tokens["refresh_expires_in"]),
                        samesite="Strict",
                        secure=True,
                        httponly=True,
                        path="/",
                        domain=settings.SESSION_COOKIE_DOMAIN,
                    )
            if success:
                get_token(request)
                # Log activité de renouvellement de token si utilisateur identifiable
                try:
                    from accounts.models import User as UserModel

                    token_data = response_data.get("data", {})
                    uid = (
                        token_data.get("user_id")
                        if isinstance(token_data, dict)
                        else None
                    )
                    if uid:
                        user_obj = UserModel.objects.filter(id=uid).first()
                        if user_obj:
                            UserActivity.objects.create(
                                user=user_obj,
                                action="login",
                                details="Renouvellement de token",
                                ip_address=get_client_ip(request),
                                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                            )
                except Exception:
                    pass  # Le logging ne doit pas bloquer le refresh

            return response
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return Response(
                standardized_response(
                    success=False, error="An error occurred during token refresh"
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ValidateTokenView(BaseAPIView):
    """Token validation with additional security checks"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get token from authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header.startswith("Bearer"):
            token = auth_header.split(" ")[1]

            # use service layer for token validation logic
            success, response_data, status_code = AuthenticationService.Validate_token(
                token, user
            )
            return Response(standardized_response(**response_data), status=status_code)
        return (
            Response(
                standardized_response(success=False, error="No token provided"),
                status=status.HTTP_400_BAD_REQUEST,
            ),
        )


class LogOutView(BaseAPIView):
    """Logout endpoint that invalidates tokens"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Déconnecter l'utilisateur et invalider les tokens",
        request_body=LogoutSerializer,
        responses={
            200: openapi.Response(
                description="Déconnexion réussie",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            401: openapi.Response(description="Non authentifié"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        try:
            user = request.user
            # Get refresh token
            refresh_token = None
            # Try to get from request data
            if "refresh_token" in request.data:
                refresh_token = request.data.get("refresh_token")
            # try to get from cookie
            elif settings.JWT_AUTH_COOKIE_SECURE:
                refresh_token = request.COOKIES.get(settings.JWT_COOKIE_NAME)
            # use service layer for logout
            success, response_data, status_code = AuthenticationService.logout(
                user=user, refresh_token=refresh_token
            )
            # create response object
            response = Response(
                standardized_response(**response_data), status=status_code
            )

            # clear the refresh token cookie if it was used
            if settings.JWT_AUTH_COOKIE_SECURE:
                response.delete_cookie(
                    key=settings.JWT_COOKIE_NAME,
                    path="/",
                    domain=settings.SESSION_COOKIE_DOMAIN,
                )
            # Log activity
            UserActivity.objects.create(
                user=user,
                action="logout",
                details="Deconnexion du système",
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            return response
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            logger.error(traceback.format_exc())

            # still try to clear cookie on error
            response = Response(
                standardized_response(success=True, message="Logout processed"),
                status=status.HTTP_200_OK,
            )

            if settings.JWT_AUTH_COOKIE_SECURE:
                response.delete_cookie(
                    key=settings.JWT_COOKIE_NAME,
                    path="/",
                    domain=settings.SESSION_COOKIE_DOMAIN,
                )
                return response


# ###########################################


class ChangePasswordView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Changer le mot de passe de l'utilisateur authentifié",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Mot de passe changé avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                description="Validation échouée ou ancien mot de passe incorrect"
            ),
            401: openapi.Response(description="Non authentifié"),
        },
        tags=["Password Management"],
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                standardized_response(success=False, error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                standardized_response(
                    success=False, error="Mot de passe actuel incorrect"
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        # Invalider tous les tokens existants
        from core.jwt_utils import TokenManager

        TokenManager.blacklist_all_user_tokens(user.id)

        # Log activité
        UserActivity.objects.create(
            user=user,
            action="update",
            details="Changement de mot de passe",
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            standardized_response(
                success=True, message="Mot de passe mis à jour avec succès"
            )
        )


class UserListView(BaseAPIView):
    serializer_class = UserSerializer
    # permission_classes = [IsAdmin]

    def get_queryset(self):
        return User.objects.all().order_by("-date_joined")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            paginated = paginator.get_paginated_response(serializer.data)
            return Response(standardized_response(data=paginated.data))

        serializer = self.serializer_class(queryset, many=True)
        return Response(standardized_response(data=serializer.data))


class UserDetailView(BaseAPIView):
    serializer_class = UserSerializer
    # permission_classes = [IsAdmin]

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.serializer_class(user)
        return Response(standardized_response(data=serializer.data))

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.serializer_class(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(standardized_response(data=serializer.data))
        return Response(
            standardized_response(
                success=False,
                error=serializer.errors,
                message="Erreur de validation des données.",
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=request.user,
            action="delete",
            details=f"Suppression de l'utilisateur {user.email}",
        )
        user.delete()
        return Response(
            standardized_response(
                success=True,
                message="Utilisateur supprimé avec succès.",
            ),
            status=status.HTTP_200_OK,
        )


class UserActivityView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    # permission_classes = [IsAdmin]

    def get_queryset(self):
        return UserActivity.objects.all().order_by("-timestamp")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return Response(standardized_response(data=paginated.data))

        serializer = self.get_serializer(queryset, many=True)
        return Response(standardized_response(data=serializer.data))


class MeView(BaseAPIView):
    """Retourne le profil de l'utilisateur connecté."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(standardized_response(data=serializer.data))


class CheckPermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        permission = request.data.get("permission")

        if not permission:
            return Response(
                standardized_response(
                    success=False,
                    error="Permission non spécifiée",
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_permission = request.user.has_permission(permission)

        return Response(
            standardized_response(
                data={
                    "has_permission": has_permission,
                    "permission": permission,
                    "user_role": request.user.role,
                }
            )
        )
