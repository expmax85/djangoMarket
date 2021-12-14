from django.urls import path

from .views import MainPageView, ProductDetailView, StoreView, AddReview, \
    ProductFilterView, SearchView, AddToWishList, \
    AddToCart, DeleteFromCart

urlpatterns = [
    path('', MainPageView.as_view(), name='main_page'),
    path('add_to_wish/', AddToWishList.as_view(), name='add_to_wish'),
    path('add_to_cart/', AddToCart.as_view(), name='add_to_cart'),
    path('delete_from_cart/', DeleteFromCart.as_view(), name='delete_from_cart'),
    path('filter/', ProductFilterView.as_view(), name='filter'),
    path('search/', SearchView.as_view(), name='search'),
    # path('json_filter/', JsonFilterStore.as_view(), name='json_filter'),
    path('store/', StoreView.as_view(), name='store'),
    path('products/<str:category>/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('review/<int:pk>/', AddReview.as_view(), name='add_review'),
]
