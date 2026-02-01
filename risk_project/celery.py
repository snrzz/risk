import os
from celery import Celery

# 设置Django的默认 settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'risk_project.settings')

app = Celery('risk_project')

# 使用Django的settings文件配置Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有Django应用中的tasks
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
