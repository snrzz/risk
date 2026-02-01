from rest_framework import views, status
from rest_framework.response import Response
from celery.result import AsyncResult
from celery import current_app
from .tasks import (
    sync_risk_indicators, check_risk_alerts,
    export_daily_report, cache_warmup, detect_abnormal_trades
)


class TaskListView(views.APIView):
    """任务列表"""
    
    def get(self, request):
        """获取所有定时任务"""
        tasks = [
            {
                'name': 'sync_risk_indicators',
                'description': '同步风险指标数据',
                'schedule': '每天 6:00',
                'enabled': True
            },
            {
                'name': 'check_risk_alerts',
                'description': '检查风险预警',
                'schedule': '每小时',
                'enabled': True
            },
            {
                'name': 'export_daily_report',
                'description': '导出日报',
                'schedule': '每天 18:00',
                'enabled': True
            },
            {
                'name': 'cache_warmup',
                'description': '缓存预热',
                'schedule': '每30分钟',
                'enabled': True
            },
            {
                'name': 'detect_abnormal_trades',
                'description': '检测异常交易',
                'schedule': '每天收盘后',
                'enabled': True
            }
        ]
        return Response(tasks)


class TaskExecuteView(views.APIView):
    """手动执行任务"""
    
    def post(self, request):
        task_name = request.data.get('task_name')
        
        if not task_name:
            return Response(
                {'error': '请指定任务名称'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task_map = {
            'sync_risk_indicators': sync_risk_indicators,
            'check_risk_alerts': check_risk_alerts,
            'export_daily_report': export_daily_report,
            'cache_warmup': cache_warmup,
            'detect_abnormal_trades': detect_abnormal_trades,
        }
        
        if task_name not in task_map:
            return Response(
                {'error': f'任务{task_name}不存在'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 异步执行任务
        task = task_map[task_name].delay()
        
        return Response({
            'message': f'任务{task_name}已开始执行',
            'task_id': task.id
        })


class TaskStatusView(views.APIView):
    """任务状态"""
    
    def get(self, request):
        task_id = request.query_params.get('task_id')
        
        if not task_id:
            return Response(
                {'error': '请指定任务ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = AsyncResult(task_id)
        
        return Response({
            'task_id': task_id,
            'status': result.status,
            'result': str(result.result) if result.result else None,
        })
