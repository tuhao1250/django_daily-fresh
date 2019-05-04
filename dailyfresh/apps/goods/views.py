from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from goods.models import Goods, GoodsType, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, \
    IndexPromotionBanner
from order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator

# Create your views here.


# def index(request):
#     """首页视图"""
#     return render(request, 'index.html')


class IndexView(View):
    """首页视图类"""

    def get(self, request):
        user = request.user
        # 先尝试从缓存中读取数据
        context = cache.get('index_page_data')
        if not context:
            # 没有读取到缓存的时候,查询数据库,然后设置缓存
            print("设置缓存")
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
                # print(title_goods_sku_list)
                # print(image_goods_sku_list)
                type.title_goods_list = title_goods_sku_list
                type.image_goods_list = image_goods_sku_list
            # 获取用户购物车商品数量(商品种类计数)
            # 判断用户是否登录,没有登录则购物车中商品数量显示为0(应该从本地存储读取)
            context = {
                "goods_type_list": goods_type_list,
                "index_goods_banner_list": index_goods_banner_list,
                "index_promotion_banner_list": index_promotion_banner_list,
            }
            cache.set('index_page_data', context, 3600)
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            # 1.读取redis数据库中用户对应的key对应的hash
            cart_key = "cart_%d" % user.id
            # 2.建立redis连接
            con = get_redis_connection("default")  # con是StrictRedis的一个实例
            cart_count = con.hlen(cart_key)
        # 向字典中添加购物车数量
        context.update(cart_count=cart_count)
        # 返回应答
        return render(request, 'index.html', context)


# def load_goods_data(request):
#     """上传商品数据"""
#
#     # 1.打开文件
#     # 2.读取数据
#     # 3.遇到图片的一项时调用上传到fastdfs的接口
#     # 4.接收fastdfs返回的id
#     # 5.存储到数据库中
#     pass


# /detail/goodsid/
class DetailView(View):
    """商品详情页面视图"""

    def get(self, request, goods_id):
        """获取商品详情页"""
        # 1.查询所有商品分类数据
        # print("商品id:%d" % goods_id)
        goods_type_list = GoodsType.objects.all()

        # 2.根据商品id查询商品
        try:
            goods = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist as res:
            # 输入的id对应的商品不存在时跳转到首页
            # print("这个id:%s不存在" % goods_id)
            return redirect(reverse('goods:index'))
        # 3.获取商品同一SPU的其他商品信息,排除商品自身
        goods_spu = goods.goods
        same_goods_list = GoodsSKU.objects.filter(goods=goods_spu).exclude(id=goods.id)
        # 4.获取新品信息
        goods_list = GoodsSKU.objects.filter(type=goods.type).exclude(id=goods.id).order_by('-create_time')[:2]
        # 5.获取商品评论信息
        goods_order_comments = OrderGoods.objects.filter(sku=goods).exclude(comment="")
        # 获取用户购物车商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)
            # 添加用户商品浏览历史记录
            history_key = "history_%d" % user.id
            # 删除redis对应用户list中已经存在过的商品的记录
            conn.lrem(history_key, 0, goods_id)
            # 在list左侧添加本次浏览记录
            conn.lpush(history_key, goods.id)
        context = {
            "goods_type_list": goods_type_list,  # 商品分类列表
            "goods": goods,  # 商品本身的引用
            "same_goods_list": same_goods_list,  # 同一SPU的其他商品规格
            "goods_list": goods_list,  # 新品信息
            "goods_order_comments": goods_order_comments,  # 订单评论信息
            "cart_count": cart_count  # 用户购物车中数量
        }
        return render(request, 'detail.html', context)


# /list/type_id/page?sort=default
class ListView(View):
    """列表页视图"""

    def get(self, request, type_id, page_index):
        """获取列表页面"""
        # 1. 获取url中排序方式
        sort = request.GET.get('sort')
        # 2. 查询所有商品分类
        goods_type_list = GoodsType.objects.all()
        # 3.查询指定的type_id是否存在
        try:
            type = GoodsType.objects.get(id=type_id)
        except Exception as res:
            # 指定的type_id不存在,返回到首页
            return redirect(reverse('goods:index'))
        # 根据type_id查询商品,按照指定顺序排序
        if sort == "price":
            goods_list = GoodsSKU.objects.filter(type=type).order_by('price')  # 价格排序默认从低到高
        elif sort == "sale":
            goods_list = GoodsSKU.objects.filter(type=type).order_by('-sales')  # 人气排序默认销量从大到小排序
        else:
            sort = "default"
            goods_list = GoodsSKU.objects.filter(type=type).order_by('-id')  # 默认排序按照id倒序排序

        # 获取新品信息
        new_goods_list = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]
        # 商品信息分页
        per_page = 1
        # 构建分页对象
        p = Paginator(goods_list, per_page)
        # 判断传递的页数与总页数的关系
        if page_index > p.num_pages:
            # 传递的页码大于总页数,显示最后一页
            page_index = p.num_pages
        elif page_index < 1:
            # 传递的页码小于1,显示第一页
            page_index = 1
        # 获取指定页码数量的商品
        page_goods_list = p.page(page_index)
        if p.num_pages < 5:
            # 总页数小于5页
            pages = range(1, p.num_pages+1)
        else:
            if page_goods_list.number <= 3:
                # 当前页是前三页,显示一到五页
                pages = range(1, 6)
            elif page_goods_list.number >= p.num_pages - 2:
                # 当前页是后三页,显示后五页
                pages = range(p.num_pages - 4, p.num_pages + 1)
            else:
                # 其他情况
                pages = range(page_goods_list.number - 2, page_goods_list.number + 3)
        # 获取用户购物车商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)
        context = {
            "goods_type_list": goods_type_list,  # 商品分类信息
            "page_goods_list": page_goods_list,  # 对应页数的商品列表信息
            "cart_count": cart_count,  # 用户购物车中商品数目
            "new_goods_list": new_goods_list,  # 新品推荐列表
            "type": type,  # 当前商品分类
            "sort": sort,  # 当前传递过来的排序方式
            "pages": pages
        }
        return render(request, 'list.html', context)