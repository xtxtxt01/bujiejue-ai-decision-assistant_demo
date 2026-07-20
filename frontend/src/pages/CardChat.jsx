import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ChevronLeft, Send, MoreVertical, CheckCircle, Pause, Share2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getCardDetail, sendMessage, closeCard, reopenCard, shareCardPreview, shareCardConfirm, getCardRecommendations } from '../api';
import Toast from '../components/Toast';
import { useToast } from '../hooks/useToast';

export default function CardChat() {
  const { cardId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const uid = localStorage.getItem('uid');

  const [card, setCard] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [closeModal, setCloseModal] = useState(null); // null | 'decided' | 'shelved'
  const [decisionText, setDecisionText] = useState('');
  const [closing, setClosing] = useState(false);
  const [insightExpanded, setInsightExpanded] = useState(false);
  // 分享到社区流程：null | 'form'(填复盘) | 'preview'(编辑预览)
  const [shareStep, setShareStep] = useState(null);
  const [shareScore, setShareScore] = useState(8);
  const [shareText, setShareText] = useState('');
  const [sharePreview, setSharePreview] = useState(null);
  const [shareLoading, setShareLoading] = useState(false);
  const [shared, setShared] = useState(false);
  const [toast, showToast] = useToast();

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const relatedCaseShownRef = useRef(false);  // 本会话是否已展示过相似案例
  const [expandedRelatedIdx, setExpandedRelatedIdx] = useState(null);
  // 卡片详情页"看相似的人怎么选"区块
  const [recommendations, setRecommendations] = useState([]);
  const [recExpanded, setRecExpanded] = useState(false);
  const [recLoaded, setRecLoaded] = useState(false);
  const [recCardExpandedId, setRecCardExpandedId] = useState(null);

  useEffect(() => { loadCard(); }, [cardId]);
  useEffect(() => { scrollToBottom(); }, [messages, sending]);

  const loadCard = async () => {
    setLoading(true);
    try {
      const data = await getCardDetail(cardId);
      setCard(data.card);
      const msgs = data.messages || [];
      if (msgs.length === 0 && location.state?.firstMessage) {
        setMessages([
          { role: 'assistant', content: location.state.firstMessage, created_at: new Date().toISOString() },
        ]);
      } else {
        setMessages(msgs);
      }
    } catch (e) {
      showToast('加载失败，请返回重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text, created_at: new Date().toISOString() }]);
    setSending(true);

    try {
      const result = await sendMessage(cardId, uid, text);
      // 相似案例：每会话只展示一次
      let relatedCase = null;
      if (result.related_case && !relatedCaseShownRef.current) {
        relatedCase = result.related_case;
        relatedCaseShownRef.current = true;
      }
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.assistant_message,
        progress_hint: result.progress_hint,
        related_case: relatedCase,
        created_at: new Date().toISOString()
      }]);
      if (result.card_updated && result.card_info) {
        setCard(prev => ({ ...prev, ...result.card_info }));
      }
      if (result.card_closed) {
        setCard(prev => ({ ...prev, status: 'decided' }));
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: '抱歉，网络出了点问题，请重试。', created_at: new Date().toISOString() }]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const openCloseModal = (status) => {
    setDecisionText('');
    setCloseModal(status);
    setShowMenu(false);
  };

  const handleClose = async () => {
    if (closeModal === 'decided' && !decisionText.trim()) return;
    setClosing(true);
    try {
      await closeCard(cardId, uid, closeModal, decisionText.trim(), '');
      setCard(prev => ({ ...prev, status: closeModal }));
      setCloseModal(null);
    } catch (e) {
      showToast('操作失败，请重试', 'error');
    } finally {
      setClosing(false);
    }
  };

  const handleReopen = async () => {
    try {
      await reopenCard(cardId);
      setCard(prev => ({ ...prev, status: 'active' }));
    } catch (e) {
      showToast('重新打开失败：' + e.message, 'error');
    }
  };

  // 打开分享流程（填复盘表单）
  const openShare = () => {
    setShareScore(8);
    setShareText('');
    setSharePreview(null);
    setShareStep('form');
  };

  // 提交复盘 → 生成脱敏预览
  const handleSharePreview = async () => {
    if (!shareText.trim()) return;
    setShareLoading(true);
    try {
      const data = await shareCardPreview(cardId, shareScore, shareText.trim());
      setSharePreview(data.preview);
      setShareStep('preview');
    } catch (e) {
      showToast('生成预览失败：' + e.message, 'error');
    } finally {
      setShareLoading(false);
    }
  };

  // 确认发布
  const handleShareConfirm = async () => {
    setShareLoading(true);
    try {
      await shareCardConfirm(cardId, sharePreview);
      setShared(true);
      setShareStep(null);
      showToast('已分享到社区，谢谢你的经验', 'success');
    } catch (e) {
      showToast('发布失败：' + e.message, 'error');
    } finally {
      setShareLoading(false);
    }
  };

  // 编辑预览字段
  const updatePreview = (key, value) => {
    setSharePreview(prev => ({ ...prev, [key]: value }));
  };

  // 切换"看相似的人怎么选"区块（首次展开时按需加载）
  const toggleRecommendations = async () => {
    const next = !recExpanded;
    setRecExpanded(next);
    if (next && !recLoaded) {
      try {
        const data = await getCardRecommendations(cardId, 3);
        setRecommendations(data.cases || []);
      } catch (e) {
        // 静默失败，区块显示"暂无相似案例"
      } finally {
        setRecLoaded(true);
      }
    }
  };

  const autoResize = (e) => {
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
  };

  if (loading) {
    return (
      <div className="page">
        <div className="navbar">
          <button className="navbar-btn" onClick={() => navigate('/home')}><ChevronLeft size={20} /></button>
          <span className="navbar-title">加载中...</span>
          <div style={{ width: 36 }} />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <Toast toast={toast} />

      <div className="navbar">
        <button className="navbar-btn" onClick={() => navigate('/home')}>
          <ChevronLeft size={20} />
        </button>
        <span className="navbar-title" style={{ fontSize: 15 }}>
          {card?.title || '对话中'}
        </span>
        <div style={{ position: 'relative' }}>
          {card?.status === 'active' && (
            <button className="navbar-btn" onClick={() => setShowMenu(!showMenu)}>
              <MoreVertical size={18} />
            </button>
          )}
          {showMenu && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 99 }} onClick={() => setShowMenu(false)} />
              <div style={{
                position: 'absolute', right: 0, top: '100%', marginTop: 4,
                background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)', border: '1px solid var(--border)',
                overflow: 'hidden', zIndex: 100, minWidth: 150,
              }}>
                <button style={{
                  display: 'flex', alignItems: 'center', gap: 8, width: '100%',
                  padding: '12px 16px', background: 'none', border: 'none',
                  color: 'var(--success)', fontSize: 13, cursor: 'pointer',
                }} onClick={() => openCloseModal('decided')}>
                  <CheckCircle size={15} /> 我做了决定
                </button>
                <button style={{
                  display: 'flex', alignItems: 'center', gap: 8, width: '100%',
                  padding: '12px 16px', background: 'none', border: 'none',
                  color: 'var(--text-muted)', fontSize: 13, cursor: 'pointer',
                }} onClick={() => openCloseModal('shelved')}>
                  <Pause size={15} /> 先搁置
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {card?.core_conflict && (
        <div className="card-detail-header">
          <div className="detail-conflict">{card.core_conflict}</div>
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 && !sending && (
          <div className="empty-state" style={{ paddingTop: 40 }}>
            <div className="icon">💭</div>
            <p>说说你的纠结，我来帮你理清思路</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <motion.div key={i}
            className={`message ${msg.role}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}>
            <div className="message-bubble">{msg.content}</div>
            {msg.role === 'assistant' && msg.progress_hint && (
              <div className="progress-hint-card">
                <div className="hint-label">{msg.progress_hint.label}</div>
                {msg.progress_hint.tendency &&
                 msg.progress_hint.tendency.option_a !== null &&
                 msg.progress_hint.tendency.option_b !== null && (
                  <div className="tendency-bar-wrapper">
                    <div className="tendency-bar">
                      <div
                        className="tendency-fill-a"
                        style={{ width: `${msg.progress_hint.tendency.option_a}%` }}
                      />
                    </div>
                    <div className="tendency-labels">
                      <span className="tendency-label-a">
                        {msg.progress_hint.tendency.options?.[0] || '选项A'} {msg.progress_hint.tendency.option_a}%
                      </span>
                      <span className="tendency-label-b">
                        {msg.progress_hint.tendency.options?.[1] || '选项B'} {msg.progress_hint.tendency.option_b}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
            {msg.role === 'assistant' && msg.related_case && (
              <div
                onClick={() => setExpandedRelatedIdx(expandedRelatedIdx === i ? null : i)}
                style={{
                  marginTop: 8,
                  background: 'var(--accent-light)',
                  border: '1px solid var(--accent)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 14px',
                  cursor: 'pointer',
                  maxWidth: '85%',
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent)', marginBottom: 6 }}>
                  💡 跟你相似的人怎么选的
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                  {msg.related_case.background}
                </div>
                <div style={{ fontSize: 13, color: 'var(--accent)', marginTop: 4, fontWeight: 500 }}>
                  → {msg.related_case.final_choice}
                </div>
                {expandedRelatedIdx === i && (
                  <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border)' }}>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 6 }}>
                      <span style={{ color: 'var(--text-muted)' }}>转折点：</span>{msg.related_case.turning_point}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                      <span style={{ color: 'var(--text-muted)' }}>{msg.related_case.retrospect_months}个月后：</span>
                      {msg.related_case.retrospect}（满意度 {msg.related_case.retrospect_score}/10）
                    </div>
                  </div>
                )}
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                  {expandedRelatedIdx === i ? '收起 ▲' : '展开看 TA 的结果 ▼'}
                </div>
              </div>
            )}
          </motion.div>
        ))}
        {sending && (
          <div className="typing-indicator">
            <span /><span /><span />
          </div>
        )}

        {/* 看看相似的人怎么选的（纠结驱动推荐，需已聊出核心矛盾） */}
        {card?.core_conflict && (
          <div style={{
            margin: '8px 0',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            background: 'var(--bg-primary)',
          }}>
            <div
              onClick={toggleRecommendations}
              style={{
                padding: '12px 14px',
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                fontSize: 13, fontWeight: 600, color: 'var(--accent)',
              }}
            >
              <span>🔍 看看相似的人怎么选的</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {recExpanded ? '收起 ▲' : '展开 ▼'}
              </span>
            </div>

            {recExpanded && (
              <div style={{ padding: '0 14px 14px' }}>
                {!recLoaded ? (
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: '8px 0' }}>
                    加载中...
                  </p>
                ) : recommendations.length === 0 ? (
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', padding: '8px 0' }}>
                    暂时没有相似的案例
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {recommendations.map((c) => {
                      const exp = recCardExpandedId === c.id;
                      return (
                        <div
                          key={c.id}
                          onClick={() => setRecCardExpandedId(exp ? null : c.id)}
                          style={{
                            background: 'var(--bg-elevated)',
                            borderRadius: 'var(--radius-md)',
                            padding: '12px 14px',
                            cursor: 'pointer',
                          }}
                        >
                          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                            {c.core_conflict}
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, lineHeight: 1.5 }}>
                            {c.background}
                          </div>
                          <div style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 500 }}>
                            → {c.final_choice}
                          </div>
                          {exp && (
                            <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border)' }}>
                              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 6 }}>
                                <span style={{ color: 'var(--text-muted)' }}>转折点：</span>{c.turning_point}
                              </div>
                              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                <span style={{ color: 'var(--text-muted)' }}>{c.retrospect_months}个月后：</span>
                                {c.retrospect}（满意度 {c.retrospect_score}/10）
                              </div>
                            </div>
                          )}
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                            {exp ? '收起 ▲' : '展开看 TA 的结果 ▼'}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {card?.status === 'active' && (
        <div className="chat-input-area">
          <textarea
            ref={textareaRef}
            rows={1}
            placeholder="说说你的想法..."
            value={input}
            onChange={(e) => { setInput(e.target.value); autoResize(e); }}
            onKeyDown={handleKeyDown}
          />
          <button className="send-btn" onClick={handleSend} disabled={!input.trim() || sending}>
            <Send size={18} />
          </button>
        </div>
      )}

      {card?.status !== 'active' && (
        <div style={{
          padding: '16px 20px',
          background: 'var(--bg-elevated)',
          borderTop: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center',
        }}>
          {card?.insight && (() => {
            try {
              const insight = JSON.parse(card.insight);
              return (
                <div style={{
                  width: '100%',
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '14px',
                  marginBottom: 8,
                  cursor: 'pointer',
                }}
                onClick={() => setInsightExpanded(!insightExpanded)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>
                      💡 AI Insight
                    </div>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {insightExpanded ? '收起 ▲' : '展开 ▼'}
                    </span>
                  </div>

                  <div style={{ fontSize: 14, color: 'var(--text-primary)', marginTop: 8, lineHeight: 1.5 }}>
                    <strong style={{ color: 'var(--text-secondary)', fontSize: 12 }}>核心矛盾</strong><br />
                    {insight.core_conflict}
                  </div>

                  {insightExpanded && (
                    <>
                      {insight.value_signals?.length > 0 && (
                        <div style={{ fontSize: 14, color: 'var(--text-primary)', marginTop: 10, lineHeight: 1.5 }}>
                          <strong style={{ color: 'var(--text-secondary)', fontSize: 12 }}>价值观信号</strong><br />
                          {insight.value_signals.map((s, i) => (
                            <span key={i} style={{
                              display: 'inline-block',
                              background: 'var(--accent-light)',
                              color: 'var(--accent)',
                              padding: '3px 10px',
                              borderRadius: 12,
                              fontSize: 12,
                              marginRight: 6,
                              marginTop: 4,
                            }}>
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                      {insight.worry_analysis && (
                        <div style={{ fontSize: 14, color: 'var(--text-primary)', marginTop: 10, lineHeight: 1.5 }}>
                          <strong style={{ color: 'var(--text-secondary)', fontSize: 12 }}>担忧分析</strong><br />
                          {insight.worry_analysis}
                        </div>
                      )}
                      {insight.action_suggestion && (
                        <div style={{
                          fontSize: 14,
                          color: 'var(--text-primary)',
                          background: 'var(--accent-light)',
                          padding: '10px 12px',
                          borderRadius: 'var(--radius-md)',
                          lineHeight: 1.5,
                          marginTop: 10,
                        }}>
                          <strong style={{ color: 'var(--accent)', fontSize: 12 }}>💪 行动建议</strong><br />
                          {insight.action_suggestion}
                        </div>
                      )}
                    </>
                  )}
                </div>
              );
            } catch {
              return null;
            }
          })()}
          <div style={{ color: 'var(--text-secondary)', fontSize: 13, textAlign: 'center' }}>
            {card?.status === 'decided' ? '✅ 已做决定' : '⏸️ 已搁置'} · 对话已结束
          </div>
          {card?.status === 'decided' && (shared || card?.shared_case_id) ? (
            <div style={{ fontSize: 13, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Share2 size={14} /> 已分享到社区
            </div>
          ) : card?.status === 'decided' ? (
            <button className="btn-reopen" onClick={openShare} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
              <Share2 size={15} /> 分享到社区，帮助其他人
            </button>
          ) : null}
          <button className="btn-reopen" onClick={handleReopen}>
            重新打开讨论
          </button>
        </div>
      )}

      {/* 关闭对话 Modal */}
      <AnimatePresence>
        {closeModal && (
          <>
            <motion.div
              className="modal-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => !closing && setCloseModal(null)}
            />
            <motion.div
              className="modal-sheet"
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            >
              <div className="modal-handle" />
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                {closeModal === 'decided' ? '记录你的决定' : '先搁置这个问题'}
              </h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
                {closeModal === 'decided'
                  ? '写下你最终的决定，以后可以回顾'
                  : '暂时搁置，等你想清楚了随时可以重新打开'}
              </p>
              {closeModal === 'decided' && (
                <textarea
                  className="input"
                  placeholder="我决定..."
                  value={decisionText}
                  onChange={e => setDecisionText(e.target.value)}
                  rows={3}
                  style={{ marginBottom: 16, fontSize: 14 }}
                  autoFocus
                />
              )}
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                  disabled={closing}
                  onClick={() => setCloseModal(null)}
                >
                  取消
                </button>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1 }}
                  disabled={closing || (closeModal === 'decided' && !decisionText.trim())}
                  onClick={handleClose}
                >
                  {closing ? '保存中...' : '确认'}
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* 分享到社区 Modal */}
      <AnimatePresence>
        {shareStep && (
          <>
            <motion.div
              className="modal-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => !shareLoading && setShareStep(null)}
            />
            <motion.div
              className="modal-sheet"
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            >
              <div className="modal-handle" />

              {shareStep === 'form' && (
                <>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                    分享你的决策经验
                  </h3>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>
                    回头看，这个决定怎么样？分享出来（已自动脱敏）能帮到正在纠结的人
                  </p>

                  <label className="form-label" style={{ fontSize: 13 }}>
                    现在的满意度：{shareScore}/10
                  </label>
                  <input
                    type="range" min="1" max="10" value={shareScore}
                    onChange={e => setShareScore(Number(e.target.value))}
                    style={{ width: '100%', marginBottom: 16, accentColor: 'var(--accent)' }}
                  />

                  <label className="form-label" style={{ fontSize: 13 }}>一句话感受</label>
                  <textarea
                    className="input"
                    placeholder="比如：现在回头看挺满意的，虽然适应期累，但成长很快"
                    value={shareText}
                    onChange={e => setShareText(e.target.value)}
                    rows={3}
                    maxLength={200}
                    style={{ marginBottom: 16, fontSize: 14 }}
                    autoFocus
                  />

                  <div style={{ display: 'flex', gap: 10 }}>
                    <button className="btn btn-secondary" style={{ flex: 1 }}
                      disabled={shareLoading} onClick={() => setShareStep(null)}>
                      取消
                    </button>
                    <button className="btn btn-primary" style={{ flex: 1 }}
                      disabled={shareLoading || !shareText.trim()} onClick={handleSharePreview}>
                      {shareLoading ? '生成中...' : '下一步'}
                    </button>
                  </div>
                </>
              )}

              {shareStep === 'preview' && sharePreview && (
                <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                    预览并编辑（已脱敏）
                  </h3>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                    确认无敏感信息后发布，你可以修改任何内容
                  </p>

                  <label className="form-label" style={{ fontSize: 12 }}>核心矛盾</label>
                  <input className="input" value={sharePreview.core_conflict}
                    onChange={e => updatePreview('core_conflict', e.target.value)}
                    style={{ marginBottom: 12, fontSize: 14 }} />

                  <label className="form-label" style={{ fontSize: 12 }}>背景（已脱敏）</label>
                  <input className="input" value={sharePreview.background}
                    onChange={e => updatePreview('background', e.target.value)}
                    style={{ marginBottom: 12, fontSize: 14 }} />

                  <label className="form-label" style={{ fontSize: 12 }}>最终选择</label>
                  <input className="input" value={sharePreview.final_choice}
                    onChange={e => updatePreview('final_choice', e.target.value)}
                    style={{ marginBottom: 12, fontSize: 14 }} />

                  <label className="form-label" style={{ fontSize: 12 }}>决策转折点</label>
                  <textarea className="input" value={sharePreview.turning_point}
                    onChange={e => updatePreview('turning_point', e.target.value)}
                    rows={2} style={{ marginBottom: 12, fontSize: 14 }} />

                  <label className="form-label" style={{ fontSize: 12 }}>事后回顾</label>
                  <textarea className="input" value={sharePreview.retrospect}
                    onChange={e => updatePreview('retrospect', e.target.value)}
                    rows={2} style={{ marginBottom: 16, fontSize: 14 }} />

                  <div style={{ display: 'flex', gap: 10 }}>
                    <button className="btn btn-secondary" style={{ flex: 1 }}
                      disabled={shareLoading} onClick={() => setShareStep('form')}>
                      返回
                    </button>
                    <button className="btn btn-primary" style={{ flex: 1 }}
                      disabled={shareLoading} onClick={handleShareConfirm}>
                      {shareLoading ? '发布中...' : '确认发布'}
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
