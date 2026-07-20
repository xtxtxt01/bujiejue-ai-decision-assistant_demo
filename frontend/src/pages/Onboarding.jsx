import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, Sparkles } from 'lucide-react';
import { register } from '../api';
import { applyTheme } from '../App';

const STEPS = ['账号', '决策模式', 'MBTI', '领域', '价值观', '主题'];

const SCENARIO_QUESTIONS = [
  {
    question: '周末和朋友约饭，怎么选餐厅？',
    options: [
      { text: '打开点评 app，看评分、人均、距离，综合对比', scores: { rational: 1 } },
      { text: '想到哪家就去哪家，觉得对了就行', scores: { intuitive: 1 } },
      { text: '丢群里让大家投票，多数人想吃啥就吃啥', scores: { dependent: 1 } },
    ],
  },
  {
    question: '网购看中一件外套，价格不低',
    options: [
      { text: '立刻下单，想要就买，不拖延', scores: { spontaneous: 1 } },
      { text: '货比三家，看材质、评价、性价比', scores: { rational: 1 } },
      { text: '先加购物车，过几天再看还想不想要', scores: { avoidant: 1 } },
    ],
  },
  {
    question: '面对换工作这样的重大决定，你会',
    options: [
      { text: '列清单：现状和新机会各有什么利弊，逐条对比', scores: { rational: 1 } },
      { text: '内心安静地想想，到底哪个更符合自己', scores: { intuitive: 1 } },
      { text: '问换过工作的朋友怎么看，参考他们的经验', scores: { dependent: 1 } },
    ],
  },
  {
    question: '一个决定拖了很久没做，最可能是因为',
    options: [
      { text: '每个选项都不完美，还在等更好的机会', scores: { avoidant: 1 } },
      { text: '其实心里已经有答案，但还没到非做不可的时候', scores: { intuitive: 1 } },
      { text: '觉得再拖下去不是办法，该赶紧做决定了', scores: { spontaneous: 1 } },
    ],
  },
  {
    question: '朋友推荐你一部电影，你会',
    options: [
      { text: '问问其他人怎么评价，多听几个意见', scores: { dependent: 1 } },
      { text: '先看看豆瓣评分和影评再决定看不看', scores: { rational: 1 } },
      { text: '收藏了，但可能一直不会看（不急着决定）', scores: { avoidant: 1 } },
    ],
  },
  {
    question: '做决定时，你更相信',
    options: [
      { text: '直觉和感觉，心里有答案', scores: { intuitive: 1 } },
      { text: '有经验的人的建议，他们走过的路', scores: { dependent: 1 } },
      { text: '快速试错，做了再说，不对再调整', scores: { spontaneous: 1 } },
    ],
  },
  {
    question: '临近 deadline 必须做决定了',
    options: [
      { text: '赶紧理一下思路，尽量做个合理的选择', scores: { rational: 1 } },
      { text: '时间不够想了，选一个感觉最顺的', scores: { intuitive: 1 } },
      { text: '能不能延期？实在不行就随便选一个', scores: { avoidant: 1 } },
    ],
  },
  {
    question: '开始一个新项目前，你通常',
    options: [
      { text: '直接开干，边做边调整方向', scores: { spontaneous: 1 } },
      { text: '先做个计划：目标、步骤、资源都列清楚', scores: { rational: 1 } },
      { text: '问问做过类似项目的人，学习他们的经验', scores: { dependent: 1 } },
    ],
  },
  {
    question: '和别人一起做决定时，你倾向于',
    options: [
      { text: '听大家的想法，综合后做决定', scores: { dependent: 1 } },
      { text: '不想当主导者，等别人决定了我就跟着做', scores: { avoidant: 1 } },
      { text: '凭直觉提个方向，让大家讨论', scores: { intuitive: 1 } },
    ],
  },
  {
    question: '关于"做决定"这件事，你的态度是',
    options: [
      { text: '做决定是件累人的事，能少做就少做', scores: { avoidant: 1 } },
      { text: '想清楚了就快速行动，不拖泥带水', scores: { spontaneous: 1 } },
      { text: '做决定需要时间，但最终能做出好选择', scores: { rational: 1 } },
    ],
  },
];

const MAXIMIZER_QUESTIONS = [
  {
    question: '做了决定之后，你通常会——',
    options: [
      { text: '反复想是不是还有更好的选择', value: 'maximizer' },
      { text: '决定了就决定了，往前看', value: 'satisficer' },
      { text: '看情况，重要的事会多想，小事不会', value: 'mixed' },
    ],
  },
  {
    question: '选择多的时候（比如点外卖有 50 家餐厅），你会——',
    options: [
      { text: '觉得压力很大，害怕选错', value: 'maximizer' },
      { text: '快速筛选出几个"还不错"的，选一个', value: 'satisficer' },
      { text: '干脆选以前吃过的，省心', value: 'satisficer' },
    ],
  },
];

const STYLE_LABELS = {
  rational: { name: '理性分析型', desc: '喜欢搜集信息、对比分析后做决定。我会帮你整理利弊、提供数据支持。' },
  intuitive: { name: '直觉感知型', desc: '相信自己的第一感觉和整体判断。我会帮你确认内心的声音。' },
  dependent: { name: '参考借鉴型', desc: '重视他人意见和集体智慧。我会提供多角度观点供你参考。' },
  avoidant: { name: '审慎观望型', desc: '不急于做决定，倾向多等等看。我会帮你把问题拆小、降低决策压力。' },
  spontaneous: { name: '果断行动型', desc: '速度快，想到就做，不拖泥带水。我会帮你快速验证想法是否靠谱。' },
};

const MAX_LABELS = {
  maximizer: { name: '追求最优型', desc: '希望找到最好的答案，选择后容易想"有没有更好的"' },
  satisficer: { name: '务实满意型', desc: '达到标准就满意，不过分纠结未选的选项' },
  mixed: { name: '灵活权衡型', desc: '重要决定追求最优，小事满意即可' },
};

const MBTI_TYPES = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP',
];

const DILEMMA_TYPES = [
  { key: 'career', label: '工作与职业发展', emoji: '💼' },
  { key: 'relationship', label: '感情与人际关系', emoji: '💝' },
  { key: 'lifestyle', label: '生活方式选择', emoji: '🏠' },
  { key: 'finance', label: '消费与财务决策', emoji: '💰' },
  { key: 'growth', label: '个人成长与方向', emoji: '🌱' },
  { key: 'education', label: '学业与升学', emoji: '🎓' },
];

const LIFE_STAGES = [
  { key: 'student', label: '🎒 在读学生' },
  { key: 'early_career', label: '🚀 刚入职场（0-3 年）' },
  { key: 'mid_career', label: '💼 职场中期（3-10 年）' },
  { key: 'senior', label: '🏢 资深职场人 / 管理层' },
  { key: 'freelance', label: '🏡 自由职业 / 创业中' },
  { key: 'transition', label: '🔄 正在转型 / 找方向' },
  { key: 'gap_year', label: '🌊 间隔期 / 休息调整中' },
  { key: 'homemaker', label: '🏠 全职在家' },
  { key: 'other', label: '🌱 其他情况' },
];

const VALUES = [
  { key: '自由自主', desc: '按自己的想法生活和做事' },
  { key: '新鲜刺激', desc: '追求新体验、不喜欢一成不变' },
  { key: '享受生活', desc: '让自己开心、舒适最重要' },
  { key: '成就认可', desc: '想在领域内做出成绩、被认可' },
  { key: '财富地位', desc: '追求经济实力和社会地位' },
  { key: '安全稳定', desc: '稳定的收入、关系和生活节奏' },
  { key: '家庭责任', desc: '满足家人期望、遵守承诺' },
  { key: '助人利他', desc: '帮助身边的人、维护关系' },
  { key: '社会公正', desc: '关心社会公平与环境问题' },
  { key: '健康平衡', desc: '身心健康和工作生活平衡' },
];

const THEMES = [
  { key: 'default', label: '天空', color: '#4A7DFF' },
  { key: 'emerald', label: '翡翠', color: '#10b981' },
  { key: 'rose', label: '玫瑰', color: '#ec4899' },
  { key: 'amber', label: '琥珀', color: '#f59e0b' },
  { key: 'violet', label: '紫水晶', color: '#8b5cf6' },
  { key: 'neutral', label: '中性', color: '#1a1a2e' },
];

function calcDecisionStyle(answers) {
  const scores = { rational: 0, intuitive: 0, dependent: 0, avoidant: 0, spontaneous: 0 };
  answers.forEach((ansIdx, qIdx) => {
    if (ansIdx === null) return;
    const opt = SCENARIO_QUESTIONS[qIdx].options[ansIdx];
    Object.entries(opt.scores).forEach(([k, v]) => { scores[k] += v; });
  });

  // 风格优先级（用于并列时排序）
  const STYLE_PRIORITY = {
    'rational': 1,
    'intuitive': 2,
    'dependent': 3,
    'spontaneous': 4,
    'avoidant': 5
  };

  // 按得分降序排序，得分相同时按优先级排序
  const sorted = Object.entries(scores).sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1];  // 按分数降序
    return STYLE_PRIORITY[a[0]] - STYLE_PRIORITY[b[0]];  // 得分相同时按优先级
  });

  const highest = sorted[0][1];
  const secondHighest = sorted[1][1];
  const gap = highest - secondHighest;

  // 判定规则（新版：10题，满分6，无平衡型）
  // 优先级 1：组合型（两个风格都强且接近）
  if (highest >= 3 && secondHighest >= 3 && gap <= 1) {
    return `${sorted[0][0]}_${sorted[1][0]}`;
  }

  // 优先级 2 & 3：单一主导（强或弱）
  // 所有其他情况都归到最高分的风格（不使用 balanced）
  return sorted[0][0];
}

function calcMaxTendency(answers) {
  const counts = { maximizer: 0, satisficer: 0, mixed: 0 };
  answers.forEach((ansIdx, qIdx) => {
    if (ansIdx === null) return;
    counts[MAXIMIZER_QUESTIONS[qIdx].options[ansIdx].value] += 1;
  });
  if (counts.maximizer > counts.satisficer) return 'maximizer';
  if (counts.satisficer > counts.maximizer) return 'satisficer';
  return 'mixed';
}

function getStyleDisplayName(styleKey) {
  if (STYLE_LABELS[styleKey]) return STYLE_LABELS[styleKey].name;
  const parts = styleKey.split('_');
  if (parts.length === 2 && STYLE_LABELS[parts[0]] && STYLE_LABELS[parts[1]]) {
    return `${STYLE_LABELS[parts[0]].name} + ${STYLE_LABELS[parts[1]].name}`;
  }
  // 兜底：如果找不到，返回 rational（不应该发生）
  return STYLE_LABELS.rational.name;
}

function getStyleDesc(styleKey) {
  if (STYLE_LABELS[styleKey]) return STYLE_LABELS[styleKey].desc;
  const parts = styleKey.split('_');
  if (parts.length === 2 && STYLE_LABELS[parts[0]] && STYLE_LABELS[parts[1]]) {
    return `${STYLE_LABELS[parts[0]].desc.replace(/。.*/, '')}，同时也${STYLE_LABELS[parts[1]].desc.replace(/。.*/, '')}。`;
  }
  // 兜底：如果找不到，返回 rational（不应该发生）
  return STYLE_LABELS.rational.desc;
}

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [qPage, setQPage] = useState(0);
  const [scenarioAnswers, setScenarioAnswers] = useState(Array(10).fill(null));
  const [maxAnswers, setMaxAnswers] = useState(Array(2).fill(null));
  const [showResult, setShowResult] = useState(false);
  const [form, setForm] = useState({
    username: '', password: '', nickname: '',
    mbti: '', frequent_dilemma_types: [], life_stage: '',
    life_stage_note: '', values_ranking: [], self_intro: '', theme: 'default',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const update = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const canNext = () => {
    switch (step) {
      case 0: return form.username && form.password && form.nickname;
      case 1: return showResult;
      case 2: return !!form.mbti;
      case 3: return form.frequent_dilemma_types.length > 0 && !!form.life_stage;
      case 4: return form.values_ranking.length >= 3;
      case 5: return !!form.theme;
      default: return false;
    }
  };

  const handleScenarioAnswer = (qIdx, optIdx) => {
    if (qIdx < 10) {
      const next = [...scenarioAnswers];
      next[qIdx] = optIdx;
      setScenarioAnswers(next);
    } else {
      const next = [...maxAnswers];
      next[qIdx - 10] = optIdx;
      setMaxAnswers(next);
    }
  };

  const handleQPageNext = () => {
    if (qPage < 5) {
      setQPage(qPage + 1);
    } else {
      setShowResult(true);
    }
  };

  const currentPageAnswered = () => {
    if (qPage < 5) {
      const i = qPage * 2;
      return scenarioAnswers[i] !== null && scenarioAnswers[i + 1] !== null;
    }
    return maxAnswers[0] !== null && maxAnswers[1] !== null;
  };

  const toggleDilemma = (key) => {
    const arr = form.frequent_dilemma_types;
    if (arr.includes(key)) update('frequent_dilemma_types', arr.filter(k => k !== key));
    else update('frequent_dilemma_types', [...arr, key]);
  };

  const toggleValue = (key) => {
    const arr = form.values_ranking;
    if (arr.includes(key)) update('values_ranking', arr.filter(k => k !== key));
    else if (arr.length < 5) update('values_ranking', [...arr, key]);
  };

  const moveValue = (idx, dir) => {
    const arr = [...form.values_ranking];
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= arr.length) return;
    [arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]];
    update('values_ranking', arr);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const styleKey = calcDecisionStyle(scenarioAnswers);
      const maxKey = calcMaxTendency(maxAnswers);
      const selfIntro = form.life_stage_note
        ? `${form.self_intro}\n补充：${form.life_stage_note}`.trim()
        : form.self_intro;
      const res = await register({
        username: form.username, password: form.password, nickname: form.nickname,
        decision_style: styleKey, maximizer_tendency: maxKey, mbti: form.mbti,
        frequent_dilemma_types: form.frequent_dilemma_types,
        life_stage: form.life_stage, values_ranking: form.values_ranking,
        self_intro: selfIntro, theme: form.theme,
      });
      localStorage.setItem('uid', res.uid);
      localStorage.setItem('username', form.username);
      localStorage.setItem('nickname', form.nickname);
      localStorage.setItem('theme', form.theme);
      applyTheme(form.theme);
      navigate('/home');
    } catch (e) {
      setError(e.message || '注册失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const next = () => { if (step < 5) setStep(step + 1); else handleSubmit(); };
  const prev = () => {
    if (step === 1 && showResult) { setShowResult(false); return; }
    if (step === 1 && qPage > 0) { setQPage(qPage - 1); return; }
    if (step > 0) setStep(step - 1);
  };

  const decisionStyle = calcDecisionStyle(scenarioAnswers);
  const maxTendency = calcMaxTendency(maxAnswers);

  // Render helpers for each step
  const renderStep0 = () => (
    <div className="scroll-area">
      <div className="form-group">
        <label className="form-label">用户名</label>
        <input className="input" value={form.username} onChange={e => update('username', e.target.value)} placeholder="用于登录" />
      </div>
      <div className="form-group">
        <label className="form-label">密码</label>
        <input className="input" type="password" value={form.password} onChange={e => update('password', e.target.value)} placeholder="至少 6 位" />
      </div>
      <div className="form-group">
        <label className="form-label">昵称</label>
        <input className="input" value={form.nickname} onChange={e => update('nickname', e.target.value)} placeholder="我怎么称呼你？" />
      </div>
    </div>
  );

  const renderStep1 = () => {
    if (showResult) {
      return (
        <div className="scroll-area" style={{ textAlign: 'center', padding: '2rem 1rem' }}>
          <Sparkles size={40} style={{ margin: '0 auto 1rem', color: 'var(--accent)' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>你的决策风格</h3>
          <h2 style={{ color: 'var(--accent)', marginBottom: '0.5rem' }}>{getStyleDisplayName(decisionStyle)}</h2>
          <p style={{ opacity: 0.8, marginBottom: '1.5rem' }}>{getStyleDesc(decisionStyle)}</p>
          <div style={{ background: 'var(--card-bg)', borderRadius: 12, padding: '1rem', marginBottom: '1rem' }}>
            <p style={{ fontSize: '0.9rem', opacity: 0.7 }}>倾向类型：{MAX_LABELS[maxTendency].name}</p>
            <p style={{ fontSize: '0.85rem', opacity: 0.6 }}>{MAX_LABELS[maxTendency].desc}</p>
          </div>
        </div>
      );
    }
    const questions = qPage < 5
      ? [SCENARIO_QUESTIONS[qPage * 2], SCENARIO_QUESTIONS[qPage * 2 + 1]]
      : MAXIMIZER_QUESTIONS;
    const baseIdx = qPage < 5 ? qPage * 2 : 10;
    return (
      <div className="scroll-area">
        <p style={{ fontSize: '0.85rem', opacity: 0.6, marginBottom: '1rem' }}>第 {qPage + 1} / 6 页</p>
        {questions.map((q, i) => (
          <div key={baseIdx + i} style={{ marginBottom: '1.5rem' }}>
            <p className="form-label" style={{ marginBottom: '0.75rem' }}>Q{baseIdx + i + 1}. {q.question}</p>
            <div className="tag-group" style={{ flexDirection: 'column' }}>
              {q.options.map((opt, oi) => {
                const answered = baseIdx + i < 10 ? scenarioAnswers[baseIdx + i] : maxAnswers[baseIdx + i - 10];
                return (
                  <button key={oi} className={`tag${answered === oi ? ' active' : ''}`}
                    onClick={() => handleScenarioAnswer(baseIdx + i, oi)}
                    style={{ textAlign: 'left', width: '100%' }}>
                    {opt.text}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderStep2 = () => (
    <div className="scroll-area">
      <p className="form-label" style={{ marginBottom: '1rem' }}>你的 MBTI 类型</p>
      <div className="tag-group" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
        {MBTI_TYPES.map(t => (
          <button key={t} className={`tag${form.mbti === t ? ' active' : ''}`} onClick={() => update('mbti', t)}>{t}</button>
        ))}
      </div>
      <button className={`tag${form.mbti === 'unknown' ? ' active' : ''}`}
        style={{ marginTop: '1rem', width: '100%' }}
        onClick={() => update('mbti', 'unknown')}>
        🤷 不确定 / 没测过
      </button>
    </div>
  );

  const renderStep3 = () => (
    <div className="scroll-area">
      <p className="form-label" style={{ marginBottom: '0.75rem' }}>你常纠结的领域（至少选 1 个）</p>
      <div className="tag-group">
        {DILEMMA_TYPES.map(d => (
          <button key={d.key} className={`tag${form.frequent_dilemma_types.includes(d.key) ? ' active' : ''}`}
            onClick={() => toggleDilemma(d.key)}>
            {d.emoji} {d.label}
          </button>
        ))}
      </div>
      <p className="form-label" style={{ marginTop: '1.5rem', marginBottom: '0.75rem' }}>你的人生阶段</p>
      <div className="tag-group" style={{ flexDirection: 'column' }}>
        {LIFE_STAGES.map(s => (
          <button key={s.key} className={`tag${form.life_stage === s.key ? ' active' : ''}`}
            onClick={() => update('life_stage', s.key)} style={{ width: '100%', textAlign: 'left' }}>
            {s.label}
          </button>
        ))}
      </div>
      <div className="form-group" style={{ marginTop: '1rem' }}>
        <label className="form-label">补充说明（选填）</label>
        <input className="input" value={form.life_stage_note} onChange={e => update('life_stage_note', e.target.value)} placeholder="简单说说你的情况" />
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="scroll-area">
      <p className="form-label" style={{ marginBottom: '0.5rem' }}>选择你最看重的价值观（3-5 个）</p>
      <p style={{ fontSize: '0.8rem', opacity: 0.5, marginBottom: '1rem' }}>选好后可上下拖动排序</p>
      <div className="tag-group">
        {VALUES.map(v => (
          <button key={v.key} className={`tag${form.values_ranking.includes(v.key) ? ' active' : ''}`}
            onClick={() => toggleValue(v.key)}>
            {v.key}
          </button>
        ))}
      </div>
      {form.values_ranking.length > 0 && (
        <div className="sortable-list" style={{ marginTop: '1.5rem' }}>
          <p className="form-label" style={{ marginBottom: '0.5rem' }}>排列优先级（从高到低）</p>
          {form.values_ranking.map((v, i) => (
            <div key={v} className="sortable-item">
              <span>{i + 1}. {v}</span>
              <span>
                <button className="btn btn-ghost" onClick={() => moveValue(i, -1)} disabled={i === 0}>↑</button>
                <button className="btn btn-ghost" onClick={() => moveValue(i, 1)} disabled={i === form.values_ranking.length - 1}>↓</button>
              </span>
            </div>
          ))}
        </div>
      )}
      <div className="form-group" style={{ marginTop: '1.5rem' }}>
        <label className="form-label">自我介绍（选填）</label>
        <textarea className="input" rows={4} maxLength={200} value={form.self_intro}
          onChange={e => update('self_intro', e.target.value)}
          placeholder="比如：90后，坐标上海，互联网行业产品经理，已婚有娃。平时喜欢跑步和看书，性格偏内向，容易想多。" />
      </div>
    </div>
  );

  const renderStep5 = () => (
    <div className="scroll-area">
      <p className="form-label" style={{ marginBottom: 16 }}>选择主题色</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {THEMES.map(t => (
          <button key={t.key}
            onClick={() => { update('theme', t.key); applyTheme(t.key); }}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
              padding: 16, background: 'none', border: 'none', cursor: 'pointer',
            }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%', background: t.color,
              border: form.theme === t.key ? '3px solid var(--text-primary)' : '3px solid transparent',
              boxShadow: form.theme === t.key ? '0 0 0 2px ' + t.color : 'none',
              transition: 'all 0.2s',
            }} />
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{t.label}</span>
          </button>
        ))}
      </div>
    </div>
  );

  const renderSteps = [renderStep0, renderStep1, renderStep2, renderStep3, renderStep4, renderStep5];

  const getNextLabel = () => {
    if (step === 1 && !showResult) return '下一题';
    if (step === 5) return loading ? '提交中...' : '完成注册';
    return '下一步';
  };

  const handleNext = () => {
    if (step === 1 && !showResult) { handleQPageNext(); return; }
    next();
  };

  const isNextDisabled = () => {
    if (step === 1 && !showResult) return !currentPageAnswered();
    return !canNext() || loading;
  };

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <div className="steps" style={{ flexShrink: 0 }}>
        {STEPS.map((s, i) => (
          <div key={s} className={`step-dot${i === step ? ' active' : ''}${i < step ? ' done' : ''}`} />
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '0 1rem' }}>
        <AnimatePresence mode="wait">
          <motion.div key={step + '-' + (step === 1 ? qPage + '-' + showResult : '')}
            initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.2 }}>
            {renderSteps[step]()}
          </motion.div>
        </AnimatePresence>
      </div>

      {error && <p style={{ color: 'var(--error)', textAlign: 'center', margin: '0.5rem 0' }}>{error}</p>}

      <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '1rem' }}>
        <button className="btn btn-primary btn-block btn-lg" onClick={handleNext} disabled={isNextDisabled()}>
          {getNextLabel()} <ChevronRight size={18} />
        </button>
        {(step > 0 || (step === 1 && qPage > 0)) && (
          <button className="btn btn-ghost btn-block" onClick={prev}>
            <ChevronLeft size={16} /> 返回上一步
          </button>
        )}
      </div>
    </div>
  );
}