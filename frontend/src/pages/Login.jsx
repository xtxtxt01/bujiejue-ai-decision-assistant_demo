import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api';
import { applyTheme } from '../App';
import { Sparkles } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!username || !password) {
      setError('请输入账号和密码');
      return;
    }

    setLoading(true);
    try {
      const data = await login(username, password);
      localStorage.setItem('uid', data.uid);
      localStorage.setItem('username', data.username);
      localStorage.setItem('nickname', data.nickname);
      localStorage.setItem('theme', data.theme || 'default');
      applyTheme(data.theme || 'default');
      navigate('/home');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 24px' }}>
      <div style={{ marginBottom: 48, textAlign: 'center' }}>
        <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>不纠结</div>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>帮你在犹豫时看得更清楚</div>
      </div>

      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label className="form-label">账号</label>
          <input
            className="input"
            type="text"
            placeholder="输入账号"
            value={username}
            onChange={e => setUsername(e.target.value)}
            autoFocus
          />
        </div>

        <div className="form-group">
          <label className="form-label">密码</label>
          <input
            className="input"
            type="password"
            placeholder="输入密码"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </div>

        {error && (
          <div style={{
            padding: '10px 14px',
            background: 'rgba(224, 85, 85, 0.1)',
            border: '1px solid rgba(224, 85, 85, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#e05555',
            fontSize: 13,
            marginBottom: 16
          }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary btn-block btn-lg"
          disabled={loading}
          style={{ marginTop: 24 }}
        >
          {loading ? '登录中...' : '登录'}
        </button>

        <button
          type="button"
          className="btn btn-ghost btn-block"
          style={{ marginTop: 12 }}
          onClick={() => navigate('/register')}
        >
          <Sparkles size={16} /> 还没账号？立即注册
        </button>
      </form>
    </div>
  );
}
