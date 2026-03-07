import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Statistic, Row, Col, Table, message, Button, Space } from 'antd'
import { DatabaseOutlined, BarChartOutlined } from '@ant-design/icons'
import { getAdminStats, getAllUsers } from '../services/api'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statsRes, usersRes] = await Promise.all([
        getAdminStats(),
        getAllUsers()
      ])
      setStats(statsRes.data)
      setUsers(usersRes.data.users)
    } catch (error) {
      message.error('加载失败')
    }
  }

  const columns = [
    { title: '用户ID', dataIndex: 'user_id', key: 'user_id' },
    { title: '角色', dataIndex: 'role', key: 'role' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' }
  ]

  return (
    <div style={{ padding: '40px' }}>
      <div style={{ marginBottom: 30, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>管理员控制台</h1>
        <Space>
          <Button
            type="primary"
            size="large"
            icon={<DatabaseOutlined />}
            onClick={() => navigate('/admin/data')}
          >
            数据查看系统
          </Button>
        </Space>
      </div>

      {stats && (
        <Row gutter={16} style={{ marginBottom: 30 }}>
          <Col span={6}>
            <Card><Statistic title="总用户数" value={stats.total_users} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="总Session数" value={stats.total_sessions} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="活跃Session" value={stats.active_sessions} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="平均评分" value={stats.average_rating} precision={2} /></Card>
          </Col>
        </Row>
      )}

      <Card title="用户列表">
        <Table dataSource={users} columns={columns} rowKey="id" />
      </Card>
    </div>
  )
}
