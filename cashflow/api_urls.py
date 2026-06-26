from rest_framework.routers import DefaultRouter

from . import views

# REST API: /api/records/, /api/statuses/, /api/types/, /api/categories/,
# /api/subcategories/
router = DefaultRouter()
router.register("records", views.RecordViewSet)
router.register("statuses", views.StatusViewSet)
router.register("types", views.TypeViewSet)
router.register("categories", views.CategoryViewSet)
router.register("subcategories", views.SubcategoryViewSet)

urlpatterns = router.urls
