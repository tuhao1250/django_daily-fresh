from django.urls import path
from goods.views import IndexView, DetailView, ListView

app_name = "goods"
urlpatterns = [
    path('index/', IndexView.as_view(), name="index"),  # 首页路由地址
    path('detail/<int:goods_id>', DetailView.as_view(), name="detail"),  # 商品详情页路由地址
    path('list/<int:type_id>/<int:page_index>/', ListView.as_view(), name="list"),  # 列表页地址
]
