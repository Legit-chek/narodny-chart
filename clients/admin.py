from django.contrib import admin

from clients.models import AdPlacement, ClientContract, ContractItem, Service


class ContractItemInline(admin.TabularInline):
    model = ContractItem
    extra = 0


class AdPlacementInline(admin.TabularInline):
    model = AdPlacement
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ClientContract)
class ClientContractAdmin(admin.ModelAdmin):
    list_display = ("title", "company_name", "client", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "company_name", "client__username")
    inlines = [ContractItemInline, AdPlacementInline]


@admin.register(AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "placement_type", "status", "poll")
    list_filter = ("placement_type", "status")
    search_fields = ("title", "client__username", "contract__company_name")
