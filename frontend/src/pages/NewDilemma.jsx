import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Loader } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { createCard } from '../api';
import Toast from '../components/Toast';
import { useToast } from '../hooks/useToast';

const DILEMMA_TYPES = [
  { key: 'career', label: '工作与职业', emoji: '💼' },
  { key: 'relationship', label: '感情与人际', emoji: '💝' },
  { key: 'lifestyle', label: '生活方式', emoji: '🏠' },
  { key: 'finance', label: '消费与财务', emoji: '💰' },
  { key: 'growth', label: '成长与方向', emoji: '🌱' },
  { key: 'education', label: '学业与升学', emoji: '🎓' },
];

const TRIGGER_PLACEHOLDERS = {
  career: '比如：收到了一个新 offer，但不确定要不要跳槽',
  relationship: '比如：和对象吵了一架，不知道该怎么处理',
  lifestyle: '比如：想搬到另一个城市生活，但家人反对',
  finance: '比如：看中了一件东西，不确定值不值得买',
  growth: '比如：坚持了半年的计划，最近开始怀疑方向对不对',
  education: '比如：拿到了 offer 和学校的录取，不知道怎么选',
};

const FEARED_PLACEHOLDERS = {
  career: '比如：怕新公司试用期通不过，骑虎难下',
  relationship: '比如：怕说了真心话反而让关系更糟',
  lifestyle: '比如：怕去了新地方适应不了，后悔莫及',
  finance: '比如：怕买了之后用不上，又心疼钱',
  growth: '比如：怕坚持下去也没结果，浪费了时间',
  education: '比如：怕选错了以后反复后悔',
};

const variants = {
  enter: (dir) => ({ x: dir > 0 ? 60 : -60, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir) => ({ x: dir > 0 ? -60 : 60, opacity: 0 }),
};

export default function NewDilemma() {
  const navigate = useNavigate();
  const uid = localStorage.getItem('uid');
  const [step, setStep] = useState(0);
  const [dir, setDir] = useState(1);
  const [selectedType, setSelectedType] = useState('');
  const [triggerEvent, setTriggerEvent] = useState('');
  const [fearedOutcome, setFearedOutcome] = useState('');
  const [loading, setLoading] = useState(false);
  const [toast, showToast] = useToast();

  const goTo = (next) => {
    setDir(next > step ? 1 : -1);
    setStep(next);
  };

  const canNext = [
    selectedType !== '',
    triggerEvent.trim() !== '',
    fearedOutcome.trim() !== '',
  ];

  const handleSubmit = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const data = await createCard(uid, selectedType, '', triggerEvent.trim(), fearedOutcome.trim());
      navigate(`/card/${data.card_id}`, { state: { firstMessage: data.assistant_message } });
    } catch (e) {
      showToast(e.message || '创建失败，请稍后重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <Toast toast={toast} />

      <div className="navbar">
        <button className="navbar-btn" onClick={() => step === 0 ? navigate('/home') : goTo(step - 1)}>
          <ChevronLeft size={20} />
        </button>
        <span className="navbar-title">新的纠结</span>
        <div style={{ width: 36 }} />
      </div>

      {/* Step dots */}
      <div className="steps">
        {[0, 1, 2].map(i => (
          <div key={i} className={`step-dot ${i === step ? 'active' : i < step ? 'done' : ''}`} />
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <AnimatePresence custom={dir} mode="wait">
          <motion.div
            key={step}
            custom={dir}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: 0.22, ease: 'easeInOut' }}
            style={{ position: 'absolute', inset: 0, overflowY: 'auto', padding: '24px 20px' }}
          >
            {step === 0 && (
              <>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 6 }}>第 1 步 / 共 3 步</p>
                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>这是什么类型的纠结？</h2>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
                  选一个最接近的类型，帮 AI 更快进入状态
                </p>
                <div className="tag-group">
                  {DILEMMA_TYPES.map(t => (
                    <div
                      key={t.key}
                      className={`tag ${selectedType === t.key ? 'active' : ''}`}
                      onClick={() => setSelectedType(t.key)}
                      style={{ fontSize: 14, padding: '11px 18px' }}
                    >
                      {t.emoji} {t.label}
                    </div>
                  ))}
                </div>
              </>
            )}

            {step === 1 && (
              <>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 6 }}>第 2 步 / 共 3 步</p>
                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>触发事件是什么？</h2>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
                  是什么让你开始纠结？一句话就够
                </p>
                <textarea
                  className="input"
                  style={{ minHeight: 120, fontSize: 15 }}
                  placeholder={TRIGGER_PLACEHOLDERS[selectedType] || '用一句话描述触发这次纠结的事情'}
                  value={triggerEvent}
                  onChange={e => setTriggerEvent(e.target.value)}
                  autoFocus
                />
              </>
            )}

            {step === 2 && (
              <>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 6 }}>第 3 步 / 共 3 步</p>
                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>最担心什么？</h2>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
                  说出你最怕发生的结果，AI 会重点关注这个
                </p>
                <textarea
                  className="input"
                  style={{ minHeight: 120, fontSize: 15 }}
                  placeholder={FEARED_PLACEHOLDERS[selectedType] || '说出你最担心的后果'}
                  value={fearedOutcome}
                  onChange={e => setFearedOutcome(e.target.value)}
                  autoFocus
                />
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      <div style={{ padding: '16px 20px 28px' }}>
        {step < 2 ? (
          <button
            className="btn btn-primary btn-block btn-lg"
            disabled={!canNext[step]}
            onClick={() => goTo(step + 1)}
          >
            下一步 <ChevronRight size={18} />
          </button>
        ) : (
          <button
            className="btn btn-primary btn-block btn-lg"
            disabled={!canNext[2] || loading}
            onClick={handleSubmit}
          >
            {loading ? (
              <><Loader size={18} className="spin" /> AI 正在思考中...</>
            ) : (
              '开始聊这个纠结'
            )}
          </button>
        )}
        {loading && (
          <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
            通常需要 5–15 秒，请稍候
          </p>
        )}
      </div>
    </div>
  );
}
