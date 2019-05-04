from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):
    """FASTSFS文件存储类"""
    def __init__(self, client_conf=None, base_url=None):
        """初始化"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF_PATH
        self.client_conf = client_conf
        if base_url is None:
            base_url = settings.FDFS_SERVER_URL
        self.base_url = base_url

    def _open(self, name, mode="rb"):
        pass

    def _save(self, name, content):
        """
        保存文件时使用
        :param name:选择的要上传的文件的名称
        :param content:包含上传文件的内容的file对象
        :return:返回文件存储在fastdfs中的id
        """
        # 创建一个fdfs_client对象,需要指明fdfs_client配置文件
        client = Fdfs_client(self.client_conf)  # 注意文件路径需要相对于项目的根目录
        res = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception("上传文件到fastdfs失败")
        # 获取返回的文件id
        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        return False

    def url(self, name):
        """
        返回要访问的文件的url地址
        :param name: name参数就是上面函数的filename,也就是fastdfs返回的id
        :return: 返回的是url地址,需要点击就可以直接访问到
        """
        return self.base_url + name
