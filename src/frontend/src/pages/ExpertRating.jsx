import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API_BASE_URL = ''

function ExpertRating() {
  const navigate = useNavigate()
  const [currentUser, setCurrentUser] = useState(null)
  const [targets, setTargets] = useState([])
  const [selectedTarget, setSelectedTarget] = useState(null)
  const [generatedImages, setGeneratedImages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expertNumber, setExpertNumber] = useState(null)
  const [savingScores, setSavingScores] = useState({})
  const [localScores, setLocalScores] = useState({})
  const [saveTimers, setSaveTimers] = useState({})

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')

    if (!token || !userStr) {
      navigate('/login')
      return
    }

    try {
      const user = JSON.parse(userStr)
      setCurrentUser(user)

      const username = user.username.toLowerCase()
      if (username.includes('expert1') || username.includes('专家1')) {
        setExpertNumber(1)
      } else if (username.includes('expert2') || username.includes('专家2')) {
        setExpertNumber(2)
      } else {

        setExpertNumber(1)
      }
    } catch (err) {
      console.error('解析用户信息失败:', err)
      navigate('/login')
    }
  }, [navigate])

  useEffect(() => {
    if (!currentUser) return

    const loadTargets = async () => {
      try {
        setLoading(true)
        const token = localStorage.getItem('token')
        const response = await axios.get(
          `${API_BASE_URL}/api/expert-rating/targets`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        setTargets(response.data.targets)
        setError(null)
      } catch (err) {
        console.error('加载目标图失败:', err)
        setError('加载目标图失败: ' + (err.response?.data?.detail || err.message))
      } finally {
        setLoading(false)
      }
    }

    loadTargets()
  }, [currentUser])

  const loadGeneratedImages = async (targetIndex) => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await axios.get(
        `${API_BASE_URL}/api/expert-rating/targets/${targetIndex}/images`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      console.log('✅ API响应数据:', response.data)
      console.log('✅ 生成图数量:', response.data.generated_images?.length)

      if (response.data.generated_images && response.data.generated_images.length > 0) {
        console.log('✅ 第一张图数据示例:', response.data.generated_images[0])
        console.log('✅ 第一张图URL:', response.data.generated_images[0]?.image_url)
      }

      setSelectedTarget(response.data)

      const images = response.data.generated_images
      const shuffledImages = [...images].sort(() => Math.random() - 0.5)

      console.log(`✅ 已随机打乱 ${shuffledImages.length} 张生成图的顺序`)
      setGeneratedImages(shuffledImages)
      setError(null)
    } catch (err) {
      console.error('加载生成图失败:', err)
      setError('加载生成图失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleTargetClick = (target) => {
    loadGeneratedImages(target.target_index)
  }

  const handleBackToTargets = () => {
    setSelectedTarget(null)
    setGeneratedImages([])
  }

  const handleScoreChange = (versionId, score) => {

    setLocalScores(prev => ({ ...prev, [versionId]: score }))

    if (saveTimers[versionId]) {
      clearTimeout(saveTimers[versionId])
    }

    const timer = setTimeout(async () => {
      try {

        setSavingScores(prev => ({ ...prev, [versionId]: true }))

        const token = localStorage.getItem('token')
        await axios.post(
          `${API_BASE_URL}/api/versions/${versionId}/expert-score`,
          {
            expert_number: expertNumber,
            score: score
          },
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )

        setGeneratedImages(prev =>
          prev.map(img =>
            img.version_id === versionId
              ? {
                  ...img,
                  [expertNumber === 1 ? 'expert_score_1' : 'expert_score_2']: score
                }
              : img
          )
        )

        setSavingScores(prev => {
          const newState = { ...prev }
          delete newState[versionId]
          return newState
        })

        console.log(`✅ 已保存评分: ${score}`)
      } catch (err) {
        console.error('更新评分失败:', err)
        alert('更新评分失败: ' + (err.response?.data?.detail || err.message))

        const originalScore = generatedImages.find(img => img.version_id === versionId)?.[expertNumber === 1 ? 'expert_score_1' : 'expert_score_2']
        setLocalScores(prev => ({ ...prev, [versionId]: originalScore || 0 }))

        setSavingScores(prev => {
          const newState = { ...prev }
          delete newState[versionId]
          return newState
        })
      }
    }, 800)

    setSaveTimers(prev => ({ ...prev, [versionId]: timer }))
  }

  useEffect(() => {
    return () => {
      Object.values(saveTimers).forEach(timer => clearTimeout(timer))
    }
  }, [saveTimers])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  if (loading && !selectedTarget) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>加载中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>重试</button>
      </div>
    )
  }

  if (!selectedTarget) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          borderBottom: '2px solid #333',
          paddingBottom: '10px'
        }}>
          <h1>专家评分系统</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <span style={{
              padding: '8px 15px',
              backgroundColor: expertNumber === 1 ? '#4CAF50' : '#2196F3',
              color: 'white',
              borderRadius: '5px',
              fontWeight: 'bold'
            }}>
              专家{expertNumber}: {currentUser?.username}
            </span>
            <button
              onClick={handleLogout}
              style={{
                padding: '8px 15px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              退出登录
            </button>
          </div>
        </div>

        <h2>请选择一个目标图</h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
          gap: '20px',
          marginTop: '20px'
        }}>
          {targets.map(target => (
            <div
              key={target.target_index}
              onClick={() => handleTargetClick(target)}
              style={{
                border: '2px solid #ddd',
                borderRadius: '8px',
                padding: '10px',
                cursor: 'pointer',
                transition: 'all 0.3s',
                backgroundColor: 'white'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.05)'
                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              <img
                src={`${API_BASE_URL}${target.target_image_url}`}
                alt={target.target_filename}
                style={{
                  width: '100%',
                  height: '250px',
                  objectFit: 'cover',
                  borderRadius: '5px'
                }}
              />
              <div style={{ marginTop: '10px', textAlign: 'center' }}>
                <strong>目标图 #{target.target_index}</strong>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                  {target.difficulty && `难度: ${target.difficulty}`}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        borderBottom: '2px solid #333',
        paddingBottom: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <button
            onClick={handleBackToTargets}
            style={{
              padding: '8px 15px',
              backgroundColor: '#666',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            ← 返回目标图列表
          </button>
          <h2>目标图 #{selectedTarget.target_index} 的生成图评分</h2>
        </div>
        <span style={{
          padding: '8px 15px',
          backgroundColor: expertNumber === 1 ? '#4CAF50' : '#2196F3',
          color: 'white',
          borderRadius: '5px',
          fontWeight: 'bold'
        }}>
          专家{expertNumber}: {currentUser?.username}
        </span>
      </div>

      {}
      <div style={{
        position: 'sticky',
        top: '20px',
        zIndex: 100,
        backgroundColor: '#f5f5f5',
        padding: '15px',
        borderRadius: '8px',
        border: '2px solid #333',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 15px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>目标图</span>
          <span style={{
            fontSize: '14px',
            fontWeight: 'normal',
            color: '#666',
            backgroundColor: 'white',
            padding: '4px 12px',
            borderRadius: '4px'
          }}>
            {selectedTarget.target_filename}
          </span>
        </h3>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <img
            src={`${API_BASE_URL}${selectedTarget.target_image_url}`}
            alt="目标图"
            style={{
              maxWidth: '400px',
              maxHeight: '400px',
              objectFit: 'contain',
              borderRadius: '8px',
              border: '3px solid #333',
              backgroundColor: 'white'
            }}
          />
        </div>
      </div>

      {}
      <h3>生成图列表 (共 {generatedImages.length} 张)</h3>
      {generatedImages.length === 0 ? (
        <p style={{ color: '#666', textAlign: 'center', marginTop: '40px' }}>
          该目标图还没有生成图
        </p>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '20px',
          marginTop: '20px'
        }}>
          {generatedImages.map((image, index) => {

            const dbScore = expertNumber === 1 ? image.expert_score_1 : image.expert_score_2
            const displayScore = localScores[image.version_id] !== undefined
              ? localScores[image.version_id]
              : (dbScore || 0)
            const isSaving = savingScores[image.version_id]

            return (
              <div
                key={image.version_id}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '15px',
                  backgroundColor: 'white',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '15px'
                }}
              >
                {}
                <div style={{ width: '100%' }}>
                  <img
                    src={`${API_BASE_URL}${image.image_url}`}
                    alt="生成图"
                    style={{
                      width: '100%',
                      height: '220px',
                      objectFit: 'cover',
                      borderRadius: '5px',
                      border: '2px solid #ddd'
                    }}
                  />
                </div>

                {}
                <div style={{ width: '100%' }}>
                  {}
                  <div style={{
                    backgroundColor: expertNumber === 1 ? '#e8f5e9' : '#e3f2fd',
                    padding: '15px',
                    borderRadius: '8px',
                    border: `2px solid ${expertNumber === 1 ? '#4CAF50' : '#2196F3'}`
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '10px'
                    }}>
                      <strong style={{ color: expertNumber === 1 ? '#2e7d32' : '#1565c0' }}>
                        专家{expertNumber}评分:
                      </strong>
                      <span style={{
                        fontSize: '24px',
                        fontWeight: 'bold',
                        color: expertNumber === 1 ? '#2e7d32' : '#1565c0',
                        minWidth: '60px',
                        textAlign: 'right'
                      }}>
                        {displayScore}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={displayScore}
                      onChange={(e) => handleScoreChange(image.version_id, parseInt(e.target.value))}
                      disabled={isSaving}
                      style={{
                        width: '100%',
                        height: '8px',
                        cursor: isSaving ? 'not-allowed' : 'pointer',
                        opacity: isSaving ? 0.5 : 1
                      }}
                    />
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '12px',
                      color: '#666',
                      marginTop: '5px'
                    }}>
                      <span>0</span>
                      <span>50</span>
                      <span>100</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default ExpertRating
