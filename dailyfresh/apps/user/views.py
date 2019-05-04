from django.shortcuts import render, redirect, reverse
from .models import User, Address
from goods.models import GoodsSKU
from django.http import HttpResponse
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django_redis import get_redis_connection
from celery_tasks.tasks import send_register_active_email, TIMEDSER48
from itsdangerous import SignatureExpired
from utils.mixin import LoginRequiredMixin
import re


# Create your views here.


# /user/register/
class RegisterView(View):
    """注册类视图"""

    def get(self, request):
        """获取登录页面"""
        return render(request, 'register.html')

    def post(self, request):
        """进行注册处理"""
        # 1. 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        is_allow_greement = request.POST.get("allow")  # 是否同意用户协议

        # 2. 进行数据校验
        # 首先校验数据是否填写
        if not all([username, password, cpassword, email]):
            """数据不完整"""
            return render(request, 'register.html', {'errmsg': "数据不完整"})
        # 检验用户名长度
        if len(username) < 5 or len(username) > 20:
            return render(request, 'register.html', {'errmsg': "用户名长度为5到20位"})
        # 校验邮箱是否正确
        if not re.match(r'^[a-z0-9][\w.-]*@[a-z0-9-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': "邮箱格式不正确"})
        # 校验两次秘密是否一致
        if password != cpassword:
            return render(request, 'register.html', {'errmsg': "两次输入的密码不一致"})
        # 检验密码长度是否符合
        if len(password) < 8 or len(password) > 20:
            return render(request, 'register.html', {'errmsg': "密码长度为8到20位"})
        # 校验是否同意协议
        if is_allow_greement != 'on':
            return render(request, 'register.html', {'errmsg': "请同意协议"})
        # 校验用户名是否已存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmsg': "用户名已存在"})
        # TODO 校验邮箱是否已存在

        # 3. 业务处理
        # 进行用户注册
        user = User.objects.create_user(username, email, password)
        # 第一次注册的用户不能是激活的,需要点击激活链接才能激活
        user.is_active = 0
        user.save()
        # 发送激活用户的链接,需要包含用户的身份,id,但是不能直接传递id,需要加密用户信息
        info = {"user_id": user.id}
        token = TIMEDSER48.dumps(info).decode()
        send_register_active_email.delay(email, username, token)

        # 4. 返回应答,跳转到首页
        return redirect(reverse('goods:index'))


# /user/resend_active_email/<str:username>/
class ResendActiveEmailView(View):
    """重新发送激活链接"""

    def get(self, request, username):
        """重新发送激活链接"""
        # 1. 根据用户名获取用户对象
        try:
            user = User.objects.get(username=username)
            # 2. 判断用户是否已经激活
            if user.is_active == 1:
                # 已经激活的用户不再发送邮件,直接跳转到登录页面
                return redirect(reverse('user:login'))
            # 生成包含用户id加密信息的token
            token = TIMEDSER48.dumps({"user_id": user.id}).decode()
            # 发送邮件
            send_register_active_email.delay(user.email, username, token)
            return HttpResponse("""<h1>激活链接重新发送成功</h1><br><a href="/user/login/">点击跳转到登录页面</a>""")
        except User.DoesNotExist as e:
            # 用户不存在
            return HttpResponse("大哥,你想要激活的用户不存在,求放过!!!")


# /user/active/<str:token>/
class ActiveView(View):
    """用户激活"""

    def get(self, request, token):
        """进行用户激活"""
        # 1. 解密,获取要激活的用户信息
        try:
            info = TIMEDSER48.loads(token)
            user_id = info['user_id']
            # 根据id获取用户对象
            user = User.objects.get(id=user_id)
            # 判断用户是否已激活,若已激活,跳转到登录页面;没有激活才激活用户并自动登录
            if user.is_active == 1:
                # TODO 返回一个页面,告知用户账号已经被激活,倒计时跳转到首页进行登录
                return redirect(reverse('user:login'))
            user.is_active = 1
            user.save()
            # 自动登录用户并跳转到首页
            # TODO 使用login函数登入用户并跳转到首页
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接失效
            return HttpResponse("激活链接已失效,请重新获取")


# /user/login
class LoginView(View):
    """登录视图"""

    def get(self, request):
        # 判断cookie中是否记录了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = "checked"
        else:
            username = ""
            checked = ""

        return render(request, 'login.html', {"username": username, "checked": checked})

    def post(self, request):
        """用户登录处理"""
        # 1. 获取数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')  # 记住用户名单选框
        # 2. 数据校验
        # 校验数据完整性
        if not all([username, password]):
            return render(request, 'login.html', {"errmsg": "数据不完整"})
        # 校验用户名密码是否正确
        user = authenticate(username=username, password=password)
        # 3. 业务处理
        if user is not None:
            # 用户名密码校验通过
            if user.is_active:
                # 记住用户登录状态
                login(request, user)
                # 获取登录后需要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
                # 判断是否需要记住用户名
                if remember == "on":
                    # 使用cookie记住用户名
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    # 用户未勾选记住用户名,删除可能已经保存的cookie
                    response.delete_cookie('username')
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {"errmsg": "用户未激活,请前往邮箱激活您的账户"})
        else:
            # the authentication system was unable to verify the username and password
            return render(request, 'login.html', {"errmsg": "用户名或密码错误"})


# /user/
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""

    def get(self, request):
        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)
        # 创建连接到redis数据库的实例
        con = get_redis_connection("default")  # con是StrictRedis的一个实例
        # 从redis中读取用户浏览记录
        # 采用redis的list存储用户浏览商品记录,格式:history_userid:[3,1,2,5,4,7]
        history_key = "history_%d" % user.id
        # 获取用户最近浏览的五个商品
        sku_ids = con.lrange(history_key, 0, 4)
        # 根据商品id查询数据库返回商品列表
        goods_list = []
        for goods_id in sku_ids:
            goods = GoodsSKU.objects.get(id=goods_id)
            # print("浏览的商品是%s"%goods.name)
            goods_list.append(goods)
        context = {
            "page": "user",
            "address": address,
            "goods_list": goods_list
        }
        return render(request, 'user_center_info.html', context)


# /user/order/
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""

    def get(self, request):
        # 获取用户的订单信息
        return render(request, 'user_center_order.html', {"page": "order"})


# /user/address/
class UserAddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""

    def get(self, request):
        """获取用户的默认收货地址"""
        # 判断是否有收货地址
        address = Address.objects.get_default_address(request.user)
        return render(request, 'user_center_site.html', {"page": "address", "address": address})

    def post(self, request):
        """用户添加收货地址"""
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('address')
        phonenumber = request.POST.get('phonenumber')
        zipcode = request.POST.get('zipcode')

        # 校验数据完整性
        if not all([receiver, addr, phonenumber]):
            return render(request, 'user_center_site.html', {"errmsg": "数据不完整"})

        # 校验手机号
        if not re.match(
                r'^((13[0-9])|(14[5,7])|(15[0-3,5-9])|(17[0,3,5-8])|(18[0-9])|166|198|199|(147))\d{8}$',
                phonenumber):
            return render(request, 'user_center_site.html', {"errmsg": "手机号码格式不正确"})

        # 业务处理
        user = request.user
        # 判断是否已经存在默认收货地址
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            # 不存在默认收货地址,创建的地址就作为默认收货地址
            is_default = True
        # 创建用户地址
        Address.objects.create(
            user=user,
            addr=addr,
            zip_code=zipcode,
            phone=phonenumber,
            is_default=is_default
        )
        # 返回应答,刷新页面
        return redirect(reverse('user:address'))


# /user.logout/
class LogoutView(View):
    """用户退出视图"""

    def get(self, request):
        # 执行退出登录操作,清除session信息
        logout(request)
        # 跳转到首页
        return redirect(reverse('goods:index'))
