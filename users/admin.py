from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import User, Marriage, MarriageProposals


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name', 'email', 'gender', 'is_married')
    list_display_links = ('username',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_married', 'gender')
    ordering = ('username',)
    readonly_fields = ('last_login', 'date_joined')
    list_per_page = 20

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'ФИО'

@admin.register(Marriage)
class MarriageAdmin(admin.ModelAdmin):
    fields = ['husband', 'wife', 'status']
    list_display = ('str_display', 'husband_link', 'wife_link', 'status')
    list_display_links = ('str_display', )
    readonly_fields = ['created_at']

    ordering = ['created_at']
    search_fields = ['husband__first_name', 'husband__last_name','wife__first_name', 'wife__last_name',]
    list_filter = ['status']
    list_per_page = 10
    actions = ['set_active', 'set_divorced']


    def husband_link(self, obj):
        url = f'/admin/users/user/{obj.husband.id}/change/'
        return format_html('<a href="{}">{}</a>', url, obj.husband.get_full_name())
    husband_link.short_description = 'Муж'

    def wife_link(self, obj):
        url = f'/admin/users/user/{obj.wife.id}/change/'
        return format_html('<a href="{}">{}</a>', url, obj.wife.get_full_name())
    wife_link.short_description = 'Жена'

    @admin.action(description='Подписать брак')
    def set_active(self, request, queryset):
        marriages = list(queryset)
        users_to_update = []
        for marriage in marriages:
            marriage.status = Marriage.Status.ACTIVE
            marriage.husband.is_married = True
            marriage.wife.is_married = True
            users_to_update.extend([marriage.husband, marriage.wife])
        Marriage.objects.bulk_update(marriages, ['status'])

        type(marriages[0].husband).objects.bulk_update(users_to_update, ['is_married'])
        self.message_user(request, f"Успешно подписано {len(marriages)} браков")

    @admin.action(description='Расторгнуть брак')
    def set_divorced(self, request, queryset):
        marriages = list(queryset)
        users_to_update = []
        for marriage in marriages:
            marriage.status = Marriage.Status.DIVORCED
            marriage.husband.is_married = False
            marriage.wife.is_married = False
            users_to_update.extend([marriage.husband, marriage.wife])
        Marriage.objects.bulk_update(marriages, ['status'])

        type(marriages[0].husband).objects.bulk_update(users_to_update, ['is_married'])
        self.message_user(request, f"Расторгнуто {len(marriages)} браков")

    def str_display(self, obj):
        return str(obj)
    str_display.short_description = 'Брак'

@admin.register(MarriageProposals)
class MarriageProposalAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('sender__username', 'receiver__username')
    ordering = ('-created_at',)
    list_per_page = 20
    autocomplete_fields = ['sender', 'receiver']
    empty_value_display = '—'
