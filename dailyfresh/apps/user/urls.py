from django.urls import path
from .views import RegisterView, ActiveView, LoginView, ResendActiveEmailView, UserInfoView, UserAddressView, UserOrderView, LogoutView

app_name = "user"
urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),  # 注册处理
    path('active/<str:token>/', ActiveView.as_view(), name="active"),  # 用户激活处理
    path('login/', LoginView.as_view(), name="login"),  # 用户登录处理
    path('resend_active_email/<str:username>/', ResendActiveEmailView.as_view(), name="resend_active_email"),  # 重新发送激活链接
    path('order/', UserOrderView.as_view(), name="order"),  # 用户中心-订单页
    path('address/', UserAddressView.as_view(), name="address"),  # 用户中心-地址页
    path('logout/', LogoutView.as_view(), name="logout"),  # 用户退出登录处理
    path('', UserInfoView.as_view(), name="info"),  # 用户中心-信息页
]
