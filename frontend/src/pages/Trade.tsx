import React, { useEffect, useState } from 'react'
import { Table, Card, Tag, Button, Space, Select, DatePicker } from 'antd'
import { ExclamationCircleOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { tradeService, portfolioService } from '../services/api'

interface TradeData {
  id: number
  portfolio: { code: string }
  trade_type: string
  security_type: string
  security_code: string
  security_name: string
  trade_date: string
  quantity: number
  price: number
  amount: number
  status: string
  is_abnormal: boolean
  abnormal_reason: string
}

const Trade: React.FC = () => {
  const [trades, setTrades] = useState<TradeData[]>([])
  const [summary, setSummary] = useState<Record<string, number>>({})
  const [portfolios, setPortfolios] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [tradeData, summaryData, portfolioData] = await Promise.all([
        tradeService.getAll(),
        tradeService.getSummary(),
        portfolioService.getAll()
      ])
      setTrades(tradeData.results || tradeData)
      setSummary(summaryData)
      setPortfolios(portfolioData.results || portfolioData)
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '交易日期', dataIndex: 'trade_date', key: 'trade_date' },
    { title: '组合', dataIndex: ['portfolio', 'code'], key: 'portfolio' },
    { 
      title: '类型', 
      dataIndex: 'trade_type', 
      key: 'trade_type',
      render: (type: string) => (
        <Tag color={type === 'buy' ? 'green' : 'red'}>{type === 'buy' ? '买入' : '卖出'}</Tag>
      )
    },
    { title: '证券代码', dataIndex: 'security_code', key: 'security_code' },
    { title: '证券名称', dataIndex: 'security_name', key: 'security_name', ellipsis: true },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', render: (v: number) => v.toLocaleString() },
    { title: '价格', dataIndex: 'price', key: 'price' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => `¥${v.toLocaleString()}` },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          pending: { text: '待成交', color: 'orange' },
          partial: { text: '部分成交', color: 'gold' },
          filled: { text: '全部成交', color: 'green' },
          cancelled: { text: '已取消', color: 'red' },
        }
        const config = statusMap[status] || { text: status, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '异常',
      dataIndex: 'is_abnormal',
      key: 'is_abnormal',
      render: (isAbnormal: boolean) => isAbnormal ? (
        <Tag color="red" icon={<ExclamationCircleOutlined />}>异常</Tag>
      ) : (
        <Tag color="green" icon={<CheckCircleOutlined />}>正常</Tag>
      )
    },
  ]

  return (
    <div>
      <Card title="交易概览">
        <Space size="large">
          <div>总交易笔数：<b>{summary.total_count || 0}</b></div>
          <div>总成交金额：<b>¥{(summary.total_amount || 0).toLocaleString()}</b></div>
          <div>买入笔数：<b>{summary.buy_count || 0}</b></div>
          <div>卖出笔数：<b>{summary.sell_count || 0}</b></div>
          <div>异常交易：<b style={{ color: summary.abnormal_count ? '#ff4d4f' : undefined }}>{summary.abnormal_count || 0}</b></div>
        </Space>
      </Card>

      <Card title="交易记录" style={{ marginTop: 16 }}>
        <Table
          loading={loading}
          columns={columns}
          dataSource={trades}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default Trade
