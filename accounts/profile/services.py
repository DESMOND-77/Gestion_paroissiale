import logging
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile

from core.jwt_utils import TokenManager
from accounts.serializers import UserSerializer

logger = logging.getLogger(__name__)


class ProfileService:
    @staticmethod
    def get_profile(user, request=None):
        """Get userprofile

        Args:
            user (object): user object
            request (optional): requête pour construire les URLs absolues (photo).

        Returns:
            dict: serialized user data
        """
        serializer = UserSerializer(user, context={"request": request})
        return serializer.data

    @staticmethod
    def update_profile(user, data, files=None, request=None):
        """Update user profile data

        Args:
            user (object): User object
            data (dict): Update profile data
            file (dict, optional): File from the request. Defaults to None.
        Returns:
            tuple : (success,response_dict,status_code)
        """
        try:
            # Handle profile picture file if provided
            if files and "profile_picture" in files:
                success = ProfileService._process_profile_picture_file(
                    user, files["profile_picture"]
                )
                if not success:
                    return (
                        False,
                        {
                            "success": False,
                            "error": "Failed to process profile picture",
                        },
                        400,
                    )
            # Handle password change if provided
            if "current_password" in data and "new_password" in data:
                result = ProfileService._process_password_change(
                    user, data.get("current_password"), data.get("new_password")
                )
                if not result["success"]:
                    return False, {"success": False, "error": result["error"]}, 400
            # Remove processed fields before passing to serializer
            safe_data = {
                k: v
                for k, v in data.items()
                if k not in ["profile_picture", "current_password", "new_password"]
            }

            # update through serializer
            serializer = UserSerializer(
                user, data=safe_data, partial=True, context={"request": request}
            )

            if serializer.is_valid():
                serializer.save()
                return (
                    True,
                    {
                        "success": True,
                        "data": serializer.data,
                        "message": "Profile updated successfully",
                    },
                    200,
                )

            return False, {"success": False, "error": serializer.errors}
        except Exception as e:
            logger.error(f"Profile picture error: {str(e)}")
            return False, {"success": False, "error": "Failed to update profile"}, 500

    @staticmethod
    def _process_profile_picture_file(user, file):
        """Process uploaded picture file

        Args:
            user (object): User object
            file (): uploaded file object (InMemoryUploadedFile or UploadedFile)

        Returns:
            bool: success status
        """
        try:
            # Validate file type
            if not ProfileService._is_valid_image_file(file):
                logger.error(f"Invalid image file type: {file.content_type}")
                return False
            # Validate file size (e.g, max 5Mb)
            max_size = 5 * 1024 * 1024  # 5 MB
            max_dim = (1024, 1024)  # max width/height
            if file.size > max_size:
                logger.error(f"File too large: {file.size}")
                return False
            # Handle existing profile
            if user.profile_picture:
                try:
                    if os.path.isfile(user.profile_picture):
                        os.remove(user.profile_picture)
                        logger.info(
                            f"Removed old profile picture: {user.profile_picture.path}"
                        )
                except Exception as e:
                    logger.warning(f"Could not remove old profile picture: {str(e)}")

            # set new profile picture
            file.name = f"profile_{user.id}{os.path.splitext(file.name)[1]}"
            user.profile_picture = file
            user.save(update_fields=["profile_picture"])
            logger.info(f"profile picture updated for user: {user.id}")
            return True
        except Exception as e:
            logger.info(f"Error processing profile picture: {str(e)}")

    @staticmethod
    def _process_password_change(user, current_password, new_password):
        """Process password change

        Args:
            user (object): User object
            current_password (str): Current user password
            new_password (str): New password to set

        Returns:
            dict: Result flag and error message if applicable
        """
        # Verify current password
        if not user.check_password(current_password):
            return {"success": False, "error": "Mot de passe actuel incorrect"}

        # Validate new password
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return {"success": False, "error": ", ".join(e.messages)}

        # update password
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Log password change for security audit
        logger.info(f"Password changed for user: {user.id}")

        # Invalidate all existing refresh tokens for security
        TokenManager.blacklist_all_user_tokens(user.id)

        return {"success": True, "message": "Mot de passe modifié avec succès"}

    @staticmethod
    def _is_valid_image_file(file):
        """Validate uploaded image file

        Args:
            file (): Uploaded file object

        Returns :
                bool: True if valid uploaded file
        """
        # check if it's a proper uploaded file
        if not isinstance(file, (InMemoryUploadedFile, UploadedFile)):  # BUG#3 fix
            return False

        # Check content type
        valid_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in valid_types:
            return False

        # Check file extensions
        valid_extensions = [".jpeg", ".jpg", ".png", ".gif", ".webp"]
        _, file_ext = os.path.splitext(
            file.name.lower()
        )  # name est une propriété, pas une méthode
        if file_ext not in valid_extensions:
            return False

        # Tous les critères sont respectés
        return True
