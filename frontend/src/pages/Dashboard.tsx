import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Progress } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, AlertOutlined, BankOutlined, SwapOutlined } from '@ant-design/icons'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { dashboardService, alertService, riskIndicatorService } from '../services/api'

interface DashboardData {
  total_portfolios: number
  active_portfolios: number
  today_trades: number
  today_amount: number
  pending_alerts: number
  critical_alerts: number
  total_return: number
  avg_sharpe_ratio: number
}

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null)
  const [alerts, setAlerts] = useState([])
  const [indicators, setIndicators] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    try {
      const [dashboardData, alertData, indicatorData] = await Promise.all([
        dashboardService.getData(),
        alertService.getPending(),
        riskIndicatorService.getLatest()
      ])
      setData(dashboardData)
      setAlerts(alertData.results || alertData.slice(0, 5))
      setIndicators(indicatorData.slice(0, 10))
    } catch (error) {
      console.error('获取仪表盘数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const alertColumns = [
    { title: '预警标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '组合', dataIndex: ['portfolio', 'code'], key: 'portfolio' },
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
        return <Tag color={colors[severity] || 'default'}>{severity}</Tag>
      }
    },
    { title: '时间', dataIndex: 'alert_time', key: 'alert_time', render: (time: string) => new Date(time).toLocaleString() }
  ]

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="组合总数"
              value={data?.total_portfolios || 0}
              prefix={<BankOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日交易"
              value={data?.today_trades || 0}
              prefix={<SwapOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待处理预警"
              value={data?.pending_alerts || 0}
              prefix={<AlertOutlined />}
              valueStyle={{ color: data?.pending_alerts ? '#faad14' : undefined }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="严重预警"
              value={data?.critical_alerts || 0}
              valueStyle={{ color: data?.critical_alerts ? '#ff4d4f' : undefined }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="最新风险指标" loading={loading}>
            <Table
              size="small"
              pagination={false}
              columns={[
                { title: '组合', dataIndex: ['portfolio', 'name'], key: 'portfolio' },
                { title: '日收益', dataIndex: 'daily_return', key: 'daily_return', render: (v: number) => `${(v * 100).toFixed(2)}%` },
                { title: '夏普比率', dataIndex: 'sharpe_ratio', key: 'sharpe_ratio' },
                { 
                  title: '最大回撤', 
                  dataIndex: 'max_drawdown', 
                  key: 'max_drawdown',
                  render: (v: number) => <span style={{ color: v < -0.05 ? '#ff4d4f' : undefined }}>{(v * 100).toFixed(2)}%</span>
                },
              ]}
              dataSource={indicators}
              rowKey="id"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="待处理预警" loading={loading}>
            <Table
              size="small"
              pagination={false}
              columns={alertColumns}
              dataSource={alerts}
              rowKey="id"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="收益概览">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="累计收益"
                  value={data?.total_return || 0}
                  precision={2}
                  valueStyle={{ color: (data?.total_return || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                  prefix={(data?.total_return || 0) >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  suffix="%"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="平均夏普比率"
                  value={data?.avg_sharpe_ratio || 0}
                  precision={2}
                />
              </Col>
              <Col span={8}>
                <Progress
                  percent={Math.min(((data?.pending_alerts || 0) / 10) * 100, 100)}
                  status="active"
                  format={() => '预警处理进度'}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
