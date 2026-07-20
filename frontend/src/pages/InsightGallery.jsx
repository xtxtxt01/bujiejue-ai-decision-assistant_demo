import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Lightbulb, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getInsights } from '../api';

const TYPE_LABELS = {
  career: '职业', relationship: '关系', lifestyle: '生活',
  finance: '财务', growth: '成长', education: '学业',
};

const TYPE_EMOJI = {
  career: '💼', relationship: '❤️', lifestyle: '🌱',
  finance: '💰', growth: '🚀', education: '📚',
};

const WORRY_LABELS = {
  rational: '理性担忧',
  emotional: '情绪担忧',
  mixed: '理性+情绪',
};

export default function InsightGallery() {
  const navigate = useNavigate();
  const uid = localStorage.getItem('uid');
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (!uid) { navigate('/'); return; }
    load();
  }, []);

  const load = async () => {
    try {
      const data = await getInsights(uid);
      setInsights(data.insights || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const formatMonth = (t) => {
    if (!t) return '';
    const d = new Date(t);
    return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}`;
  };

  return (
    <div className="page">
      {/* 顶栏 */}
      <div className="navbar">
        <button className="navbar-btn" onClick={() => navigate('/home')}>
          <ArrowLeft size={20} />
        </button>
        <div style={{ flex: 1, textAlign: 'center', fontWeight: 600, fontSize: 16 }}>
          我的洞察
        </div>
        <div style={{ width: 36 }} />
      </div>

      {/* 成就感统计条 */}
      {!loading && insights.length > 0 && (
        <div style={{
          padding: '14px 20px',
          display: 'flex', alignItems: 'center', gap: 10,
          background: 'var(--accent-light)',
          margin: '12px 16px 4px', borderRadius: 'var(--radius-md)',
        }}>
          <Lightbulb size={20} style={{ color: 'var(--accent)' }} />
          <span style={{ fontSize: 14, color: 'var(--text-primary)' }}>
            你已经积累了 <strong style={{ color: 'var(--accent)' }}>{insights.length}</strong> 张决策洞察
          </span>
        </div>
      )}

      {/* 内容区 */}
      <div className="scroll-area">
        {loading ? (
          <div className="empty-state"><p style={{ color: 'var(--text-muted)' }}>加载中...</p></div>
        ) : insights.length === 0 ? (
          <div className="empty-state">
            <div className="icon">💡</div>
            <h3>还没有洞察</h3>
            <p>完成一次纠结决策后，系统会自动生成洞察卡片</p>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 10,
            padding: '8px 0',
          }}>
            {insights.map((item, i) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                onClick={() => setSelected(item)}
                style={{
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px',
                  cursor: 'pointer',
                  display: 'flex', flexDirection: 'column', gap: 8,
                  minHeight: 130,
                }}
              >
                <div style={{ fontSize: 22 }}>{TYPE_EMOJI[item.dilemma_type] || '🤔'}</div>
                <div style={{
                  fontSize: 13, fontWeight: 600, color: 'var(--text-primary)',
                  lineHeight: 1.4,
                  display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}>
                  {item.insight.core_conflict || item.title || '决策洞察'}
                </div>
                {item.insight.value_signals?.[0] && (
                  <div style={{
                    fontSize: 11, color: 'var(--accent)',
                    background: 'var(--accent-light)',
                    padding: '2px 8px', borderRadius: 8, alignSelf: 'flex-start',
                  }}>
                    {item.insight.value_signals[0]}
                  </div>
                )}
                <div style={{
                  marginTop: 'auto', fontSize: 11, color: 'var(--text-muted)',
                  display: 'flex', justifyContent: 'space-between',
                }}>
                  <span>{TYPE_LABELS[item.dilemma_type] || ''}</span>
                  <span>{formatMonth(item.closed_at || item.updated_at)} · {item.duration_days}天</span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* 详情弹窗 */}
      <AnimatePresence>
        {selected && (
          <>
            <motion.div
              className="modal-overlay"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setSelected(null)}
            />
            <motion.div
              className="modal-sheet"
              initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            >
              <div className="modal-handle" />
              {selected && (
                <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                  {/* 标题区 */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                    <div style={{ fontSize: 28 }}>{TYPE_EMOJI[selected.dilemma_type] || '🤔'}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 16, fontWeight: 700, lineHeight: 1.3 }}>
                        {selected.title || '决策洞察'}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                        {formatMonth(selected.closed_at || selected.updated_at)} · 纠结 {selected.duration_days} 天
                      </div>
                    </div>
                    <button className="navbar-btn" onClick={() => setSelected(null)}>
                      <X size={18} />
                    </button>
                  </div>

                  {/* 核心矛盾 */}
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>核心矛盾</div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                      {selected.insight.core_conflict || '—'}
                    </div>
                  </div>

                  {/* 价值观信号 */}
                  {selected.insight.value_signals?.length > 0 && (
                    <div style={{ marginBottom: 14 }}>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>价值观信号</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {selected.insight.value_signals.map((s, i) => (
                          <span key={i} style={{
                            fontSize: 13, color: 'var(--accent)', background: 'var(--accent-light)',
                            padding: '4px 12px', borderRadius: 12,
                          }}>{s}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 担忧分析 */}
                  {selected.insight.worry_analysis && (
                    <div style={{ marginBottom: 14 }}>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>
                        担忧分析 {selected.insight.worry_type && `· ${WORRY_LABELS[selected.insight.worry_type] || ''}`}
                      </div>
                      <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>
                        {selected.insight.worry_analysis}
                      </div>
                    </div>
                  )}

                  {/* 行动建议 */}
                  {selected.insight.action_suggestion && (
                    <div style={{
                      background: 'var(--accent-light)', borderRadius: 'var(--radius-md)',
                      padding: '12px 14px', marginBottom: 8,
                    }}>
                      <div style={{ fontSize: 12, color: 'var(--accent)', marginBottom: 4, fontWeight: 600 }}>
                        💪 行动建议
                      </div>
                      <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>
                        {selected.insight.action_suggestion}
                      </div>
                    </div>
                  )}

                  {/* 查看原对话 */}
                  <button
                    className="btn btn-ghost"
                    style={{ width: '100%', marginTop: 8, fontSize: 13 }}
                    onClick={() => navigate(`/card/${selected.id}`)}
                  >
                    查看完整对话
                  </button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

