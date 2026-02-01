import React, { useEffect, useState } from 'react'
import { Table, Card, Select, DatePicker, Tag, Space } from 'antd'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { riskIndicatorService, portfolioService } from '../services/api'
import dayjs from 'dayjs'

interface IndicatorData {
  id: number
  portfolio: { id: number; code: string; name: string }
  indicator_date: string
  daily_return: number
  cumulative_return: number
  annualized_return: number
  sharpe_ratio: number
  max_drawdown: number
  value_at_risk: number
}

const RiskIndicator: React.FC = () => {
  const [indicators, setIndicators] = useState<IndicatorData[]>([])
  const [history, setHistory] = useState([])
  const [portfolios, setPortfolios] = useState([])
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [indicatorData, portfolioData] = await Promise.all([
        riskIndicatorService.getLatest(),
        portfolioService.getAll()
      ])
      setIndicators(indicatorData)
      setPortfolios(portfolioData.results || portfolioData)
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchHistory = async (portfolioId: number) => {
    try {
      const data = await riskIndicatorService.getHistory(portfolioId)
      setHistory(data)
    } catch (error) {
      console.error('获取历史数据失败:', error)
    }
  }

  const handlePortfolioChange = (value: number) => {
    setSelectedPortfolio(value)
    if (value) {
      fetchHistory(value)
    }
  }

  const columns = [
    { title: '组合', dataIndex: ['portfolio', 'name'], key: 'portfolio' },
    { title: '日期', dataIndex: 'indicator_date', key: 'date' },
    { 
      title: '日收益', 
      dataIndex: 'daily_return', 
      key: 'daily_return',
      render: (v: number) => {
        const color = v >= 0 ? 'green' : 'red'
        return <Tag color={color}>{(v * 100).toFixed(2)}%</Tag>
      }
    },
    { title: '夏普比率', dataIndex: 'sharpe_ratio', key: 'sharpe_ratio' },
    { 
      title: '最大回撤', 
      dataIndex: 'max_drawdown', 
      key: 'max_drawdown',
      render: (v: number) => <span style={{ color: v < -0.05 ? '#ff4d4f' : undefined }}>{(v * 100).toFixed(2)}%</span>
    },
    { title: 'VaR(95%)', dataIndex: 'value_at_risk', key: 'var', render: (v: number) => `${(v * 100).toFixed(2)}%` },
  ]

  return (
    <div>
      <Card
        title="风险指标"
        extra={
          <Space>
            <span>选择组合：</span>
            <Select
              style={{ width: 200 }}
              placeholder="请选择组合"
              onChange={handlePortfolioChange}
              allowClear
            >
              {portfolios.map((p: { id: number; code: string; name: string }) => (
                <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
              ))}
            </Select>
          </Space>
        }
      >
        <Table
          loading={loading}
          columns={columns}
          dataSource={indicators}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {selectedPortfolio && history.length > 0 && (
        <Card title="收益走势" style={{ marginTop: 16 }}>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="indicator_date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="daily_return" name="日收益" stroke="#1890ff" />
              <Line yAxisId="right" type="monotone" dataKey="sharpe_ratio" name="夏普比率" stroke="#52c41a" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  )
}

export default RiskIndicator
