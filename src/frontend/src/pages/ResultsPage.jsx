import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Row, Col, Spin, Button, message, Alert } from 'antd'
import { getSessionDetail, finishSession } from '../services/api'

export default function ResultsPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [tasks, setTasks] = useState([])

  useEffect(() => {
    loadSession()
    const interval = setInterval(loadSession, 5000)
    return () => clearInterval(interval)
  }, [sessionId])

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadSession()
      }
    }

    const handleFocus = () => {
      loadSession()
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('focus', handleFocus)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('focus', handleFocus)
    }
  }, [sessionId])

  const loadSession = async () => {
    try {
      const res = await getSessionDetail(sessionId)
      setTasks(res.data.tasks)
      setLoading(false)
    } catch (error) {
      message.error('加载失败')
      setLoading(false)
    }
  }

  const handleFinish = async () => {
    try {
      await finishSession(sessionId)
      message.success('测试完成！')
      navigate('/login')
    } catch (error) {
      message.error(error.response?.data?.detail || '完成失败')
    }
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh'
      }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, color: '#666' }}>加载任务列表...</div>
      </div>
    )
  }

  const completedCount = tasks.filter(t => t.status === 'completed').length
  const failedCount = tasks.filter(t => t.status === 'failed').length
  const processingCount = tasks.filter(t => t.status === 'processing').length
  const pendingCount = tasks.filter(t => t.status === 'pending').length

  const finalizedCount = tasks.filter(t => t.has_final_version === true).length

  const MIN_COMPLETED_REQUIRED = 8

  const canFinish = (
    pendingCount === 0 &&
    processingCount === 0 &&
    completedCount >= MIN_COMPLETED_REQUIRED &&
    finalizedCount >= completedCount
  )

  return (
    <div style={{ padding: '40px' }}>
      <Card title="生成结果画廊">
        {}
        <div style={{
          marginBottom: 24,
          padding: 16,
          background: '#f5f5f5',
          borderRadius: 8,
          textAlign: 'center'
        }}>
          {processingCount > 0 && (
            <span style={{ marginRight: 24, color: '#1890ff', fontWeight: 'bold' }}>
              ⏳ 生成中: {processingCount}
            </span>
          )}
          <span style={{ marginRight: 24, color: '#52c41a', fontWeight: 'bold' }}>
            ✅ 已生成: {completedCount}
          </span>
          {failedCount > 0 && (
            <span style={{marginRight: 24, color: '#ff4d4f', fontWeight: 'bold' }}>
              ❌ 失败: {failedCount}
            </span>
          )}
           <span style={{ marginRight: 24, color: '#722ed1', fontWeight: 'bold' }}>
            ⭐ 已完结: {finalizedCount}/{completedCount}
          </span>
        </div>

        {}
        {!canFinish && pendingCount === 0 && processingCount === 0 && (
          <Alert
            message="请进入每轮任务改进提示词"
            description={
              <div>
                <p style={{ marginTop: 12, color: '#666' }}>
                  💡 当您认为该任务的生成图已与目标图足够相似时即可将其标记为最终版本
                </p>
                <p>您需要将<strong>所有已生成的任务</strong>都标记为最终版本才能完成测试。</p>
                <p>已生成: <strong>{completedCount}</strong> 个</p>
                <p>已完结: <strong>{finalizedCount}</strong> 个</p>
                <p>待标记: <strong>{completedCount - finalizedCount}</strong> 个</p>

                {completedCount < MIN_COMPLETED_REQUIRED && (
                  <p style={{ marginTop: 12, color: '#ff4d4f' }}>
                    ⚠️ 注意：还需要至少 <strong>{MIN_COMPLETED_REQUIRED - completedCount}</strong> 个任务成功完成（当前 {completedCount}/{MIN_COMPLETED_REQUIRED}）
                  </p>
                )}
              </div>
            }
            type="warning"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

        {}
        <Row gutter={[16, 16]}>
          {tasks.map((task, index) => {
            const hasFinal = task.has_final_version === true

            return (
              <Col span={8} key={task.task_id}>
                <Card
                  hoverable={task.status === 'completed' || task.status === 'failed'}
                  onClick={() => {
                    if (task.status === 'completed') {
                      navigate(`/image/${task.task_id}`)
                    } else if (task.status === 'failed') {
                      navigate(`/image/${task.task_id}`)
                    } else if (task.status === 'processing') {
                      message.info('图片正在生成中，请稍候...')
                    } else {
                      message.warning('请先提交prompt')
                    }
                  }}
                  style={{
                    cursor: task.status === 'completed' || task.status === 'failed' ? 'pointer' : 'not-allowed',
                    border: hasFinal ? '2px solid #52c41a' : '1px solid #d9d9d9'
                  }}
                  cover={
                    task.status === 'completed' ? (
                      <div style={{ position: 'relative' }}>
                        <img
                          src={task.generated_image_url || task.target_image_url}
                          alt={`任务 ${index + 1}`}
                          style={{ height: 200, objectFit: 'cover' }}
                        />
                        {}
                        {hasFinal && (
                          <div style={{
                            position: 'absolute',
                            top: 8,
                            right: 8,
                            background: '#52c41a',
                            color: 'white',
                            padding: '4px 12px',
                            borderRadius: 4,
                            fontSize: 12,
                            fontWeight: 'bold',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
                          }}>
                            ⭐ 最终版本
                          </div>
                        )}
                      </div>
                    ) : task.status === 'failed' ? (
                      <div style={{ position: 'relative', height: 200, background: '#f5f5f5' }}>
                        <img
                          src={task.target_image_url}
                          alt={`任务 ${index + 1}`}
                          style={{
                            height: 200,
                            objectFit: 'cover',
                            opacity: 0.3,
                            filter: 'grayscale(100%)'
                          }}
                        />
                        <div style={{
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          transform: 'translate(-50%, -50%)',
                          fontSize: 48,
                          color: '#ff4d4f'
                        }}>
                          ❌
                        </div>
                      </div>
                    ) : (
                      <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
                        {task.status === 'processing' ? (
                          <div style={{ textAlign: 'center' }}>
                            <Spin />
                            <div style={{ marginTop: 10, color: '#666' }}>生成中...</div>
                          </div>
                        ) : (
                          <div style={{ color: '#999' }}>等待中...</div>
                        )}
                      </div>
                    )
                  }
                >
                  <Card.Meta
                    title={`任务 ${task.round_number}`}
                    description={
                      <div>
                        <div>状态: {
                          task.status === 'completed' ? '😎 已生成' :
                          task.status === 'processing' ? '⏳ 生成中' :
                          task.status === 'failed' ? '❌ 生成失败(需重新提交）' :
                          '○ 等待中'
                        }</div>
                        {task.status === 'completed' && !hasFinal && (
                          <div style={{ color: '#fa8c16', marginTop: 4, fontSize: 12 }}>
                            请继续打磨提示词提升相似度
                          </div>
                        )}
                      </div>
                    }
                  />
                </Card>
              </Col>
            )
          })}
        </Row>

        {}
        {canFinish ? (
          <div style={{ marginTop: 30, textAlign: 'center' }}>
            {failedCount > 0 && (
              <div style={{
                marginBottom: 16,
                padding: 12,
                background: '#fff7e6',
                border: '1px solid #ffd591',
                borderRadius: 4,
                color: '#d46b08'
              }}>
                ⚠️ 注意：有 {failedCount} 张图片生成失败，但您已标记足够的最终版本，可以完成测试。
              </div>
            )}
            <Alert
              message="恭喜！"
              description={`您已将所有 ${completedCount} 个已生成的任务都标记为最终版本，可以完成测试了。`}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Button type="primary" size="large" onClick={handleFinish}>
              完成所有测试
            </Button>
          </div>
        ) : (
          <div style={{
            marginTop: 30,
            textAlign: 'center'
          }}>
            {processingCount > 0 ? (
              <div style={{
                padding: 12,
                background: '#e6f7ff',
                borderRadius: 4,
                color: '#0050b3'
              }}>
                ⏳ 还有 {processingCount} 张图片正在生成中，请稍候...
              </div>
            ) : (
              <Button
                type="primary"
                size="large"
                disabled
                style={{ opacity: 0.5, cursor: 'not-allowed' }}
              >
                需要标记所有已生成任务 (已标记: {finalizedCount}/{completedCount})
              </Button>
            )}
          </div>
        )}
      </Card>
    </div>
  )
}
