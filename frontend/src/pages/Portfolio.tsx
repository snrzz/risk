import React, { useEffect, useState } from 'react'
import { Table, Card, Button, Modal, Form, Input, Select, message, Tag, Space } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { portfolioService } from '../services/api'

interface PortfolioData {
  id: number
  code: string
  name: string
  manager: string
  portfolio_type: string
  status: string
  asset_scale: number
}

const Portfolio: React.FC = () => {
  const [portfolios, setPortfolios] = useState<PortfolioData[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingPortfolio, setEditingPortfolio] = useState<PortfolioData | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchPortfolios()
  }, [])

  const fetchPortfolios = async () => {
    try {
      const response = await portfolioService.getAll()
      setPortfolios(response.results || response)
    } catch (error) {
      message.error('获取组合列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingPortfolio(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: PortfolioData) => {
    setEditingPortfolio(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleSubmit = async (values: Record<string, unknown>) => {
    try {
      if (editingPortfolio) {
        await portfolioService.update(editingPortfolio.id, values)
        message.success('更新成功')
      } else {
        await portfolioService.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchPortfolios()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个组合吗？',
      onOk: async () => {
        try {
          await portfolioService.delete(id)
          message.success('删除成功')
          fetchPortfolios()
        } catch (error) {
          message.error('删除失败')
        }
      }
    })
  }

  const columns = [
    { title: '组合代码', dataIndex: 'code', key: 'code' },
    { title: '组合名称', dataIndex: 'name', key: 'name' },
    { title: '投资经理', dataIndex: 'manager', key: 'manager' },
    { 
      title: '类型', 
      dataIndex: 'portfolio_type', 
      key: 'portfolio_type',
      render: (type: string) => {
        const typeMap: Record<string, { text: string; color: string }> = {
          stock: { text: '股票', color: 'blue' },
          bond: { text: '债券', color: 'green' },
          mixed: { text: '混合', color: 'orange' },
          index: { text: '指数', color: 'purple' },
        }
        const config = typeMap[type] || { text: type, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          active: 'green',
          suspended: 'orange',
          closed: 'red'
        }
        return <Tag color={colors[status] || 'default'}>{status}</Tag>
      }
    },
    { title: '资产规模', dataIndex: 'asset_scale', key: 'asset_scale', render: (v: number) => `¥${v.toLocaleString()}` },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: PortfolioData) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => handleEdit(record)}>查看</Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      )
    }
  ]

  return (
    <Card
      title="组合管理"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增组合</Button>}
    >
      <Table
        loading={loading}
        columns={columns}
        dataSource={portfolios}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingPortfolio ? '编辑组合' : '新增组合'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="code" label="组合代码" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="组合名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="manager" label="投资经理">
            <Input />
          </Form.Item>
          <Form.Item name="portfolio_type" label="组合类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="stock">股票组合</Select.Option>
              <Select.Option value="bond">债券组合</Select.Option>
              <Select.Option value="mixed">混合组合</Select.Option>
              <Select.Option value="index">指数组合</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="asset_scale" label="资产规模">
            <Input type="number" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>提交</Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default Portfolio
