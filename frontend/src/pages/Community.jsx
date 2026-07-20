import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Heart, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { motion } from 'framer-motion';
import { getCommunityCases, addCaseEmpathy } from '../api';

const CASE_TYPES = [
  { key: 'all', label: '全部' },
  { key: 'career', label: '💼 工作' },
  { key: 'relationship', label: '💝 感情' },
  { key: 'lifestyle', label: '🏠 生活' },
  { key: 'finance', label: '💰 消费' },
  { key: 'education', label: '🎓 学业' },
];

function renderScore(score) {
  const color = score >= 7 ? 'var(--success)' : score >= 5 ? 'var(--warning)' : 'var(--danger)';
  return <span style={{ color, fontWeight: 600 }}>{score}/10</span>;
}

// 可复用案例卡片
function CaseCard({ c, expanded, onToggle, onEmpathy, highlight }) {
  return (
    <div
      onClick={onToggle}
      style={{
        background: 'var(--bg-primary)',
        border: highlight ? '1px solid var(--accent)' : '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: 16,
        cursor: 'pointer',
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8, lineHeight: 1.4 }}>
        {c.core_conflict}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
        {c.background}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13, marginBottom: expanded ? 12 : 0 }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)' }}>
          <Clock size={13} /> 纠结{c.duration_days}天
        </span>
        <span style={{ color: 'var(--accent)', fontWeight: 500 }}>
          → {c.final_choice}
        </span>
      </div>

      {expanded && (
        <div style={{ marginTop: 4 }}>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.6 }}>
            <span style={{ color: 'var(--text-muted)' }}>转折点：</span>
            {c.turning_point}
          </div>
          <div style={{
            background: 'var(--bg-elevated)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 14px',
            fontSize: 13,
            lineHeight: 1.6,
          }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: 4, fontSize: 12 }}>
              {c.retrospect_months}个月后回顾 · 满意度 {renderScore(c.retrospect_score)}
            </div>
            {c.retrospect}
          </div>
        </div>
      )}

      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-light)',
      }}>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
          {expanded ? <><ChevronUp size={14} /> 收起</> : <><ChevronDown size={14} /> 查看转折点和结果</>}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onEmpathy(c.id); }}
          style={{
            display: 'flex', alignItems: 'center', gap: 4,
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 13, color: 'var(--text-secondary)',
            padding: '4px 8px', borderRadius: 8,
          }}
        >
          <Heart size={14} /> 我也是 {c.empathy_count > 0 ? c.empathy_count : ''}
        </button>
      </div>
    </div>
  );
}

// PLACEHOLDER_MAIN
export default function Community() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    loadCases();
  }, [filter]);

  const loadCases = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getCommunityCases(filter);
      setCases(data.cases || []);
    } catch (e) {
      setError('加载失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 共鸣：乐观更新
  const handleEmpathy = async (caseId) => {
    const bump = (list, delta) => list.map(c =>
      c.id === caseId ? { ...c, empathy_count: c.empathy_count + delta } : c
    );
    setCases(prev => bump(prev, 1));
    try {
      await addCaseEmpathy(caseId);
    } catch (err) {
      setCases(prev => bump(prev, -1));
    }
  };

  const toggle = (key) => setExpandedId(prev => prev === key ? null : key);

  return (
    <div className="page">
      <div className="navbar">
        <button className="navbar-btn" onClick={() => navigate('/home')}>
          <ArrowLeft size={20} />
        </button>
        <div style={{ flex: 1, textAlign: 'center', fontWeight: 600, fontSize: 16 }}>
          决策经验库
        </div>
        <div style={{ width: 36 }} />
      </div>

      <div style={{ padding: '12px 16px 4px', fontSize: 13, color: 'var(--text-muted)' }}>
        看看跟你情况相似的人，最后怎么选的
      </div>

      <div className="scroll-area">
        {/* 分类筛选 */}
        <div style={{
          display: 'flex', gap: 8, padding: '12px 0 8px', overflowX: 'auto',
          position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 1,
        }}>
          {CASE_TYPES.map(t => (
            <button
              key={t.key}
              onClick={() => setFilter(t.key)}
              style={{
                flexShrink: 0,
                padding: '6px 14px',
                borderRadius: 16,
                fontSize: 13,
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.15s',
                background: filter === t.key ? 'var(--accent)' : 'var(--bg-elevated)',
                color: filter === t.key ? '#fff' : 'var(--text-secondary)',
                fontWeight: filter === t.key ? 600 : 400,
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* 浏览列表 */}
        {loading ? (
          <div className="empty-state"><p style={{ color: 'var(--text-muted)' }}>加载中...</p></div>
        ) : error ? (
          <div className="empty-state"><p style={{ color: 'var(--danger)' }}>{error}</p></div>
        ) : cases.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📭</div>
            <p>这个类型暂时还没有案例</p>
          </div>
        ) : (
          <div style={{ padding: '4px 0 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {cases.map((c, i) => (
              <motion.div
                key={`all-${c.id}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(i * 0.03, 0.3) }}
              >
                <CaseCard
                  c={c}
                  expanded={expandedId === `all-${c.id}`}
                  onToggle={() => toggle(`all-${c.id}`)}
                  onEmpathy={handleEmpathy}
                />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

