# 使用celery处理任务
# 在任务处理者一端加下面注释的几句
import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
# django.setup()
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as TimedSerializer
from goods.models import Goods, GoodsType, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django.template import loader

# 初始化Celery类的对象
app = Celery('celery_tasks.tasks', broker="redis://192.168.1.110:6379/8")


# 生成48小时有效期的私钥
TIMEDSER48 = TimedSerializer(settings.SECRET_KEY, 48 * 3600)


@app.task
def send_register_active_email(to_email, username, token):
    """
    发送激活邮件的方法
    :param to_email: 收件人的邮箱地址
    :param username: 激活邮件中需要包含用户名信息
    :param token: 激活邮件内容需要包含用户加密信息的token
    :return: None
    """
    # 发邮件
    subject = "天天生鲜欢迎信息"
    message = ""
    # 发送包含html标签的邮件内容时需要使用html_message
    html_message = """<h1>%s欢迎您成为天天生鲜注册会员,</h1><br />请点击如下链接激活您的账户(48小时内有效)<br /><a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/%s/</a><br /><br />如果您的激活链接已过期,请点击如下链接<a href="http://127.0.0.1:8000/user/resend_active_email/%s/">重新发送</a>""" % (username, token, token, username)
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    send_mail(subject, message, sender, recipient_list=receiver, html_message=html_message)
    print("celery发送邮件了")


@app.task
def generate_static_index():
    """
    首页静态化函数
    :return:
    """
    # 1.查询首页商品分类
    goods_type_list = GoodsType.objects.all()
    # print(goods_type_list)
    # 2.查询首页轮播图列表
    index_goods_banner_list = IndexGoodsBanner.objects.all().order_by('index')
    # print(index_goods_banner_list)
    # 3.查询首页活动展示信息列表
    index_promotion_banner_list = IndexPromotionBanner.objects.all().order_by('index')
    # print(index_promotion_banner_list)
    # 4.根据商品分类查询对应标题展示商品和图片展示商品
    for type in goods_type_list:
        title_goods_sku_list = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        image_goods_sku_list = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        type.title_goods_list = title_goods_sku_list
        type.image_goods_list = image_goods_sku_list
    # 返回应答
    context = {
        "goods_type_list": goods_type_list,
        "index_goods_banner_list": index_goods_banner_list,
        "index_promotion_banner_list": index_promotion_banner_list,
    }
    # 根据查询到的数据创建一个静态文件
    # 1. 加载模板文件
    temp = loader.get_template('staticindex.html')
    # 2. 替换模板中的变量
    content = temp.render(context)
    # 写入文件
    fpath = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(fpath, "w") as f:
        f.write(content)

