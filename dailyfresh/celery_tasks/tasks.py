# 使用celery处理任务
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as TimedSerializer

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
    html_message = """
           <h1>%s欢迎您成为天天生鲜注册会员,</h1><br />请点击如下链接激活您的账户(48小时内有效)<br /><a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/%s/</a><br /><br />如果您的激活链接已过期,请点击如下链接<a href="http://127.0.0.1:8000/user/resend_active_email/%s/">重新发送</a>
           """ % (username, token, token, username)
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    send_mail(subject, message, sender, recipient_list=receiver, html_message=html_message)
    print("celery发送邮件了")
