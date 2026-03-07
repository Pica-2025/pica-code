import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card, Select, Image, Tag, Statistic, Row, Col,
  Space, Button, message, Spin, Divider, Alert, Rate, Typography,
  Progress, Badge, Tooltip, Layout, Checkbox, InputNumber
} from 'antd'
import {
  ArrowLeftOutlined, StarOutlined, ClockCircleOutlined,
  CheckCircleOutlined, SyncOutlined, SaveOutlined,
  EyeOutlined, FireOutlined, ThunderboltOutlined, RobotOutlined,
  UserOutlined, PictureOutlined, HomeOutlined, BarChartOutlined,
  EditOutlined
} from '@ant-design/icons'
import {
  getAdminUsersWithSessions,
  getAdminSessionTasks,
  getAdminTaskAllVersions,
  getAdminDetailedStats,
  updateAdminDifficulty
} from '../services/api'

const { Option } = Select
const { Title, Text, Paragraph } = Typography
const { Sider, Content } = Layout

export default function AdminDataViewer() {
  const navigate = useNavigate()

  const [stats, setStats] = useState(null)

  const [users, setUsers] = useState([])
  const [selectedUserId, setSelectedUserId] = useState(null)

  const [sessions, setSessions] = useState([])
  const [selectedSessionId, setSelectedSessionId] = useState(null)

  const [tasks, setTasks] = useState([])
  const [selectedTaskId, setSelectedTaskId] = useState(null)

  const [versions, setVersions] = useState([])
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [taskInfo, setTaskInfo] = useState(null)

  const [sessionStats, setSessionStats] = useState(null)

  const [selectedSessionIds, setSelectedSessionIds] = useState([])
  const [multiSessionStats, setMultiSessionStats] = useState(null)

  const [editingAdminDifficulty, setEditingAdminDifficulty] = useState(null)
  const [savingDifficulty, setSavingDifficulty] = useState(false)

  const [loading, setLoading] = useState(false)
  const [loadingVersions, setLoadingVersions] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      const [usersRes, statsRes] = await Promise.all([
        getAdminUsersWithSessions(),
        getAdminDetailedStats()
      ])

      setUsers(usersRes.data.users)
      setStats(statsRes.data)
    } catch (error) {
      message.error('加载数据失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleUserSelect = (userId) => {
    setSelectedUserId(userId)
    const user = users.find(u => u.user_id === userId)
    if (user) {
      setSessions(user.sessions)
      setSelectedSessionId(null)
      setTasks([])
      setSelectedTaskId(null)
      setVersions([])
      setSelectedVersion(null)
      setTaskInfo(null)
      setSessionStats(null)
      setSelectedSessionIds([])
      setMultiSessionStats(null)
    }
  }

  const handleSessionSelect = async (sessionId) => {
    setSelectedSessionId(sessionId)
    setLoading(true)

    try {
      const res = await getAdminSessionTasks(sessionId)
      setTasks(res.data.tasks)

      calculateSessionStats(res.data.tasks)

      setSelectedTaskId(null)
      setVersions([])
      setSelectedVersion(null)
      setTaskInfo(null)
    } catch (error) {
      message.error('加载任务失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const calculateSessionStats = (tasks) => {
    if (!tasks || tasks.length === 0) {
      setSessionStats(null)
      return
    }

    let totalPromptLength = 0
    let totalPromptTime = 0
    let totalAiScore = 0
    let totalManualScore = 0
    let countPromptLength = 0
    let countPromptTime = 0
    let countAiScore = 0
    let countManualScore = 0

    tasks.forEach(task => {
      const latestVersion = task.latest_version
      if (latestVersion) {

        if (latestVersion.prompt) {
          totalPromptLength += latestVersion.prompt.length
          countPromptLength++
        }

        if (latestVersion.prompt_time_seconds) {
          totalPromptTime += latestVersion.prompt_time_seconds
          countPromptTime++
        }

        if (latestVersion.ai_similarity_score !== null && latestVersion.ai_similarity_score !== undefined) {
          totalAiScore += latestVersion.ai_similarity_score * 100
          countAiScore++
        }

        if (latestVersion.user_manual_score) {
          totalManualScore += latestVersion.user_manual_score
          countManualScore++
        }
      }
    })

    setSessionStats({
      avgPromptLength: countPromptLength > 0 ? (totalPromptLength / countPromptLength).toFixed(1) : 0,
      avgPromptTime: countPromptTime > 0 ? (totalPromptTime / countPromptTime).toFixed(1) : 0,
      avgAiScore: countAiScore > 0 ? (totalAiScore / countAiScore).toFixed(1) : 0,
      avgManualScore: countManualScore > 0 ? (totalManualScore / countManualScore).toFixed(1) : 0,
      taskCount: tasks.length,
      versionCount: countPromptLength
    })
  }

  const handleMultiSessionSelect = (sessionIds) => {
    setSelectedSessionIds(sessionIds)
    if (sessionIds.length === 0) {
      setMultiSessionStats(null)
      return
    }

    calculateMultiSessionStats(sessionIds)
  }

  const calculateMultiSessionStats = async (sessionIds) => {
    try {

      const allTasks = []
      for (const sessionId of sessionIds) {
        const res = await getAdminSessionTasks(sessionId)
        allTasks.push(...res.data.tasks)
      }

      let totalPromptLength = 0
      let totalPromptTime = 0
      let totalAiScore = 0
      let totalManualScore = 0
      let countPromptLength = 0
      let countPromptTime = 0
      let countAiScore = 0
      let countManualScore = 0

      allTasks.forEach(task => {
        const latestVersion = task.latest_version
        if (latestVersion) {
          if (latestVersion.prompt) {
            totalPromptLength += latestVersion.prompt.length
            countPromptLength++
          }

          if (latestVersion.prompt_time_seconds) {
            totalPromptTime += latestVersion.prompt_time_seconds
            countPromptTime++
          }

          if (latestVersion.ai_similarity_score !== null && latestVersion.ai_similarity_score !== undefined) {
            totalAiScore += latestVersion.ai_similarity_score * 100
            countAiScore++
          }

          if (latestVersion.user_manual_score) {
            totalManualScore += latestVersion.user_manual_score
            countManualScore++
          }
        }
      })

      setMultiSessionStats({
        avgPromptLength: countPromptLength > 0 ? (totalPromptLength / countPromptLength).toFixed(1) : 0,
        avgPromptTime: countPromptTime > 0 ? (totalPromptTime / countPromptTime).toFixed(1) : 0,
        avgAiScore: countAiScore > 0 ? (totalAiScore / countAiScore).toFixed(1) : 0,
        avgManualScore: countManualScore > 0 ? (totalManualScore / countManualScore).toFixed(1) : 0,
        sessionCount: sessionIds.length,
        taskCount: allTasks.length,
        versionCount: countPromptLength
      })
    } catch (error) {
      message.error('计算统计失败: ' + error.message)
    }
  }

  const handleTaskSelect = async (taskId) => {
    setSelectedTaskId(taskId)
    setLoadingVersions(true)

    try {
      const res = await getAdminTaskAllVersions(taskId)
      setTaskInfo({
        task_id: res.data.task_id,
        round_number: res.data.round_number,
        target_image_url: res.data.target_image_url,
        ground_truth: res.data.ground_truth,
        difficulty: res.data.difficulty,
        user_difficulty_rating: res.data.user_difficulty_rating,
        admin_difficulty_rating: res.data.admin_difficulty_rating,
        status: res.data.status,
        model_type: res.data.model_type
      })
      setVersions(res.data.versions)

      if (res.data.versions.length > 0) {
        setSelectedVersion(res.data.versions[res.data.versions.length - 1])
        setEditingAdminDifficulty(res.data.admin_difficulty_rating || 5)
      }
    } catch (error) {
      message.error('加载版本失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoadingVersions(false)
    }
  }

  const handleVersionSelect = (version) => {
    setSelectedVersion(version)
  }

  const handleSaveAdminDifficulty = async () => {
    if (!taskInfo || editingAdminDifficulty === null) {
      message.warning('请设置管理员难度评级')
      return
    }

    if (editingAdminDifficulty < 1 || editingAdminDifficulty > 10) {
      message.error('难度评级必须在 1-10 之间')
      return
    }

    setSavingDifficulty(true)
    try {
      await updateAdminDifficulty(taskInfo.task_id, editingAdminDifficulty)

      setTaskInfo({
        ...taskInfo,
        admin_difficulty_rating: editingAdminDifficulty
      })

      message.success(`管理员难度评级已更新为: ${editingAdminDifficulty}`)
    } catch (error) {
      message.error('保存失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSavingDifficulty(false)
    }
  }

  const handleBackToGallery = () => {
    setSelectedTaskId(null)
    setSelectedVersion(null)
    setVersions([])
    setTaskInfo(null)
  }

  const renderStatistics = () => {
    if (!stats) return null

    return (
      <Card
        size="small"
        title={
          <Space>
            <FireOutlined style={{ color: '#ff4d4f' }} />
            <span>系统统计</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[8, 8]}>
          <Col span={12}>
            <Statistic
              title="用户"
              value={stats.users.total}
              prefix={<UserOutlined />}
              valueStyle={{ fontSize: 20 }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="Session"
              value={stats.sessions.total}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ fontSize: 20 }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="任务"
              value={stats.tasks.total}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ fontSize: 20 }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="版本"
              value={stats.versions.total}
              prefix={<PictureOutlined />}
              valueStyle={{ fontSize: 20 }}
            />
          </Col>
        </Row>
      </Card>
    )
  }

  const renderLeftSidebar = () => {
    const selectedUser = users.find(u => u.user_id === selectedUserId)
    const selectedSession = sessions.find(s => s.session_id === selectedSessionId)

    return (
      <div style={{ padding: 16 }}>
        {}
        <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Button
            block
            onClick={() => navigate('/admin')}
            icon={<ArrowLeftOutlined />}
          >
            返回控制台
          </Button>
          <Button
            block
            type="primary"
            onClick={loadInitialData}
            icon={<SyncOutlined />}
          >
            刷新数据
          </Button>
        </Space>

        {}
        {renderStatistics()}

        {}
        <Card
          size="small"
          title="选择用户"
          style={{ marginBottom: 16 }}
        >
          <Select
            showSearch
            style={{ width: '100%' }}
            placeholder="请选择用户"
            value={selectedUserId}
            onChange={handleUserSelect}
            dropdownStyle={{ maxHeight: 400 }}
            listHeight={300}
            filterOption={(input, option) =>
              option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          >
            {users.map(user => (
              <Option key={user.user_id} value={user.user_id}>
                {user.user_id}
              </Option>
            ))}
          </Select>

          {selectedUser && (
            <div style={{ marginTop: 12 }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">Sessions:</Text>
                  <Tag color="blue">{selectedUser.sessions.length}</Tag>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">已完成:</Text>
                  <Tag color="green">
                    {selectedUser.sessions.filter(s => s.status === 'finished').length}
                  </Tag>
                </div>
              </Space>
            </div>
          )}
        </Card>

        {}
        {selectedUserId && (
          <Card
            size="small"
            title="选择Session（单选）"
            style={{ marginBottom: 16 }}
          >
            <Select
              showSearch
              style={{ width: '100%' }}
              placeholder="请选择Session"
              value={selectedSessionId}
              onChange={handleSessionSelect}
              dropdownStyle={{ maxHeight: 400 }}
              listHeight={300}
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {sessions.map(session => (
                <Option key={session.session_id} value={session.session_id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>{session.session_id.slice(0, 8)}...</span>
                    <Tag
                      color={session.status === 'finished' ? 'green' : 'orange'}
                      style={{ marginLeft: 8 }}
                    >
                      {session.status}
                    </Tag>
                  </div>
                </Option>
              ))}
            </Select>

            {selectedSession && (
              <div style={{ marginTop: 12 }}>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">状态:</Text>
                    <Tag color={selectedSession.status === 'finished' ? 'green' : 'orange'}>
                      {selectedSession.status}
                    </Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">开始:</Text>
                    <Text style={{ fontSize: 12 }}>
                      {new Date(selectedSession.started_at).toLocaleString('zh-CN', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </Text>
                  </div>
                </Space>
              </div>
            )}
          </Card>
        )}

        {}
        {selectedUserId && sessions.length > 0 && (
          <Card
            size="small"
            title={
              <Space>
                <BarChartOutlined style={{ color: '#1890ff' }} />
                <span>多选Session统计</span>
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="选择多个Session计算统计"
              value={selectedSessionIds}
              onChange={handleMultiSessionSelect}
              maxTagCount={2}
              dropdownStyle={{ maxHeight: 400 }}
              listHeight={300}
            >
              {sessions.map(session => (
                <Option key={session.session_id} value={session.session_id}>
                  {session.session_id.slice(0, 8)}... ({session.status})
                </Option>
              ))}
            </Select>

            {multiSessionStats && (
              <div style={{ marginTop: 12 }}>
                <Divider style={{ margin: '12px 0' }} />
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text strong style={{ fontSize: 13 }}>多Session统计:</Text>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>Session数:</Text>
                    <Text strong>{multiSessionStats.sessionCount}</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>任务总数:</Text>
                    <Text strong>{multiSessionStats.taskCount}</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>平均Prompt长度:</Text>
                    <Text strong style={{ color: '#1890ff' }}>{multiSessionStats.avgPromptLength}字</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>平均Prompt时长:</Text>
                    <Text strong style={{ color: '#52c41a' }}>{multiSessionStats.avgPromptTime}秒</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>平均AI评分:</Text>
                    <Text strong style={{ color: '#722ed1' }}>{multiSessionStats.avgAiScore}分</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>平均人工评分:</Text>
                    <Text strong style={{ color: '#fa8c16' }}>{multiSessionStats.avgManualScore}分</Text>
                  </div>
                </Space>
              </div>
            )}
          </Card>
        )}
      </div>
    )
  }

  const renderTasksGallery = () => {
    if (!selectedSessionId || tasks.length === 0) {
      return (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <Text type="secondary">请先选择用户和Session</Text>
        </div>
      )
    }

    return (
      <div style={{ padding: 20 }}>
        {}
        {sessionStats && (
          <Card
            size="small"
            style={{ marginBottom: 20 }}
            title={
              <Space>
                <BarChartOutlined style={{ color: '#1890ff' }} />
                <span>Session统计</span>
              </Space>
            }
          >
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="任务数"
                  value={sessionStats.taskCount}
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="平均Prompt长度"
                  value={sessionStats.avgPromptLength}
                  suffix="字"
                  valueStyle={{ fontSize: 20, color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="平均Prompt时长"
                  value={sessionStats.avgPromptTime}
                  suffix="秒"
                  valueStyle={{ fontSize: 20, color: '#52c41a' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="平均AI评分"
                  value={sessionStats.avgAiScore}
                  suffix="分"
                  valueStyle={{ fontSize: 20, color: '#722ed1' }}
                />
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={6}>
                <Statistic
                  title="平均人工评分"
                  value={sessionStats.avgManualScore}
                  suffix="分"
                  valueStyle={{ fontSize: 20, color: '#fa8c16' }}
                />
              </Col>
            </Row>
          </Card>
        )}

        <Title level={4}>
          任务列表 ({tasks.length})
        </Title>

        <Row gutter={[16, 16]}>
          {tasks.map((task) => {
            const latestVersion = task.latest_version
            const displayImageUrl = latestVersion?.image_url || task.target_image_url

            return (
              <Col xs={24} sm={12} md={8} lg={6} key={task.task_id}>
                <Card
                  hoverable
                  size="small"
                  onClick={() => handleTaskSelect(task.task_id)}
                  style={{
                    border: selectedTaskId === task.task_id ? '2px solid #1890ff' : '1px solid #d9d9d9',
                    cursor: 'pointer'
                  }}
                  cover={
                    <div style={{ position: 'relative' }}>
                      <Image
                        src={displayImageUrl}
                        alt={task.target_filename}
                        style={{
                          width: '100%',
                          height: 200,
                          objectFit: 'cover'
                        }}
                        preview={false}
                      />
                      <div style={{
                        position: 'absolute',
                        top: 8,
                        left: 8,
                        background: 'rgba(0,0,0,0.6)',
                        padding: '4px 8px',
                        borderRadius: 4
                      }}>
                        <Text strong style={{ color: 'white' }}>
                          Round {task.round_number}
                        </Text>
                      </div>
                      {latestVersion && (
                        <div style={{
                          position: 'absolute',
                          top: 8,
                          right: 8,
                          background: 'rgba(24,144,255,0.9)',
                          padding: '4px 8px',
                          borderRadius: 4
                        }}>
                          <Text strong style={{ color: 'white', fontSize: 12 }}>
                            V{latestVersion.version_number}
                          </Text>
                        </div>
                      )}
                    </div>
                  }
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    {}
                    <div>
                      <Tag color={
                        task.status === 'completed' ? 'green' :
                        task.status === 'processing' ? 'orange' :
                        task.status === 'failed' ? 'red' : 'default'
                      }>
                        {task.status}
                      </Tag>
                      <Tag color={task.model_type === 'qwen' ? 'blue' : 'cyan'}>
                        {task.model_type}
                      </Tag>
                    </div>

                    {}
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>难度: </Text>
                      <Tag color={
                        task.difficulty === 'easy' ? 'green' :
                        task.difficulty === 'medium' ? 'orange' :
                        task.difficulty === 'hard' ? 'red' : 'default'
                      }>
                        {task.difficulty === 'easy' ? '简单' :
                         task.difficulty === 'medium' ? '中等' :
                         task.difficulty === 'hard' ? '困难' : task.difficulty}
                      </Tag>
                    </div>

                    {}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>版本:</Text>
                      <Badge
                        count={task.version_count || 0}
                        showZero
                        style={{ backgroundColor: task.version_count > 0 ? '#52c41a' : '#d9d9d9' }}
                      />
                    </div>

                    {}
                    {latestVersion && (
                      <>
                        {latestVersion.ai_similarity_score !== null && latestVersion.ai_similarity_score !== undefined && (
                          <div>
                            <Text type="secondary" style={{ fontSize: 12 }}>AI评分: </Text>
                            <Text strong style={{ color: '#722ed1' }}>
                              {(latestVersion.ai_similarity_score * 100).toFixed(1)}
                            </Text>
                          </div>
                        )}
                        {latestVersion.user_manual_score && (
                          <div>
                            <Text type="secondary" style={{ fontSize: 12 }}>人工评分: </Text>
                            <Text strong style={{ color: '#1890ff' }}>
                              {latestVersion.user_manual_score}
                            </Text>
                          </div>
                        )}
                      </>
                    )}

                    {}
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{ margin: 0, fontSize: 12 }}
                      type="secondary"
                    >
                      {task.ground_truth}
                    </Paragraph>
                  </Space>
                </Card>
              </Col>
            )
          })}
        </Row>
      </div>
    )
  }

  const renderVersionDetail = () => {
    if (!selectedVersion || !taskInfo) return null

    const rating = selectedVersion.rating

    const aiScores = {
      dino: selectedVersion.dino_score !== null && selectedVersion.dino_score !== undefined
        ? (selectedVersion.dino_score * 100).toFixed(1)
        : null,
      hsv: selectedVersion.hsv_score !== null && selectedVersion.hsv_score !== undefined
        ? (selectedVersion.hsv_score * 100).toFixed(1)
        : null,
      structure: selectedVersion.structure_score !== null && selectedVersion.structure_score !== undefined
        ? (selectedVersion.structure_score * 100).toFixed(1)
        : null,
      composite: selectedVersion.ai_similarity_score !== null && selectedVersion.ai_similarity_score !== undefined
        ? (selectedVersion.ai_similarity_score * 100).toFixed(1)
        : null
    }

    const promptLength = selectedVersion.prompt ? selectedVersion.prompt.length : 0
    const promptTime = selectedVersion.prompt_time_seconds || 0

    return (
      <div style={{ padding: 20 }}>
        {}
        <Button
          type="primary"
          icon={<HomeOutlined />}
          onClick={handleBackToGallery}
          style={{ marginBottom: 16 }}
        >
          返回画廊
        </Button>

        <Card
          title={
            <Space>
              <span>版本详情 - 版本 {selectedVersion.version_number}</span>
              {selectedVersion.is_final && <Tag color="green">最终版本</Tag>}
            </Space>
          }
        >
          {}
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card size="small" title="目标图片" hoverable>
                <Image
                  src={taskInfo.target_image_url}
                  alt="Target"
                  style={{ width: '100%', borderRadius: 8 }}
                />
                <Divider style={{ margin: '12px 0' }} />
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Paragraph
                    ellipsis={{ rows: 3, expandable: true }}
                    style={{ margin: 0 }}
                  >
                    <Text strong>Ground Truth: </Text>
                    {taskInfo.ground_truth}
                  </Paragraph>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">用户难度:</Text>
                    <Tag color={
                      taskInfo.user_difficulty_rating === 'easy' ? 'green' :
                      taskInfo.user_difficulty_rating === 'medium' ? 'orange' : 'red'
                    }>
                      {taskInfo.user_difficulty_rating === 'easy' ? '简单' :
                       taskInfo.user_difficulty_rating === 'medium' ? '中等' : '困难'}
                    </Tag>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">模型:</Text>
                    <Tag color={taskInfo.model_type === 'qwen' ? 'blue' : 'cyan'}>
                      {taskInfo.model_type}
                    </Tag>
                  </div>
                </Space>
              </Card>
            </Col>

            <Col xs={24} md={12}>
              <Card size="small" title="生成图片" hoverable>
                <Image
                  src={selectedVersion.image_url}
                  alt="Generated"
                  style={{ width: '100%', borderRadius: 8 }}
                />
                <Divider style={{ margin: '12px 0' }} />
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Paragraph
                    ellipsis={{ rows: 3, expandable: true }}
                    style={{ margin: 0 }}
                  >
                    <Text strong>Prompt: </Text>
                    {selectedVersion.prompt}
                  </Paragraph>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">Prompt长度:</Text>
                    <Text strong style={{ color: '#1890ff' }}>{promptLength}字</Text>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">Prompt时长:</Text>
                    <Text strong style={{ color: '#52c41a' }}>{promptTime}秒</Text>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">生成类型:</Text>
                    <Tag color={selectedVersion.generation_type === 'initial' ? 'blue' : 'purple'}>
                      {selectedVersion.generation_type === 'initial' ? '初始生成' : '修改生成'}
                    </Tag>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">模型:</Text>
                    <Tag color={selectedVersion.model_type === 'qwen' ? 'blue' : 'cyan'}>
                      {selectedVersion.model_type}
                    </Tag>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">创建时间:</Text>
                    <Text style={{ fontSize: 12 }}>
                      {new Date(selectedVersion.created_at).toLocaleString('zh-CN')}
                    </Text>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>

          {}
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} md={12}>
              <Card
                size="small"
                title={
                  <Space>
                    <RobotOutlined style={{ color: '#1890ff' }} />
                    <span>AI评分（只读）</span>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {}
                  {(aiScores.dino || aiScores.hsv || aiScores.structure) && (
                    <>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <Text strong style={{ color: '#1890ff' }}>DINO相似度:</Text>
                          <Text strong style={{ fontSize: 16 }}>{aiScores.dino}分</Text>
                        </div>
                        <Progress
                          percent={parseFloat(aiScores.dino)}
                          strokeColor="#1890ff"
                          showInfo={false}
                        />
                      </div>

                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <Text strong style={{ color: '#52c41a' }}>HSV色彩:</Text>
                          <Text strong style={{ fontSize: 16 }}>{aiScores.hsv}分</Text>
                        </div>
                        <Progress
                          percent={parseFloat(aiScores.hsv)}
                          strokeColor="#52c41a"
                          showInfo={false}
                        />
                      </div>

                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <Text strong style={{ color: '#faad14' }}>结构相似度:</Text>
                          <Text strong style={{ fontSize: 16 }}>{aiScores.structure}分</Text>
                        </div>
                        <Progress
                          percent={parseFloat(aiScores.structure)}
                          strokeColor="#faad14"
                          showInfo={false}
                        />
                      </div>

                      <Divider style={{ margin: '12px 0' }} />
                    </>
                  )}

                  {}
                  {aiScores.composite && (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                        <Text strong style={{ fontSize: 15, color: '#722ed1' }}>
                          <StarOutlined /> AI综合评分:
                        </Text>
                        <Text strong style={{ fontSize: 18, color: '#722ed1' }}>
                          {aiScores.composite}分
                        </Text>
                      </div>
                      <Progress
                        percent={parseFloat(aiScores.composite)}
                        strokeColor="#722ed1"
                        strokeWidth={12}
                      />
                    </div>
                  )}
                </Space>
              </Card>
            </Col>

            <Col xs={24} md={12}>
              <Card
                size="small"
                title={
                  <Space>
                    <UserOutlined style={{ color: '#52c41a' }} />
                    <span>用户评分（只读）</span>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <div>
                    <Text strong>相似度评分: </Text>
                    <Text style={{ fontSize: 18, color: '#1890ff' }}>
                      {selectedVersion.user_manual_score || '未评分'}
                    </Text>
                    <Text type="secondary"> / 100</Text>
                  </div>

                  {selectedVersion.user_manual_score && (
                    <Progress
                      percent={selectedVersion.user_manual_score}
                      strokeColor="#1890ff"
                      strokeWidth={12}
                    />
                  )}
                </Space>
              </Card>
            </Col>
          </Row>

          {}
          <Card
            size="small"
            title={
              <Space>
                <EditOutlined style={{ color: '#fa8c16' }} />
                <span>管理员难度评级（可编辑）</span>
              </Space>
            }
            style={{ marginTop: 16 }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>当前评级: </Text>
                <Text style={{ fontSize: 18, color: '#fa8c16' }}>
                  {taskInfo.admin_difficulty_rating || '未评级'}
                </Text>
                <Text type="secondary"> / 10</Text>
              </div>

              <div>
                <Text strong>设置新评级 (1-10): </Text>
                <div style={{ marginTop: 8 }}>
                  <InputNumber
                    min={1}
                    max={10}
                    value={editingAdminDifficulty}
                    onChange={setEditingAdminDifficulty}
                    style={{ width: 120, marginRight: 12 }}
                  />
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    loading={savingDifficulty}
                    onClick={handleSaveAdminDifficulty}
                  >
                    保存
                  </Button>
                </div>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                  提示：1=非常简单，10=非常困难
                </Text>
              </div>
            </Space>
          </Card>

          {}
          {rating && (
            <Card
              size="small"
              title={
                <Space>
                  <StarOutlined style={{ color: '#faad14' }} />
                  <span>用户星级评分（只读）</span>
                </Space>
              }
              style={{ marginTop: 16 }}
            >
              <Row gutter={16}>
                <Col xs={24} md={14}>
                  <Space direction="vertical" style={{ width: '100%' }} size="small">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong style={{ width: 100 }}>画风风格:</Text>
                      <Rate disabled value={rating.style_score} count={7} />
                      <Text strong style={{ color: '#1890ff', width: 50, textAlign: 'right' }}>
                        {rating.style_score}/7
                      </Text>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong style={{ width: 100 }}>物件数量:</Text>
                      <Rate disabled value={rating.object_count_score} count={7} />
                      <Text strong style={{ color: '#52c41a', width: 50, textAlign: 'right' }}>
                        {rating.object_count_score}/7
                      </Text>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong style={{ width: 100 }}>角度方位:</Text>
                      <Rate disabled value={rating.perspective_score} count={7} />
                      <Text strong style={{ color: '#722ed1', width: 50, textAlign: 'right' }}>
                        {rating.perspective_score}/7
                      </Text>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong style={{ width: 100 }}>景深背景:</Text>
                      <Rate disabled value={rating.depth_background_score} count={7} />
                      <Text strong style={{ color: '#fa8c16', width: 50, textAlign: 'right' }}>
                        {rating.depth_background_score}/7
                      </Text>
                    </div>

                    <Divider style={{ margin: '12px 0' }} />

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong style={{ fontSize: 15, width: 100 }}>平均分:</Text>
                      <Rate disabled value={rating.average_score} allowHalf />
                      <Text strong style={{ fontSize: 16, color: '#fa541c', width: 50, textAlign: 'right' }}>
                        {rating.average_score.toFixed(2)}/7
                      </Text>
                    </div>
                  </Space>
                </Col>

                <Col xs={24} md={10}>
                  <div>
                    <Text strong>详细评价:</Text>
                    <Card
                      size="small"
                      style={{
                        marginTop: 8,
                        background: '#f5f5f5'
                      }}
                    >
                      <Paragraph
                        style={{
                          margin: 0,
                          whiteSpace: 'pre-line',
                          fontSize: 13
                        }}
                      >
                        {rating.detailed_review || '无详细评价'}
                      </Paragraph>
                    </Card>
                  </div>
                </Col>
              </Row>
            </Card>
          )}
        </Card>

        {}
        {versions.length > 1 && (
          <Card
            title="其他版本"
            size="small"
            style={{ marginTop: 16 }}
          >
            <Row gutter={[12, 12]}>
              {versions.filter(v => v.version_id !== selectedVersion.version_id).map((version) => {
                const vAiScore = version.ai_similarity_score !== null && version.ai_similarity_score !== undefined
                  ? (version.ai_similarity_score * 100).toFixed(1)
                  : null

                return (
                  <Col xs={12} sm={8} md={6} key={version.version_id}>
                    <Card
                      hoverable
                      size="small"
                      onClick={() => handleVersionSelect(version)}
                      cover={
                        <Image
                          src={version.image_url}
                          alt={`version ${version.version_number}`}
                          style={{
                            width: '100%',
                            height: 150,
                            objectFit: 'cover'
                          }}
                          preview={{
                            mask: <EyeOutlined />
                          }}
                        />
                      }
                    >
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <Badge count={version.version_number} style={{ backgroundColor: '#1890ff' }} />
                        {version.is_final && <Tag color="green" style={{ fontSize: 11 }}>最终</Tag>}

                        {}
                        {vAiScore && (
                          <div>
                            <Text type="secondary" style={{ fontSize: 11 }}>AI: </Text>
                            <Text strong style={{ fontSize: 11 }}>
                              {vAiScore}分
                            </Text>
                          </div>
                        )}

                        {}
                        {version.user_manual_score && (
                          <div>
                            <Text type="secondary" style={{ fontSize: 11 }}>用户: </Text>
                            <Text strong style={{ fontSize: 11 }}>
                              {version.user_manual_score}分
                            </Text>
                          </div>
                        )}

                        {}
                        {version.prompt && (
                          <div>
                            <Text type="secondary" style={{ fontSize: 11 }}>Prompt: </Text>
                            <Text strong style={{ fontSize: 11 }}>
                              {version.prompt.length}字
                            </Text>
                          </div>
                        )}
                      </Space>
                    </Card>
                  </Col>
                )
              })}
            </Row>
          </Card>
        )}
      </div>
    )
  }

  if (loading && !stats) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <Spin size="large" tip="加载数据中..." />
      </div>
    )
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {}
      <Sider
        width={280}
        style={{
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0
        }}
      >
        <div style={{ padding: '16px 0', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <Title level={4} style={{ margin: 0 }}>
            <StarOutlined style={{ color: '#1890ff' }} /> 管理员
          </Title>
        </div>
        {renderLeftSidebar()}
      </Sider>

      {}
      <Layout style={{ marginLeft: 280 }}>
        <Content style={{ background: '#f0f2f5', minHeight: '100vh' }}>
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center' }}>
              <Spin size="large" tip="加载中..." />
            </div>
          ) : selectedTaskId && selectedVersion ? (

            renderVersionDetail()
          ) : (

            renderTasksGallery()
          )}
        </Content>
      </Layout>
    </Layout>
  )
}
