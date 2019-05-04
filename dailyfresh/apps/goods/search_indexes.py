from haystack import indexes
from goods.models import GoodsSKU


class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """商品SKU所以类"""
    # 索引字段 use_template=True表示从模板文件中指定需要建立索引的字段
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return GoodsSKU

    # 建立索引的数据,这个方法返回的是什么数据,就会对那些数据做索引
    def index_queryset(self, using=None):
        return self.get_model().objects.all()