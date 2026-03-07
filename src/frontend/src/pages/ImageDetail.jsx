import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Rate, Input, Button, Space, message, Spin, Divider, Alert, Tooltip, Progress, Slider, Row, Col } from 'antd'
import { StarOutlined } from '@ant-design/icons'
import { getTaskDetail, rateVersion, submitTask, finalizeVersion, getRatingDimensions } from '../services/api'
import { MAX_VERSIONS_PER_TASK } from '../config'
const { TextArea } = Input

export default function ImageDetail() {
  const { taskId } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [task, setTask] = useState(null)
  const [dimensions, setDimensions] = useState(null)

  const [wiseSuggestions, setWiseSuggestions] = useState(null)
  const [wiseLoading, setWiseLoading] = useState(false)
  const [wiseError, setWiseError] = useState(null)

  const [manualScore, setManualScore] = useState(0)
  const [savingManualScore, setSavingManualScore] = useState(false)
  const [hasManualScoreSaved, setHasManualScoreSaved] = useState(false)

  const [styleScore, setStyleScore] = useState(0)
  const [objectCountScore, setObjectCountScore] = useState(0)
  const [perspectiveScore, setPerspectiveScore] = useState(0)
  const [depthBackgroundScore, setDepthBackgroundScore] = useState(0)
  const [hasStarScoreSaved, setHasStarScoreSaved] = useState(false)

  const isFailedTask = task?.status === 'failed'
  const failedTaskHasVersions = task?.versions && task.versions.length > 0
  const failedTaskLastVersion = failedTaskHasVersions ? task.versions[task.versions.length - 1] : null
  const isInitialFailed = isFailedTask && failedTaskHasVersions && task.versions.length === 1

  const [detailedReview, setDetailedReview] = useState('')

  const [modifyPrompt, setModifyPrompt] = useState('')

  const [modifying, setModifying] = useState(false)
  const [rating, setRating] = useState(false)
  const [modifyStartTime, setModifyStartTime] = useState(null)

  useEffect(() => {
    loadDimensions()
    loadTask()
  }, [taskId])

  useEffect(() => {
    if (!task || !task.versions || task.versions.length === 0) return

    const latestVersion = task.versions[task.versions.length - 1]

    if (latestVersion.is_final) {
      console.log('⚠️ 版本已标记final，跳过自动保存')
      return
    }

    if (manualScore > 0 && latestVersion.user_manual_score !== manualScore) {
      const timer = setTimeout(async () => {
        try {
          const response = await fetch(`/api/versions/${latestVersion.version_id}/manual-score`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({
              user_manual_score: manualScore
            })
          })

          if (response.ok) {
            setHasManualScoreSaved(true)
            const updatedTask = { ...task }
            updatedTask.versions[updatedTask.versions.length - 1].user_manual_score = manualScore
            setTask(updatedTask)
            console.log(`✅ 自动保存滑轮评分: ${manualScore}`)
          }
        } catch (error) {
          console.error('自动保存滑轮评分失败:', error)
        }
      }, 1000)

      return () => clearTimeout(timer)
    }
  }, [manualScore, task])

  const loadDimensions = async () => {
    try {
      const res = await getRatingDimensions()
      setDimensions(res.data)
    } catch (error) {
      console.error('加载评分维度失败:', error)
    }
  }

const loadTask = async () => {
    try {
      const res = await getTaskDetail(taskId)
      const taskData = res.data
      setTask(taskData)

      if (taskData.versions && taskData.versions.length > 0) {
        const latestVersion = taskData.versions[taskData.versions.length - 1]

        let currentManualScore = 0
        let foundScore = false

        if (latestVersion.user_manual_score !== null &&
            latestVersion.user_manual_score !== undefined) {
          currentManualScore = latestVersion.user_manual_score
          foundScore = true
          console.log('✅ 当前版本有相似度评分:', currentManualScore)
        } else {
          console.log('⚠️ 当前版本未评分，设为0（不继承之前版本）')
        }

        setManualScore(currentManualScore)
        setHasManualScoreSaved(foundScore)

        if (latestVersion.rating) {
          setStyleScore(latestVersion.rating.style_score || 0)
          setObjectCountScore(latestVersion.rating.object_count_score || 0)
          setPerspectiveScore(latestVersion.rating.perspective_score || 0)
          setDepthBackgroundScore(latestVersion.rating.depth_background_score || 0)
          setDetailedReview(latestVersion.rating.detailed_review || '')
          setHasStarScoreSaved(true)
          console.log('✅ 当前版本有星星评分')
        } else {
          let inheritedRating = null
          for (let i = taskData.versions.length - 2; i >= 0; i--) {
            const prevVersion = taskData.versions[i]
            if (prevVersion.rating) {
              inheritedRating = prevVersion.rating
              console.log(`✅ 继承版本${i+1}的星星评分`)
              break
            }
          }

          if (inheritedRating) {
            setStyleScore(inheritedRating.style_score || 0)
            setObjectCountScore(inheritedRating.object_count_score || 0)
            setPerspectiveScore(inheritedRating.perspective_score || 0)
            setDepthBackgroundScore(inheritedRating.depth_background_score || 0)
            setDetailedReview(inheritedRating.detailed_review || '')
            setHasStarScoreSaved(false)
          } else {
            console.log('⚠️ 没有找到任何版本的星星评分，设为0星')
            setStyleScore(0)
            setObjectCountScore(0)
            setPerspectiveScore(0)
            setDepthBackgroundScore(0)
            setDetailedReview('')
            setHasStarScoreSaved(false)
          }
        }

        setModifyPrompt(latestVersion.prompt || '')

        if (latestVersion.wise_generated) {

          if (latestVersion.wise_suggestions && latestVersion.wise_suggestions.length > 0) {
            setWiseSuggestions(latestVersion.wise_suggestions)
            setWiseLoading(false)
            console.log('✅ 加载到 Wise 建议:', latestVersion.wise_suggestions.length, '条')
          } else if (latestVersion.wise_error) {
            setWiseError(latestVersion.wise_error)
            setWiseLoading(false)
            console.log('⚠️  Wise 分析失败:', latestVersion.wise_error)
          } else {
            setWiseSuggestions(null)
            setWiseLoading(false)
            console.log('⚠️  当前版本没有Wise建议')
          }
        } else {

          setWiseLoading(true)
          setWiseSuggestions(null)
          setWiseError(null)
          console.log('⏳ Wise 分析中...')
        }
      }

      setLoading(false)
    } catch (error) {
      message.error('加载失败: ' + (error.response?.data?.detail || error.message))
      setLoading(false)
    }
  }

const handleRate = async () => {
    setRating(true)
    try {
      const latestVersion = task.versions[task.versions.length - 1]

      await rateVersion(latestVersion.version_id, {
        style_score: styleScore,
        object_count_score: objectCountScore,
        perspective_score: perspectiveScore,
        depth_background_score: depthBackgroundScore,
        detailed_review: detailedReview.trim() || '无'
      })

      message.success('评分已保存')
      setHasStarScoreSaved(true)

      const updatedTask = { ...task }
      updatedTask.versions[updatedTask.versions.length - 1].rating = {
        style_score: styleScore,
        object_count_score: objectCountScore,
        perspective_score: perspectiveScore,
        depth_background_score: depthBackgroundScore,
        detailed_review: detailedReview.trim() || '无'
      }
      setTask(updatedTask)

    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message
      message.error('评分失败: ' + errorMsg)
    } finally {
      setRating(false)
    }
  }

  const handleSaveManualScore = async () => {
    setSavingManualScore(true)
    try {
      const latestVersion = task.versions[task.versions.length - 1]

      const response = await fetch(`/api/versions/${latestVersion.version_id}/manual-score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          user_manual_score: manualScore
        })
      })

      if (response.ok) {
        message.success(`相似度评分已保存: ${manualScore}/100`)
        setHasManualScoreSaved(true)

        const updatedTask = { ...task }
        updatedTask.versions[updatedTask.versions.length - 1].user_manual_score = manualScore
        setTask(updatedTask)
      } else {
        throw new Error('保存失败')
      }

    } catch (error) {
      message.error('保存失败: ' + error.message)
    } finally {
      setSavingManualScore(false)
    }
  }

const handleModify = async () => {
    if (!modifyPrompt.trim()) {
      message.warning('请输入提示词')
      return
    }

    if (!isFailedTask) {

      if (manualScore === 0) {
        message.warning('⚠️ 请先对当前版本进行相似度评分（拖动滑轮打分，0分不允许生成）')
        return
      }

      if (styleScore === 0 || objectCountScore === 0 || perspectiveScore === 0 || depthBackgroundScore === 0) {
        message.warning('⚠️ 请先完成所有维度的星级评分（每个维度至少1星）')
        return
      }
    }

    setModifying(true)
    try {
      const timeSpent = modifyStartTime
        ? Math.floor((Date.now() - modifyStartTime) / 1000)
        : 0

      await submitTask(taskId, {
        prompt: modifyPrompt,
        time_spent_seconds: timeSpent
      })

      message.success(isFailedTask ? '已重新提交，请等待生成' : '修改任务已提交，正在生成新版本...')

      let previousRating = null

      if (!isFailedTask && task.versions && task.versions.length > 0) {
        const previousVersion = task.versions[task.versions.length - 1]

        if (previousVersion.rating) {
          previousRating = {
            style_score: previousVersion.rating.style_score || 0,
            object_count_score: previousVersion.rating.object_count_score || 0,
            perspective_score: previousVersion.rating.perspective_score || 0,
            depth_background_score: previousVersion.rating.depth_background_score || 0,
            detailed_review: previousVersion.rating.detailed_review || ''
          }
        }
      }

      setModifyStartTime(null)

      let attempts = 0
      const maxAttempts = 120

      const checkInterval = setInterval(async () => {
        attempts++
        try {
          const updatedTask = await getTaskDetail(taskId)

          const shouldStop = isFailedTask
            ? (updatedTask.data.status === 'completed')
            : (updatedTask.data.versions.length > task.versions.length)

          if (shouldStop) {
            clearInterval(checkInterval)

            const newLatestVersion = updatedTask.data.versions[updatedTask.data.versions.length - 1]

            if (!isFailedTask) {

              console.log('⚠️ 新版本生成，滑轮评分重置为0，请手动评分')
              setManualScore(0)
              setHasManualScoreSaved(false)

              if (previousRating) {
                try {
                  await rateVersion(newLatestVersion.version_id, {
                    style_score: previousRating.style_score,
                    object_count_score: previousRating.object_count_score,
                    perspective_score: previousRating.perspective_score,
                    depth_background_score: previousRating.depth_background_score,
                    detailed_review: previousRating.detailed_review || '无'
                  })
                  console.log('✅ 自动应用前一版本星星评分到新版本')

                  setStyleScore(previousRating.style_score)
                  setObjectCountScore(previousRating.object_count_score)
                  setPerspectiveScore(previousRating.perspective_score)
                  setDepthBackgroundScore(previousRating.depth_background_score)
                  setDetailedReview(previousRating.detailed_review)
                  setHasStarScoreSaved(true)
                } catch (err) {
                  console.error('自动保存星级评分失败:', err)

                  setStyleScore(0)
                  setObjectCountScore(0)
                  setPerspectiveScore(0)
                  setDepthBackgroundScore(0)
                  setDetailedReview('')
                  setHasStarScoreSaved(false)
                }
              } else {

                setStyleScore(0)
                setObjectCountScore(0)
                setPerspectiveScore(0)
                setDepthBackgroundScore(0)
                setDetailedReview('')
                setHasStarScoreSaved(false)
              }
            } else {

              setManualScore(0)
              setHasManualScoreSaved(false)
              setStyleScore(0)
              setObjectCountScore(0)
              setPerspectiveScore(0)
              setDepthBackgroundScore(0)
              setDetailedReview('')
              setHasStarScoreSaved(false)
            }

            setTask(updatedTask.data)
            setModifyPrompt(newLatestVersion.prompt || '')

            const successMsg = isFailedTask
              ? '重新生成成功！请对新图片进行评分'
              : '新版本生成完成！请重新评分'
            message.success(successMsg)
            setModifying(false)
          } else if (attempts >= maxAttempts) {
            clearInterval(checkInterval)
            message.warning('生成时间较长，请稍后刷新查看')
            setModifying(false)
          }
        } catch (error) {
          clearInterval(checkInterval)
          message.error('检查状态失败: ' + error.message)
          setModifying(false)
        }
      }, 10000)

    } catch (error) {
      message.error('修改失败: ' + (error.response?.data?.detail || error.message))
      setModifying(false)
    }
  }

const handleFinalize = async () => {
    const currentLatestVersion = task.versions[task.versions.length - 1]

    if (!currentLatestVersion.user_manual_score || currentLatestVersion.user_manual_score === 0) {
      message.warning('⚠️ 请先完成相似度评分才能标记为最终版本（拖动滑轮打分）')
      return
    }

    if (!currentLatestVersion.rating ||
        currentLatestVersion.rating.style_score === 0 ||
        currentLatestVersion.rating.object_count_score === 0 ||
        currentLatestVersion.rating.perspective_score === 0 ||
        currentLatestVersion.rating.depth_background_score === 0) {
      message.warning('⚠️ 请先完成所有维度的星级评分才能标记为最终版本（每个维度至少1星）')
      return
    }

    try {
      await finalizeVersion(currentLatestVersion.version_id)
      message.success('已标记为最终版本')
      navigate(-1)
    } catch (error) {
      message.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  if (loading) {
    return <Spin size="large" style={{ margin: '200px auto', display: 'block' }} />
  }

  if (!task) {
    return <div style={{ textAlign: 'center', padding: 40 }}>Task数据加载失败</div>
  }

  if (!task.versions) {
    task.versions = []
  }

  const latestVersion = task.versions.length > 0 ? task.versions[task.versions.length - 1] : null
  const isProcessing = latestVersion?.status === 'processing'
  const canModify = task.versions.length < MAX_VERSIONS_PER_TASK && !latestVersion?.is_final

  return (
    <div style={{ padding: 24, maxWidth: 1400, margin: '0 auto' }}>
      <Button onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>
        ← 返回
      </Button>
      {isFailedTask ? (
        <Card>
          {}
          <Alert
            message={"生成失败"}
            description={
              <div>
                <p><strong>提示词可能违反了内容审核规则，请修改后重新提交。</strong></p>
                {isInitialFailed ? (
                  <p>重新提交将更新初始版本。</p>
                ) : (
                  <p>重新提交将覆盖失败的版本。</p>
                )}
              </div>
            }
            type="error"
            showIcon
            style={{ marginBottom: 20 }}
          />

          {}
          <div style={{ marginTop: 20 }}>
            <h3>任务 {task.round_number} - 重新提交</h3>

            <Row gutter={24} style={{ marginTop: 20 }}>
              <Col span={12}>
                {}
                <Card title="目标图片" size="small">
                  <img
                    src={task.target_image_url}
                    alt="Target"
                    style={{ width: '100%', borderRadius: 8 }}
                  />

                </Card>
              </Col>

              <Col span={12}>
                {}
                <Card
                  title={`修改提示词`}
                  size="small"
                >
                  <Alert
                    message="⚠️ 请修改提示词，避免敏感内容"
                    type="warning"
                    showIcon
                    style={{ marginBottom: 12 }}
                  />

                 <TextArea
                  value={modifyPrompt}
                  onChange={(e) => {
                    setModifyPrompt(e.target.value)
                    if (!modifyStartTime) {
                      setModifyStartTime(Date.now())
                    }
                  }}
                  rows={12}
                  disabled={modifying}
                  placeholder="请输入新的提示词..."
                />

                  <Button
                    type="primary"
                    onClick={handleModify}
                    loading={modifying}
                    disabled={!modifyPrompt.trim()}
                    block
                    size="large"
                    style={{ marginTop: 12 }}
                  >
                    {modifying ? '正在提交...' : '重新提交'}
                  </Button>

                  <div style={{ marginTop: 8, fontSize: 12, color: '#666', textAlign: 'center' }}>
                  </div>
                </Card>
              </Col>
            </Row>
          </div>
        </Card>
      ) : (
        <>
      <Card>
        {}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 15,
          paddingLeft: 20,
          paddingRight: 20
        }}>
          <h3 style={{ margin: 0, fontSize: 16 }}>图片对比</h3>
          <div style={{ fontSize: 12, color: '#999' }}>
            版本追踪: v{latestVersion.version_number} / 8
            {latestVersion.is_final && (
              <span style={{ marginLeft: 8, color: '#52c41a' }}>✓ 最终版本</span>
            )}
          </div>
        </div>

        {}
        <div style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          backgroundColor: '#fff',
          padding: '15px 0',
          marginBottom: 20,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 4
        }}>
          <div style={{
            display: 'flex',
            gap: 10,
            paddingLeft: 20,
            paddingRight: 20,
            maxWidth: '1000px',
            margin: '0 auto',
            justifyContent: 'center',
            alignItems: 'center'
          }}>
            {}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <img
                src={task.target_image_url}
                alt="target"
                style={{
                  width: '300px',
                  maxHeight: '350px',
                  objectFit: 'contain',
                  border: '2px solid #d9d9d9',
                  borderRadius: 4,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  backgroundColor: '#fafafa'
                }}
              />
              <div style={{
                writingMode: 'vertical-rl',
                textOrientation: 'upright',
                fontSize: 14,
                fontWeight: 500,
                color: '#666',
                letterSpacing: '2px'
              }}>
                目标图片
              </div>
            </div>

            {}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              {isProcessing ? (
                <div style={{
                  width: '300px',
                  height: '350px',
                  border: '2px solid #1890ff',
                  borderRadius: 4,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#f5f5f5'
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 10 }}>生成中...</div>
                  </div>
                </div>
              ) : (
                <img
                  src={latestVersion.image_url}
                  alt="generated"
                  style={{
                    width: '300px',
                    maxHeight: '350px',
                    objectFit: 'contain',
                    border: '2px solid #1890ff',
                    borderRadius: 4,
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    backgroundColor: '#fafafa'
                  }}
                />
              )}
              <div style={{
                writingMode: 'vertical-rl',
                textOrientation: 'upright',
                fontSize: 14,
                fontWeight: 500,
                color: '#1890ff',
                letterSpacing: '2px'
              }}>
                生成图片
              </div>
            </div>
          </div>
        </div>

        {}
        {task.versions.length > 1 && (
          <>
            <Divider />
            <div>
              <h3>版本历史 ({task.versions.length}/8)</h3>
              <div style={{ display: 'flex', gap: 15, overflowX: 'auto', paddingBottom: 10 }}>
                {task.versions.map((v, i) => (
                  <div key={v.version_id} style={{ textAlign: 'center', minWidth: 100 }}>
                    <img
                      src={v.thumbnail_url}
                      alt={`v${v.version_number}`}
                      style={{
                        width: 100,
                        height: 100,
                        objectFit: 'cover',
                        border: i === task.versions.length - 1 ? '3px solid #1890ff' : '1px solid #d9d9d9',
                        borderRadius: 4,
                        cursor: 'pointer'
                      }}
                    />
                    <div style={{ fontSize: 12, marginTop: 5 }}>
                      v{v.version_number}
                      {v.rating && (
                        <div style={{ color: '#faad14' }}>
                          <StarOutlined /> {((v.rating.style_score + v.rating.object_count_score + v.rating.perspective_score + v.rating.depth_background_score) / 4).toFixed(1)}
                        </div>
                      )}
                      {v.ai_similarity_score !== null && v.ai_similarity_score !== undefined && (
                        <div style={{ color: '#52c41a', fontSize: 10 }}>

                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {}
        {latestVersion.is_final && (
          <>
            <Divider />
            <div style={{ marginBottom: 30 }}>
              <h3>AI 综合相似度评分</h3>
              <Alert
                message="AI 自动评分"
                description="以下是基于 DINO v2 + 颜色 + 结构的综合相似度评分"
                type="info"
                showIcon
                style={{ marginBottom: 20 }}
              />

              {latestVersion.ai_similarity_score !== null && latestVersion.ai_similarity_score !== undefined ? (
                <div style={{
                  padding: 30,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: 12,
                  marginBottom: 20,
                  boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      fontSize: 48,
                      fontWeight: 'bold',
                      color: '#fff',
                      marginBottom: 10,
                      textShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}>
                      {latestVersion.ai_similarity_score.toFixed(1)}
                    </div>
                    <div style={{ fontSize: 18, color: 'rgba(255,255,255,0.9)' }}>
                      综合相似度分数
                    </div>
                  </div>
                </div>
              ) : (
                <Alert
                  message="⏳ 正在计算 AI 相似度..."
                  description="图片生成完成后会自动计算，请稍候刷新页面"
                  type="info"
                  showIcon
                />
              )}
            </div>
          </>
        )}

        {!latestVersion.is_final && !isProcessing && (
          <>
          <Divider />
{}
            <div>
              <h3>
                您对图片相似度的评价
                <span style={{ color: '#ff4d4f', marginLeft: 8 }}>*必填</span>
                {hasManualScoreSaved && (
                  <span style={{
                    marginLeft: 12,
                    fontSize: 14,
                    color: '#52c41a',
                    background: '#f6ffed',
                    padding: '2px 8px',
                    borderRadius: 4
                  }}>
                    ✓ 已保存
                  </span>
                )}
              </h3>

              <Alert
                message="评分说明"
                description={`⚠️ 每个版本都需要重新评估打分！请根据生成图与目标图的整体相似程度打分（1-100分）。评分会自动保存。

                      1-20: 几乎没有关系的两个图
                      21-40: 有一定相关性但不多
                      41-60: 拙劣的模仿但是有模有样
                      61-80: 大体上很相近但不缺乏瑕疵
                      81-100: 靠近完美的相似
                      `}
                type="warning"
                showIcon
                style={{ marginBottom: 20, whiteSpace: "pre-line" }}
              />

              <div style={{ marginBottom: 30 }}>
                <div style={{
                  marginBottom: 20,
                  textAlign: 'center',
                  padding: '20px',
                  background: manualScore === 0 ? '#e8e8e8' :
                              manualScore <= 20 ? '#F9ED69' :
                              manualScore <= 40 ? '#FFD93D' :
                              manualScore <= 60 ? '#FFA07A' :
                              manualScore <= 80 ? '#FF6B6B' : '#DC143C',
                  borderRadius: 12,
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                }}>
                  <div style={{ fontSize: 48, fontWeight: 'bold', color: '#6392f1ff', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>
                    {manualScore}
                  </div>
                  <div style={{ fontSize: 16, color: '#030303ff', marginTop: 5 }}>
                    {manualScore === 0 ? '请拖动滑钮评价生成图与目标图相似度～' :
                     manualScore < 20 ? '《几乎没有关系的两个图》' :
                     manualScore < 40 ? '《有一定相关性但不多》' :
                     manualScore < 60 ? '《拙劣的模仿但是有模有样》' :
                     manualScore < 80 ? '《大体上很相近但不缺乏瑕疵》' : '《靠近完美的相似》'
                     }
                  </div>
                </div>

                <style>{`
                  .candy-slider .ant-slider-handle::before {
                    content: none !important;
                  }
                  .candy-slider .ant-slider-handle::after {
                    content: none !important;
                  }
                `}</style>

                <Slider
                  className="candy-slider"
                  min={0}
                  max={100}
                  value={manualScore}
                  disabled={latestVersion?.is_final}
                  onChange={(value) => {
                    setManualScore(value)
                    setHasManualScoreSaved(false)
                  }}
                  marks={{
                    0: { style: { color: '#999' }, label: '0' },
                    20: '20',
                    40: '40',
                    60: '60',
                    80: '80',
                    100: { style: { color: '#DC143C' }, label: '100' }
                  }}
                  tooltip={{
                    formatter: (value) => `${value} 分`
                  }}
                  trackStyle={{
                    background: `linear-gradient(90deg,
                      #F9ED69 0%,
                      #FFD93D 25%,
                      #FFA07A 50%,
                      #FF6B6B 75%,
                      #DC143C 100%)`,
                    height: 8,
                    borderRadius: 4
                  }}
                  handleStyle={{
                    border: 'none',
                    backgroundColor: manualScore === 0 ? '#999' :
                                     manualScore <= 20 ? '#F9ED69' :
                                     manualScore <= 40 ? '#FFD93D' :
                                     manualScore <= 60 ? '#FFA07A' :
                                     manualScore <= 80 ? '#FF6B6B' : '#DC143C',
                    width: 24,
                    height: 24,
                    borderRadius: 6,
                    marginTop: -8,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                    cursor: 'grab'
                  }}
                  railStyle={{
                    height: 8,
                    backgroundColor: '#f0f0f0',
                    borderRadius: 4
                  }}
                  style={{ marginBottom: 10 }}
                />

              </div>
            </div>

           <Divider />

            {}
            <div>
              <h3>图片细节评价</h3>

              <style>{`

                .style-rate .ant-rate-star {
                  color: #D3E4F0 !important;
                }
                .style-rate .ant-rate-star-full {
                  color: #5B8DBE !important;
                }

                .object-rate .ant-rate-star {
                  color: #D8E5D0 !important;
                }
                .object-rate .ant-rate-star-full {
                  color: #6A8759 !important;
                }

                .perspective-rate .ant-rate-star {
                  color: #F5D5D8 !important;
                }
                .perspective-rate .ant-rate-star-full {
                  color: #C93756 !important;
                }

                .depth-rate .ant-rate-star {
                  color: #FFF1D0 !important;
                }
                .depth-rate .ant-rate-star-full {
                  color: #FAAD14 !important;
                }
              `}</style>

              <Row gutter={24}>
                {}
                <Col span={12}>
                  <Alert
                    message="评分说明"
                    description={`请对生成图与目标图在以下四个维度的符合程度进行评分（0-7星）：

                        0星: 未评分
                        1星: 完全不符 - 严重偏离目标
                        2星: 很不符 - 明显差异
                        3星: 不太符 - 有较大差异
                        4星: 基本符合 - 可接受但有改进空间
                        5星: 较符合 - 比较接近目标
                        6星: 很符合 - 非常接近目标
                        7星: 完全符合 - 几乎一模一样

                        需要点击保存按钮来提交打分与文字评价。
                        `}
                    type="info"
                    showIcon
                    style={{ marginBottom: 20, whiteSpace: "pre-line" }}
                  />
                </Col>

                {}
                <Col span={12}>
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <div>
                      <div style={{ marginBottom: 8, fontWeight: 500 }}>
                        <Tooltip title="生成图与目标图的整体画风、艺术风格的一致性">
                          1. 画风风格 ⓘ
                        </Tooltip>
                      </div>
                      <Rate
                        className="style-rate"
                        count={7}
                        value={styleScore}
                        disabled={latestVersion?.is_final}
                        onChange={setStyleScore}
                        style={{ fontSize: 28 }}
                        allowClear
                      />
                      <span style={{ marginLeft: 15, color: '#5B8DBE', fontWeight: 500 }}>
                        {styleScore === 0 ? '未评分' : `${styleScore} 星`}
                      </span>
                    </div>

                    <div>
                      <div style={{ marginBottom: 8, fontWeight: 500 }}>
                        <Tooltip title="生成图中物体的种类和数量与目标图的符合程度">
                          2. 物件数量 ⓘ
                        </Tooltip>
                      </div>
                      <Rate
                        className="object-rate"
                        count={7}
                        value={objectCountScore}
                        disabled={latestVersion?.is_final}
                        onChange={setObjectCountScore}
                        style={{ fontSize: 28 }}
                        allowClear
                      />
                      <span style={{ marginLeft: 15, color: '#6A8759', fontWeight: 500 }}>
                        {objectCountScore === 0 ? '未评分' : `${objectCountScore} 星`}
                      </span>
                    </div>

                    <div>
                      <div style={{ marginBottom: 8, fontWeight: 500 }}>
                        <Tooltip title="生成图的视角、拍摄角度与目标图的符合程度">
                          3. 视角构图 ⓘ
                        </Tooltip>
                      </div>
                      <Rate
                        className="perspective-rate"
                        count={7}
                        value={perspectiveScore}
                        disabled={latestVersion?.is_final}
                        onChange={setPerspectiveScore}
                        style={{ fontSize: 28 }}
                        allowClear
                      />
                      <span style={{ marginLeft: 15, color: '#C93756', fontWeight: 500 }}>
                        {perspectiveScore === 0 ? '未评分' : `${perspectiveScore} 星`}
                      </span>
                    </div>

                    <div>
                      <div style={{ marginBottom: 8, fontWeight: 500 }}>
                        <Tooltip title="生成图的景深效果、背景细节与目标图的符合程度">
                          4. 景深背景 ⓘ
                        </Tooltip>
                      </div>
                      <Rate
                        className="depth-rate"
                        count={7}
                        value={depthBackgroundScore}
                        disabled={latestVersion?.is_final}
                        onChange={setDepthBackgroundScore}
                        style={{ fontSize: 28 }}
                        allowClear
                      />
                      <span style={{ marginLeft: 15, color: '#FAAD14', fontWeight: 500 }}>
                        {depthBackgroundScore === 0 ? '未评分' : `${depthBackgroundScore} 星`}
                      </span>
                    </div>
                  </Space>
                </Col>
              </Row>

              {}
              <div style={{ marginTop: 20 }}>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>文字评价</div>
                <TextArea
                  rows={3}
                  value={detailedReview}
                  onChange={(e) => setDetailedReview(e.target.value)}
                  placeholder="可以详细描述生成图与目标图的差异..."
                />
              </div>

              <Button
                type="primary"
                onClick={handleRate}
                loading={rating}
                disabled={latestVersion?.is_final}
                size="large"
                style={{ marginTop: 16 }}
              >
                {latestVersion?.is_final ? '已标记最终版本（不可修改评分）' : '保存图片细节评价'}
              </Button>
            </div>

        <Divider />
          {!latestVersion.is_final && !isProcessing && (
  <>
    <Divider />
    <div style={{ marginBottom: 24 }}>
      <h3 style={{
        marginBottom: 16,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        fontWeight: 'bold',
        fontSize: 18
      }}>
        ✨ AI 提示词优化建议
      </h3>

      {wiseLoading && (
        <div style={{
          padding: 40,
          textAlign: 'center',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          borderRadius: 12,
          border: '1px solid rgba(102, 126, 234, 0.3)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `
              radial-gradient(2px 2px at 20% 30%, white, transparent),
              radial-gradient(2px 2px at 60% 70%, white, transparent),
              radial-gradient(1px 1px at 50% 50%, white, transparent),
              radial-gradient(1px 1px at 80% 10%, white, transparent),
              radial-gradient(2px 2px at 90% 60%, white, transparent),
              radial-gradient(1px 1px at 33% 80%, white, transparent)
            `,
            backgroundSize: '200% 200%',
            animation: 'twinkle 4s ease-in-out infinite',
            opacity: 0.6
          }} />

          <style>{`
            @keyframes twinkle {
              0%, 100% { opacity: 0.3; }
              50% { opacity: 0.8; }
            }
            @keyframes shimmer {
              0% { background-position: -200% center; }
              100% { background-position: 200% center; }
            }
            @keyframes float {
              0%, 100% { transform: translateY(0px); }
              50% { transform: translateY(-10px); }
            }
          `}</style>

          <div style={{ position: 'relative', zIndex: 1 }}>
            <Spin size="large" />
            <div style={{
              marginTop: 16,
              color: '#a8b3ff',
              fontSize: 15,
              fontWeight: 500
            }}>
              AI 正在分析您的提示词...
            </div>
          </div>
        </div>
      )}

      {wiseError && (
        <Alert
          message="AI 分析失败"
          description={wiseError}
          type="warning"
          showIcon
          closable
          style={{
            background: 'linear-gradient(135deg, #2d1b3d 0%, #1f1528 100%)',
            border: '1px solid #ff4d4f',
            color: '#ff7875'
          }}
        />
      )}

      {!wiseLoading && !wiseError && wiseSuggestions && wiseSuggestions.length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
          borderRadius: 16,
          padding: 24,
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
        }}>
          {}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `
              radial-gradient(2px 2px at 10% 20%, rgba(255,255,255,0.8), transparent),
              radial-gradient(2px 2px at 70% 40%, rgba(255,255,255,0.6), transparent),
              radial-gradient(1px 1px at 30% 60%, rgba(255,255,255,0.9), transparent),
              radial-gradient(1px 1px at 50% 80%, rgba(255,255,255,0.7), transparent),
              radial-gradient(2px 2px at 90% 30%, rgba(255,255,255,0.5), transparent),
              radial-gradient(1px 1px at 80% 70%, rgba(255,255,255,0.8), transparent),
              radial-gradient(1px 1px at 20% 90%, rgba(255,255,255,0.6), transparent),
              radial-gradient(2px 2px at 60% 10%, rgba(255,255,255,0.7), transparent)
            `,
            backgroundSize: '100% 100%',
            animation: 'twinkle 3s ease-in-out infinite',
            pointerEvents: 'none'
          }} />

          {}
          <div style={{
            marginBottom: 20,
            position: 'relative',
            zIndex: 1
          }}>
            <div style={{
              background: 'linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #ff9ff3, #54a0ff, #ff6b6b)',
              backgroundSize: '200% auto',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'shimmer 3s linear infinite',
              fontSize: 16,
              fontWeight: 'bold',
              display: 'inline-block'
            }}>
              💡 AI 智能建议
            </div>
          </div>

          <Space direction="vertical" size={16} style={{ width: '100%', position: 'relative', zIndex: 1 }}>
            {wiseSuggestions.map((sug, index) => (
              <div
                key={index}
                style={{
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: 12,
                  padding: '16px 20px',
                  border: '2px solid rgba(102, 126, 234, 0.4)',
                  boxShadow: '0 4px 20px rgba(102, 126, 234, 0.3), inset 0 1px 0 rgba(255,255,255,0.1)',
                  position: 'relative',
                  overflow: 'hidden',
                  transition: 'all 0.3s ease',
                  cursor: 'default',
                  animation: `float 3s ease-in-out infinite ${index * 0.2}s`
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 30px rgba(102, 126, 234, 0.5), inset 0 1px 0 rgba(255,255,255,0.2)';
                  e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.25) 0%, rgba(118, 75, 162, 0.25) 100%)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.3), inset 0 1px 0 rgba(255,255,255,0.1)';
                  e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)';
                }}
              >
                {}
                <div style={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: 4,
                  background: 'linear-gradient(180deg, #667eea 0%, #764ba2 100%)'
                }} />

                {}
                <div style={{
                  color: '#e8eaf6',
                  fontSize: 15,
                  lineHeight: 1.8,
                  paddingLeft: 12,
                  fontWeight: 500,
                  textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                }}>
                  {sug.suggestion}
                </div>

                {sug.example && (
                  <div style={{
                    marginTop: 12,
                    paddingLeft: 12,
                    paddingTop: 12,
                    borderTop: '1px solid rgba(255,255,255,0.1)',
                    color: '#b0bec5',
                    fontSize: 13,
                    fontStyle: 'italic',
                    lineHeight: 1.6
                  }}>
                    💬 {sug.example}
                  </div>
                )}

                {}
                <div style={{
                  position: 'absolute',
                  top: -50,
                  right: -50,
                  width: 100,
                  height: 100,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '50%',
                  filter: 'blur(40px)',
                  opacity: 0.15,
                  pointerEvents: 'none'
                }} />
              </div>
            ))}
          </Space>

          {}
          <div style={{
            marginTop: 24,
            padding: '14px 18px',
            background: 'rgba(102, 126, 234, 0.15)',
            borderRadius: 10,
            border: '1px solid rgba(102, 126, 234, 0.3)',
            position: 'relative',
            zIndex: 1
          }}>
            <div style={{
              color: '#a8b3ff',
              fontSize: 14,
              lineHeight: 1.6,
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              <span style={{
                fontSize: 18,
                animation: 'float 2s ease-in-out infinite'
              }}>💡</span>
              <span>参考以上建议优化您的提示词，生成更精准的图像</span>
            </div>
          </div>
        </div>
      )}

      {!wiseLoading && !wiseError && (!wiseSuggestions || wiseSuggestions.length === 0) && (
        <div style={{
          padding: 32,
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
          borderRadius: 12,
          textAlign: 'center',
          border: '1px solid rgba(102, 126, 234, 0.2)'
        }}>
          <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.6 }}>🎉</div>
          <div style={{ color: '#a8b3ff', fontSize: 15 }}>
            当前提示词质量不错，暂无优化建议
          </div>
        </div>
      )}
    </div>
  </>
)}
            {}
            {canModify && (
              <div>
                <h3>
                  修改提示词（版本 {task.versions.length + 1}/{MAX_VERSIONS_PER_TASK}）
                  <span style={{ color: '#ff4d4f', marginLeft: 8 }}>*必填</span>
                </h3>
                <TextArea
                  rows={6}
                  value={modifyPrompt}
                  onChange={(e) => {
                    setModifyPrompt(e.target.value)
                    if (!modifyStartTime) {
                      setModifyStartTime(Date.now())
                    }
                  }}
                  placeholder="输入新的提示词..."
                  style={{ marginBottom: 16 }}
                />

                {}
                <div style={{ display: 'flex', gap: 16, marginBottom: 10 }}>
                  <Button
                    type="primary"
                    size="large"
                    onClick={handleModify}
                    loading={modifying}
                    disabled={
                      !latestVersion.user_manual_score ||
                      latestVersion.user_manual_score === 0 ||
                      !latestVersion.rating ||
                      latestVersion.rating.style_score === 0 ||
                      latestVersion.rating.object_count_score === 0 ||
                      latestVersion.rating.perspective_score === 0 ||
                      latestVersion.rating.depth_background_score === 0 ||
                      !modifyPrompt.trim()
                    }
                    style={{ flex: 1 }}
                  >
                    {modifying ? '生成中...' : '生成新版本'}
                  </Button>

                  <Button
                    type="primary"
                    size="large"
                    onClick={handleFinalize}
                    disabled={
                      !latestVersion.user_manual_score ||
                      latestVersion.user_manual_score === 0 ||
                      !latestVersion.rating ||
                      latestVersion.rating.style_score === 0 ||
                      latestVersion.rating.object_count_score === 0 ||
                      latestVersion.rating.perspective_score === 0 ||
                      latestVersion.rating.depth_background_score === 0
                    }
                    style={{
                      flex: 1,
                      background: '#8b0000',
                      borderColor: '#8b0000'
                    }}
                    onMouseEnter={(e) => {
                      if (!e.currentTarget.disabled) {
                        e.currentTarget.style.background = '#a52a2a'
                        e.currentTarget.style.borderColor = '#a52a2a'
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!e.currentTarget.disabled) {
                        e.currentTarget.style.background = '#8b0000'
                        e.currentTarget.style.borderColor = '#8b0000'
                      }
                    }}
                  >
                    标记为最终版本
                  </Button>
                </div>

                {(!latestVersion.user_manual_score ||
                  latestVersion.user_manual_score === 0 ||
                  !latestVersion.rating ||
                  latestVersion.rating.style_score === 0 ||
                  latestVersion.rating.object_count_score === 0 ||
                  latestVersion.rating.perspective_score === 0 ||
                  latestVersion.rating.depth_background_score === 0) && (
                  <div style={{ color: '#ff4d4f', fontSize: 14 }}>
                    ⚠️ 请先完成相似度评分与所有维度的星级评分
                  </div>
                )}
              </div>
            )}

            {!canModify && (
              <>
                <Alert
                  message="已达到最大版本数"
                  description={`当前已有 ${task.versions.length} 个版本，已达到上限。请标记为最终版本完成任务。`}
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                {}
                {!latestVersion.is_final && (
                  <div>
                    <Button
                      type="primary"
                      size="large"
                      onClick={handleFinalize}
                      disabled={
                        !latestVersion.user_manual_score ||
                        latestVersion.user_manual_score === 0 ||
                        !latestVersion.rating ||
                        latestVersion.rating.style_score === 0 ||
                        latestVersion.rating.object_count_score === 0 ||
                        latestVersion.rating.perspective_score === 0 ||
                        latestVersion.rating.depth_background_score === 0
                      }
                      block
                      style={{
                        background: '#8b0000',
                        borderColor: '#8b0000'
                      }}
                      onMouseEnter={(e) => {
                        if (!e.currentTarget.disabled) {
                          e.currentTarget.style.background = '#a52a2a'
                          e.currentTarget.style.borderColor = '#a52a2a'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!e.currentTarget.disabled) {
                          e.currentTarget.style.background = '#8b0000'
                          e.currentTarget.style.borderColor = '#8b0000'
                        }
                      }}
                    >
                      ✓ 标记为最终版本（完成此任务）
                    </Button>

                    {(!latestVersion.user_manual_score ||
                      latestVersion.user_manual_score === 0 ||
                      !latestVersion.rating ||
                      latestVersion.rating.style_score === 0 ||
                      latestVersion.rating.object_count_score === 0 ||
                      latestVersion.rating.perspective_score === 0 ||
                      latestVersion.rating.depth_background_score === 0) && (
                      <div style={{
                        marginTop: 12,
                        padding: 12,
                        background: '#fff7e6',
                        border: '1px solid #ffd591',
                        borderRadius: 4,
                        color: '#d46b08',
                        fontSize: 13
                      }}>
                        ⚠️ 请先完成相似度评分（拖动滑轮）和所有维度的星级评分，才能标记为最终版本
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {latestVersion.is_final && (
              <Alert
                message="已标记为最终版本"
                description="此任务已完成，无法继续修改。"
                type="success"
                showIcon
              />
            )}
          </>
        )}
      </Card>
              </>
      )}
    </div>
  )
}
