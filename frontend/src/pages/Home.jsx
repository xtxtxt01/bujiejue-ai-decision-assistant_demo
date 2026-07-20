import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, LogOut, Brain, Settings, Lightbulb, Users } from 'lucide-react';
import { motion } from 'framer-motion';
import { getCards } from '../api';

const TYPE_LABELS = {
  career: '职业', relationship: '关系', lifestyle: '生活',
  finance: '财务', growth: '成长', education: '学业',
};

export default function Home() {
  const navigate = useNavigate();
  const uid = localStorage.getItem('uid');
  const nickname = localStorage.getItem('nickname') || '用户';
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!uid) { navigate('/'); return; }
    loadCards();
  }, []);

  const loadCards = async () => {
    try {
      const data = await getCards(uid);
      setCards(data.cards || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const activeCards = cards.filter(c => c.status === 'active');
  const closedCards = cards.filter(c => c.status !== 'active');

  const formatTime = (t) => {
    if (!t) return '';
    const d = new Date(t);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    return `${Math.floor(diff / 86400000)}天前`;
  };

  return (
    <div className="page">
      {/* 顶栏 */}
      <div className="navbar">
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>不纠结</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>嗨，{nickname}</div>
        </div>
        <button className="navbar-btn" onClick={() => navigate('/community')}>
          <Users size={18} />
        </button>
        <button className="navbar-btn" onClick={() => navigate('/insights')}>
          <Lightbulb size={18} />
        </button>
        <button className="navbar-btn" onClick={() => navigate('/memories')}>
          <Brain size={18} />
        </button>
        <button className="navbar-btn" onClick={() => navigate('/settings')}>
          <Settings size={18} />
        </button>
        <button className="navbar-btn" onClick={() => { localStorage.clear(); navigate('/'); }}>
          <LogOut size={18} />
        </button>
      </div>

      {/* 卡片列表 */}
      <div className="scroll-area">
        {loading ? (
          <div className="empty-state"><p>加载中...</p></div>
        ) : cards.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🤔</div>
            <h3>还没有纠结</h3>
            <p>点击下方按钮，说出你正在纠结的事</p>
          </div>
        ) : (
          <>
            {activeCards.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                  进行中
                </div>
                {activeCards.map((card, i) => (
                  <motion.div key={card.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}>
                    <div className="dilemma-card" onClick={() => navigate(`/card/${card.id}`)}>
                      <div className="card-header">
                        <div className="card-status active" />
                        <div className="card-title">{card.title || '新的纠结'}</div>
                      </div>
                      {card.core_conflict && (
                        <div className="card-conflict">{card.core_conflict}</div>
                      )}
                      <div className="card-meta">
                        <span className="card-type">{TYPE_LABELS[card.dilemma_type] || card.dilemma_type}</span>
                        <span className="card-time">{formatTime(card.updated_at)}</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}

            {closedCards.length > 0 && (
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: 1 }}>
                  已结束
                </div>
                {closedCards.map(card => (
                  <div key={card.id} className="dilemma-card" style={{ opacity: 0.6 }}
                    onClick={() => navigate(`/card/${card.id}`)}>
                    <div className="card-header">
                      <div className={`card-status ${card.status}`} />
                      <div className="card-title">{card.title || '纠结'}</div>
                    </div>
                    {card.core_conflict && (
                      <div className="card-conflict">{card.core_conflict}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* FAB */}
      <button className="fab" onClick={() => navigate('/new')}>
        <Plus size={24} />
      </button>
    </div>
  );
}
