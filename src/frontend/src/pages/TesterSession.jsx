import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Input, Button, Progress, message, Spin, Modal, Radio, Space } from 'antd'
import { startSession, submitTask, getTaskStatus } from '../services/api'

const { TextArea } = Input

const TASKS_PER_SESSION = 10

export default function TesterSession() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [session, setSession] = useState(null)
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0)
  const [prompt, setPrompt] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [progress, setProgress] = useState([])
  const [promptStartTime, setPromptStartTime] = useState(null)

  const [difficultyRating, setDifficultyRating] = useState(null)
  const [showDifficultyModal, setShowDifficultyModal] = useState(false)
  const [ratedTasks, setRatedTasks] = useState(new Set())

  const [submittedCount, setSubmittedCount] = useState(0)

  useEffect(() => {
    initSession()
  }, [])

  useEffect(() => {

    if (session && currentTaskIndex < TASKS_PER_SESSION) {
      const currentTask = session.tasks[currentTaskIndex]

      if (currentTask &&
          currentTask.status === 'pending' &&
          !ratedTasks.has(currentTask.task_id)) {
        setShowDifficultyModal(true)
      }
    }
  }, [currentTaskIndex, session, ratedTasks])

  const initSession = async () => {
    try {
      const res = await startSession()
      const sessionData = res.data

      setSession(sessionData)

      const tasks = sessionData.tasks

      const submitted = tasks.filter(t =>
        t.status === 'completed' || t.status === 'processing' || t.status === 'failed'
      ).length
      setSubmittedCount(submitted)

      if (submitted >= TASKS_PER_SESSION) {
        message.success('所有任务已提交，正在进入画廊...')
        setTimeout(() => {
          navigate(`/results/${sessionData.session_id}`)
        }, 1000)
        return
      }

      const firstPendingIndex = tasks.findIndex(t => t.status === 'pending')
      if (firstPendingIndex !== -1) {
        setCurrentTaskIndex(firstPendingIndex)
      } else {

        const completedCount = tasks.filter(t => t.status === 'completed').length
        setCurrentTaskIndex(completedCount)
      }

      setProgress(tasks.map(t => ({
        status: t.status,
        taskId: t.task_id
      })))

      tasks.forEach((t, index) => {
        if (t.status === 'processing') {
          pollTaskStatus(t.task_id, index)
        }
      })

      const completedCount = tasks.filter(t => t.status === 'completed').length
      if (completedCount > 0 && completedCount < TASKS_PER_SESSION) {
        message.success(`已恢复session，已完成 ${completedCount}/${TASKS_PER_SESSION} 个任务`)
      } else if (completedCount === TASKS_PER_SESSION) {
        message.success('🎉 所有任务已完成！')
      }

      setLoading(false)

    } catch (error) {
      message.error('启动session失败: ' + (error.response?.data?.detail || error.message))
      setLoading(false)
    }
  }

  const handleDifficultySubmit = () => {
    if (!difficultyRating) {
      message.warning('请选择难度等级')
      return
    }

    const currentTask = session.tasks[currentTaskIndex]

    setRatedTasks(prev => new Set([...prev, currentTask.task_id]))

    setShowDifficultyModal(false)
    setPromptStartTime(Date.now())
  }

  const handleSubmit = async () => {
    if (!prompt.trim()) {
      message.warning('请输入prompt')
      return
    }

    if (!difficultyRating) {
      message.warning('请先评价难度')
      setShowDifficultyModal(true)
      return
    }

    const task = session.tasks[currentTaskIndex]

    if (task.status === 'processing') {
      message.info('该任务正在生成中，请稍候...')
      return
    }

    if (task.status === 'failed') {
      message.error('该任务生成失败，请联系管理员')
      return
    }

    setSubmitting(true)

    try {

      const timeSpent = promptStartTime
        ? Math.round((Date.now() - promptStartTime) / 1000)
        : 0

      await submitTask(task.task_id, {
        prompt: prompt,
        time_spent_seconds: timeSpent,
        difficulty_rating: difficultyRating
      })

      setProgress(prevProgress => {
        const newProgress = [...prevProgress]
        newProgress[currentTaskIndex] = { status: 'processing', taskId: task.task_id }
        return newProgress
      })

      setSession(prevSession => {
        const newSession = { ...prevSession }
        newSession.tasks[currentTaskIndex].status = 'processing'
        return newSession
      })

      const newSubmittedCount = submittedCount + 1
      setSubmittedCount(newSubmittedCount)

      pollTaskStatus(task.task_id, currentTaskIndex)

      setPrompt('')
      setPromptStartTime(null)
      setDifficultyRating(null)

      if (newSubmittedCount >= TASKS_PER_SESSION) {
        message.success('🎉 所有任务已提交！正在进入画廊...')
        setTimeout(() => {
          navigate(`/results/${session.session_id}`)
        }, 1500)
      } else {

        setCurrentTaskIndex(currentTaskIndex + 1)
        message.success(`已提交第 ${newSubmittedCount} 个任务，正在生成...`)
      }

    } catch (error) {
      console.error('提交失败:', error)
      message.error('提交失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSubmitting(false)
    }
  }

  const pollTaskStatus = (taskId, taskIndex) => {
    const poll = setInterval(async () => {
      try {
        const res = await getTaskStatus(taskId)
        const { status, image_url } = res.data

        if (status === 'completed') {
          clearInterval(poll)

          setProgress(prevProgress => {
            const newProgress = [...prevProgress]
            newProgress[taskIndex] = { status: 'completed', taskId }
            return newProgress
          })

          setSession(prevSession => {
            const newSession = { ...prevSession }
            newSession.tasks[taskIndex].status = 'completed'
            newSession.tasks[taskIndex].generated_image_url = image_url
            return newSession
          })

          message.success(`第 ${taskIndex + 1} 张图片生成完成`)

        } else if (status === 'failed') {
          clearInterval(poll)

          setProgress(prevProgress => {
            const newProgress = [...prevProgress]
            newProgress[taskIndex] = { status: 'failed', taskId }
            return newProgress
          })

          setSession(prevSession => {
            const newSession = { ...prevSession }
            newSession.tasks[taskIndex].status = 'failed'
            return newSession
          })

          message.error(`第 ${taskIndex + 1} 张图片生成失败（可能被审核拒绝）`, 5)
        }
      } catch (error) {
        console.error('轮询任务状态失败:', error)
      }
    }, 3000)
  }

  const handleViewResults = () => {
    navigate(`/results/${session.session_id}`)
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!session) {
    return <div>Session加载失败</div>
  }

  if (!session.tasks || session.tasks.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <p>正在加载任务...</p>
      </div>
    )
  }

  const currentTask = session.tasks[currentTaskIndex]

  const allSubmitted = submittedCount >= TASKS_PER_SESSION

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1>Pica 图像生成测试</h1>

      {}
      <Card style={{ marginBottom: 24 }}>
        <h3>进度</h3>
        <Progress
          percent={Math.round((submittedCount / TASKS_PER_SESSION) * 100)}
          format={() => `${submittedCount}/${TASKS_PER_SESSION}`}
          status={allSubmitted ? 'success' : 'active'}
        />
        <p style={{ marginTop: 8, color: '#666' }}>
          {allSubmitted
            ? '🎉 所有任务已提交！'
            : `已提交 ${submittedCount} 个任务，正在进行第 ${currentTaskIndex + 1} 张图片`}
        </p>

        {}
        {submittedCount > 0 && (
          <div style={{ marginTop: 12, fontSize: 13, color: '#999' }}>
            <span style={{ marginRight: 16 }}>
              ✅ 已完成: {session.tasks.filter(t => t.status === 'completed').length}
            </span>
            <span style={{ marginRight: 16 }}>
              ⏳ 生成中: {session.tasks.filter(t => t.status === 'processing').length}
            </span>
            {session.tasks.filter(t => t.status === 'failed').length > 0 && (
              <span style={{ color: '#ff4d4f' }}>
                ❌ 失败: {session.tasks.filter(t => t.status === 'failed').length}
              </span>
            )}
          </div>
        )}
      </Card>

      {}
      <Modal
        title="请评价目标图的难度"
        open={showDifficultyModal && currentTask && !ratedTasks.has(currentTask.task_id)}
        closable={false}
        footer={null}
        maskClosable={false}
      >
        <div style={{ padding: '16px 0' }}>
          <p style={{ marginBottom: 16, fontSize: 14, color: '#666' }}>
            请根据目标图的复杂程度选择难度等级。难度评级仅用于研究目的，不会影响您的任务进度。
          </p>

          {}
          {currentTask && currentTask.target_image_url && (
            <div style={{ marginBottom: 24, textAlign: 'center' }}>
              <img
                src={currentTask.target_image_url}
                alt="目标图片"
                style={{
                  maxWidth: '400px',
                  maxHeight: '400px',
                  border: '2px solid #d9d9d9',
                  borderRadius: 8,
                  objectFit: 'contain'
                }}
                onError={(e) => {
                  console.error('图片加载失败:', currentTask.target_image_url)
                  e.target.style.display = 'none'
                }}
              />
            </div>
          )}

          <Radio.Group
            value={difficultyRating}
            onChange={(e) => setDifficultyRating(e.target.value)}
            style={{ width: '100%' }}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Radio value="easy" style={{ padding: '12px 16px', border: '1px solid #d9d9d9', borderRadius: 8, width: '100%' }}>
                <strong>简单</strong> - 图片内容简单，容易描述
              </Radio>
              <Radio value="medium" style={{ padding: '12px 16px', border: '1px solid #d9d9d9', borderRadius: 8, width: '100%' }}>
                <strong>中等</strong> - 图片有一定复杂度，需要仔细观察
              </Radio>
              <Radio value="hard" style={{ padding: '12px 16px', border: '1px solid #d9d9d9', borderRadius: 8, width: '100%' }}>
                <strong>困难</strong> - 图片非常复杂，细节丰富
              </Radio>
            </Space>
          </Radio.Group>

          <Button
            type="primary"
            onClick={handleDifficultySubmit}
            disabled={!difficultyRating}
            block
            style={{ marginTop: 24 }}
            size="large"
          >
            确认并开始
          </Button>
        </div>
      </Modal>

      {}
      {!allSubmitted && currentTask && (
        <Card title={`第 ${currentTaskIndex + 1} / ${TASKS_PER_SESSION} 张图片`}>
          <div style={{ marginBottom: 16 }}>
            <strong>目标图片：</strong>
            <div style={{ marginTop: 8, textAlign: 'center' }}>
              <img
                src={currentTask.target_image_url}
                alt="目标图片"
                style={{
                  maxWidth: '500px',
                  maxHeight: '500px',
                  border: '1px solid #d9d9d9',
                  borderRadius: 4,
                  objectFit: 'contain'
                }}
                onError={(e) => {
                  console.error('目标图片加载失败:', currentTask.target_image_url)
                  message.error('图片加载失败，请刷新页面')
                }}
              />
            </div>
          </div>

          {currentTask.ground_truth && (
            <div style={{ marginBottom: 16, padding: 12, background: '#f0f0f0', borderRadius: 4 }}>
              <strong>Ground Truth:</strong>
              <p style={{ marginTop: 4, marginBottom: 0 }}>{currentTask.ground_truth}</p>
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <strong>请输入生成这张图片的提示词：</strong>
            <TextArea
              rows={6}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="请详细描述目标图片的内容、风格、构图等..."
              disabled={showDifficultyModal || submitting}
              style={{ marginTop: 8 }}
            />
          </div>

          <Button
            type="primary"
            onClick={handleSubmit}
            loading={submitting}
            disabled={showDifficultyModal}
            size="large"
            block
          >
            {submitting ? '提交中...' : '提交'}
          </Button>

          {}
          {session.tasks.some(t => t.status === 'failed') && (
            <div style={{
              marginTop: 16,
              padding: 12,
              background: '#fff7e6',
              border: '1px solid #ffd591',
              borderRadius: 4
            }}>
              <p style={{ margin: 0, fontSize: 13, color: '#d46b08' }}>
                ⚠️ 有 {session.tasks.filter(t => t.status === 'failed').length} 张图片生成失败（可能被内容审核拒绝）。
                不用担心，提交完所有任务后可以在画廊中查看成功生成的图片。
              </p>
            </div>
          )}
        </Card>
      )}

      {}
      {allSubmitted && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <h2>🎉 所有任务已提交完成！</h2>
            <p style={{ fontSize: 16, margin: '20px 0', color: '#666' }}>
              您已提交 {TASKS_PER_SESSION} 个任务的提示词
            </p>

            {}
            <div style={{
              margin: '24px auto',
              maxWidth: 400,
              padding: 16,
              background: '#f5f5f5',
              borderRadius: 8
            }}>
              <div style={{ marginBottom: 8 }}>
                <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                  ✅ 已完成: {session.tasks.filter(t => t.status === 'completed').length}
                </span>
              </div>
              {session.tasks.filter(t => t.status === 'processing').length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <span style={{ color: '#1890ff' }}>
                    ⏳ 生成中: {session.tasks.filter(t => t.status === 'processing').length}
                  </span>
                </div>
              )}
              {session.tasks.filter(t => t.status === 'failed').length > 0 && (
                <div>
                  <span style={{ color: '#ff4d4f' }}>
                    ❌ 失败: {session.tasks.filter(t => t.status === 'failed').length}
                  </span>
                </div>
              )}
            </div>

            <Button
              type="primary"
              size="large"
              onClick={handleViewResults}
            >
              进入画廊
            </Button>

            <p style={{ marginTop: 16, fontSize: 13, color: '#999' }}>
              {session.tasks.filter(t => t.status === 'processing').length > 0
                ? '正在生成的图片完成后会自动显示在画廊中'
                : ''}
            </p>
          </div>
        </Card>
      )}
    </div>
  )
}
