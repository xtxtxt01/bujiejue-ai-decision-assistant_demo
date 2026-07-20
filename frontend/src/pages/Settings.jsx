import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { applyTheme } from '../App';

const THEMES = [
  { key: 'default', label: '天空', color: '#4A7DFF' },
  { key: 'emerald', label: '翡翠', color: '#10b981' },
  { key: 'rose', label: '玫瑰', color: '#ec4899' },
  { key: 'amber', label: '琥珀', color: '#f59e0b' },
  { key: 'violet', label: '紫水晶', color: '#8b5cf6' },
  { key: 'neutral', label: '中性', color: '#1a1a2e' },
];

export default function SettingsPage() {
  const navigate = useNavigate();
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'default');

  const selectTheme = (key) => {
    setTheme(key);
    localStorage.setItem('theme', key);
    applyTheme(key);
  };

  return (
    <div className="page">
      <div className="navbar">
        <button className="navbar-btn" onClick={() => navigate('/home')}>
          <ChevronLeft size={20} />
        </button>
        <div className="navbar-title">设置</div>
        <div style={{ width: 36 }} />
      </div>

      <div className="scroll-area">
        <p className="form-label" style={{ marginBottom: 16 }}>主题颜色</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {THEMES.map(t => (
            <button key={t.key} onClick={() => selectTheme(t.key)}
              style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                padding: 16, background: 'none', border: 'none', cursor: 'pointer',
              }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%', background: t.color,
                border: theme === t.key ? '3px solid var(--text-primary)' : '3px solid transparent',
                boxShadow: theme === t.key ? '0 0 0 2px ' + t.color : 'none',
                transition: 'all 0.2s',
              }} />
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{t.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
