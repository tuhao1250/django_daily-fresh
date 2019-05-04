from django.contrib import admin
from goods.models import Goods, GoodsType, GoodsSKU, GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, \
    IndexPromotionBanner
from celery_tasks.tasks import generate_static_index
from django.core.cache import cache

# Register your models here.


class BaseAdmin(admin.ModelAdmin):
    """Admin站点模型管理器基类"""
    def save_model(self, request, obj, form, change):
        """当更新或创建模型时调用"""
        super().save_model(request, obj, form, change)
        # print("发出任务")
        # 在执行保存之后,执行发出任务更新静态首页内容
        generate_static_index.delay()
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """当删除模型时调用"""
        super().delete_model(request, obj)
        # 发出任务
        generate_static_index.delay()
        cache.delete('index_page_data')


class IndexTypeGoodsBannerAdmin(BaseAdmin):
    """首页分类商品模型管理器类"""
    list_per_page = 10
    list_display = ['id', 'typename', 'skuname', 'display_type', 'index']


class IndexPromotionBannerAdmin(BaseAdmin):
    """首页促销活动模型管理器类"""
    pass


# class GoodsAdmin(BaseAdmin):
#     """商品SPU模型管理器"""
#     pass


class GoodsTypeAdmin(BaseAdmin):
    """商品分类模型管理器类"""
    pass


class GoodsSKUAdmin(BaseAdmin):
    """商品SKU模型管理器类"""
    pass


# class GoodsImagAdmin(BaseAdmin):
#     """商品图片模型管理器类"""
#     pass


class IndexGoodsBannerAdmin(BaseAdmin):
    """首页轮播商品模型管理器类"""
    pass


# admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
# admin.site.register(GoodsImage, GoodsImagAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
