import React, { useEffect, useState } from 'react'
import { Table, Card, Tag, Button, Modal, Input, Space, Row, Col, Statistic } from 'antd'
import { CheckOutlined, CloseOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { alertService } from '../services/api'

interface AlertData {
  id: number
  alert_type: string
  portfolio: { id: number; code: string; name: string } | null
  severity: string
  title: string
  content: string
  indicator_name: string
  indicator_value: number
  threshold: number
  status: string
  alert_time: string
  handled_by: { email: string } | null
  handled_at: string
  handle_comment: string
}

const Alert: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertData[]>([])
  const [statistics, setStatistics] = useState<Record<string, unknown>>({})
  const [loading, setLoading] = useState(true)
  const [commentModalVisible, setCommentModalVisible] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<AlertData | null>(null)
  const [comment, setComment] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [alertData, statsData] = await Promise.all([
        alertService.getAll(),
        alertService.getStatistics()
      ])
      setAlerts(alertData.results || alertData)
      setStatistics(statsData)
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (id: number, status: string) => {
    try {
      await alertService.updateStatus(id, status, comment)
      message.success('处理成功')
      setCommentModalVisible(false)
      setComment('')
      fetchData()
    } catch (error) {
      message.error('处理失败')
    }
  }

  const openCommentModal = (record: AlertData) => {
    setSelectedAlert(record)
    setCommentModalVisible(true)
  }

  const columns = [
    { title: '预警时间', dataIndex: 'alert_time', key: 'alert_time', render: (t: string) => new Date(t).toLocaleString() },
    { title: '预警标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { 
      title: '等级', 
      dataIndex: 'severity', 
      key: 'severity',
      render: (severity: string) => {
        const colors: Record<string, string> = {
          critical: 'red',
          error: 'orange',
          warning: 'gold',
          info: 'blue'
        }
        const texts: Record<string, string> = {
          critical: '严重',
          error: '错误',
          warning: '警告',
          info: '信息'
        }
        return <Tag color={colors[severity] || 'default'}>{texts[severity] || severity}</Tag>
      }
    },
    { title: '类型', dataIndex: 'alert_type', key: 'alert_type', render: (t: string) => {
      const types: Record<string, string> = {
        threshold: '阈值预警',
        anomaly: '异常预警',
        limit: '限制预警',
        trend: '趋势预警'
      }
      return types[t] || t
    }},
    { title: '组合', dataIndex: ['portfolio', 'code'], key: 'portfolio', render: (c: string, r: AlertData) => r.portfolio?.code || '-' },
    { title: '指标', dataIndex: 'indicator_name', key: 'indicator' },
    { 
      title: '值/阈值', 
      key: 'value',
      render: (_: unknown, r: AlertData) => `${r.indicator_value?.toFixed(4)} / ${r.threshold?.toFixed(4)}`
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => {
        const statuses: Record<string, { text: string; color: string }> = {
          pending: { text: '待处理', color: 'orange' },
          acknowledged: { text: '已确认', color: 'blue' },
          resolved: { text: '已解决', color: 'green' },
          ignored: { text: '已忽略', color: 'default' }
        }
        const config = statuses[status] || { text: status, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: AlertData) => (
        <Space>
          {record.status === 'pending' && (
            <>
              <Button type="primary" size="small" icon={<CheckOutlined />} onClick={() => openCommentModal(record)}>处理</Button>
              <Button size="small" icon={<CloseOutlined />} onClick={() => handleStatusChange(record.id, 'ignored')}>忽略</Button>
            </>
          )}
          {record.status === 'acknowledged' && (
            <Button type="primary" size="small" onClick={() => openCommentModal(record)}>解决</Button>
          )}
        </Space>
      )
    }
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="待处理" value={statistics['by_status']?.find((s: {status: string}) => s.status === 'pending')?.count || 0} valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="严重" value={statistics['by_severity']?.find((s: {severity: string}) => s.severity === 'critical')?.count || 0} valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已确认" value={statistics['by_status']?.find((s: {status: string}) => s.status === 'acknowledged')?.count || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已解决" value={statistics['by_status']?.find((s: {status: string}) => s.status === 'resolved')?.count || 0} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
      </Row>

      <Card title="风险预警">
        <Table
          loading={loading}
          columns={columns}
          dataSource={alerts}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="处理预警"
        open={commentModalVisible}
        onCancel={() => setCommentModalVisible(false)}
        onOk={() => selectedAlert && handleStatusChange(selectedAlert.id, 'resolved')}
      >
        <Input.TextArea
          rows={4}
          placeholder="请输入处理意见..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </Modal>
    </div>
  )
}

export default Alert
