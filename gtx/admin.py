from django.contrib import admin
from django.contrib.auth import get_user_model
from authemail.admin import EmailUserAdmin

class AdminUser(EmailUserAdmin):
	fieldsets = (
		(None, {'fields': ('email', 'password')}),
		('Personal Info', {'fields': ('first_name', 'last_name')}),
		('Permissions', {'fields': ('is_active', 'is_staff', 
									   'is_superuser', 'is_verified', 
									   'groups', 'user_permissions')}),
		('Important dates', {'fields': ('last_login', 'date_joined')}),
		('Custom info', {'fields': ('full_name',)}),
	)

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), AdminUser)