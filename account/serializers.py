from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import UserProfile, Level2Credentials, Level3Credentials


class SignupSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=80, required=True)
    class Meta:
        model = UserProfile
        fields = ['email', 'password', 'full_name']


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    code = serializers.CharField(max_length=6, min_length=6)


class ResendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(max_length=128, min_length=8)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)


class CreateTransactionPinSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4, min_length=4)
    confirm_pin = serializers.CharField(max_length=4, min_length=4)

    def validate_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        return value

    def validate(self, data):
        if data['pin'] != data['confirm_pin']:
            raise serializers.ValidationError({"confirm_pin": "PINs do not match."})
        return data


class UpdateTransactionPinSerializer(serializers.Serializer):
    old_pin = serializers.CharField(max_length=4, min_length=4)
    new_pin = serializers.CharField(max_length=4, min_length=4)
    confirm_new_pin = serializers.CharField(max_length=4, min_length=4)

    def validate_new_pin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("PIN must contain only digits.")
        return value

    def validate(self, data):
        if data['new_pin'] != data['confirm_new_pin']:
            raise serializers.ValidationError({"confirm_new_pin": "PINs do not match."})
        return data


class Level2CredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level2Credentials
        fields = ['nin', 'nin_image']


class Level3CredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level3Credentials
        fields = [
            'house_address_1', 'house_address_2', 'nearest_bus_stop',
            'city', 'state', 'country', 'proof_of_address_image',
            'face_verification_image'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    level2_credentials = Level2CredentialsSerializer(read_only=True)
    level3_credentials = Level3CredentialsSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'full_name', 'phone_number', 'dp', 'level',
            'transaction_limit', 'status', 'is_verified', 'date_joined',
            'last_login', 'level2_credentials', 'level3_credentials','has_pin'
        ]
        read_only_fields = [
            'id', 'email', 'level', 'transaction_limit', 'status',
            'is_verified', 'date_joined', 'last_login'
        ]


class ProfilePictureSerializer(serializers.Serializer):
    dp = serializers.ImageField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128, min_length=8)
    confirm_new_password = serializers.CharField(max_length=128, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})
        return attrs


class AddPhoneNumberSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()

    def validate_phone_number(self, value):
        if UserProfile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value
