import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2, Pencil, Check, X } from 'lucide-react';
import { getMemories, deleteMemory, updateCoreMemory } from '../api';
import Toast from '../components/Toast';
import { useToast } from '../hooks/useToast';

const TABS = [
  { key: 'episode', label: '历史回顾' },
  { key: 'core', label: '个人档案' },
];

export default function Memories() {
  const navigate = useNavigate();
  const uid = localStorage.getItem('uid');
  const [tab, setTab] = useState('episode');
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [toast, showToast] = useToast();

  useEffect(() => {
    if (!uid) { navigate('/'); return; }
    load();
  }, [tab]);

  const load = async () => {
    setLoading(true);
    setEditingId(null);
    setConfirmDeleteId(null);
    try {
      const data = await getMemories(uid, tab);
      setMemories(data.memories || []);
    } catch (e) {
      showToast('加载失败，请重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (memoryId) => {
    setDeletingId(memoryId);
    setConfirmDeleteId(null);
    try {
      await deleteMemory(uid, tab, [memoryId]);
      setMemories(prev => prev.filter(m => (m.id ?? m._id) !== memoryId));
    } catch (e) {
      showToast('删除失败，请重试', 'error');
    } finally {
      setDeletingId(null);
    }
  };

  const startEdit = (memory, index) => {
    const id = memory.id ?? memory._id ?? index;
    setEditingId(id);
    setEditContent(memory.content);
  };

  const saveEdit = async (memory) => {
    const id = memory.id ?? memory._id;
    const updated = memories.map(m =>
      (m.id ?? m._id) === id ? { ...m, content: editContent } : m
    );
    try {
      await updateCoreMemory(uid, updated.map(m => ({
        content: m.content,
        tags: m.tags || [],
      })));
      setMemories(updated);
      setEditingId(null);
      showToast('已保存', 'success');
    } catch (e) {
      showToast('保存失败，请重试', 'error');
    }
  };

  const formatTime = (ts) => {
    if (!ts) return null;
    const ms = ts > 1e12 ? ts : ts * 1000;
    return new Date(ms).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  const getId = (memory, i) => memory.id ?? memory._id ?? i;

  const renderMemory = (memory, i) => {
    const id = getId(memory, i);
    const isEditing = editingId === id;
    const isDeleting = deletingId === id;
    const isConfirming = confirmDeleteId === id;

    return (
      <div key={id} style={{
        background: 'var(--bg-primary)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '14px 16px',
        marginBottom: 10,
      }}>
        {isEditing ? (
          <>
            <textarea
              className="input"
              value={editContent}
              onChange={e => setEditContent(e.target.value)}
              rows={3}
              style={{ resize: 'none', marginBottom: 10, fontSize: 14 }}
              autoFocus
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary"
                style={{ flex: 1, padding: '8px 0', fontSize: 13, gap: 4 }}
                onClick={() => saveEdit(memory)}
              >
                <Check size={13} /> 保存
              </button>
              <button
                className="btn btn-ghost"
                style={{ flex: 1, padding: '8px 0', fontSize: 13, gap: 4 }}
                onClick={() => setEditingId(null)}
              >
                <X size={13} /> 取消
              </button>
            </div>
          </>
        ) : (
          <>
            <div style={{ fontSize: 14, lineHeight: 1.65, color: 'var(--text-primary)', marginBottom: 8 }}>
              {memory.content}
            </div>
            {memory.tags?.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                {memory.tags.map((tag, ti) => (
                  <span key={ti} style={{
                    fontSize: 11, padding: '2px 8px', borderRadius: 10,
                    background: 'var(--bg-elevated)', color: 'var(--text-muted)',
                  }}>{tag}</span>
                ))}
              </div>
            )}

            {isConfirming ? (
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                paddingTop: 8, borderTop: '1px solid var(--border)',
              }}>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>确认删除这条记忆？</span>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    className="navbar-btn"
                    style={{ fontSize: 12, color: 'var(--text-muted)', padding: '4px 10px', height: 'auto', borderRadius: 6 }}
                    onClick={() => setConfirmDeleteId(null)}
                  >
                    取消
                  </button>
                  <button
                    className="navbar-btn"
                    style={{ fontSize: 12, color: 'white', background: '#ef4444', padding: '4px 10px', height: 'auto', borderRadius: 6 }}
                    disabled={isDeleting}
                    onClick={() => handleDelete(id)}
                  >
                    {isDeleting ? '删除中...' : '删除'}
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  {formatTime(memory.createdAt || memory.created_at)}
                </span>
                <div style={{ display: 'flex', gap: 4 }}>
                  {tab === 'core' && (
                    <button
                      className="navbar-btn"
                      style={{ color: 'var(--text-muted)', width: 30, height: 30 }}
                      onClick={() => startEdit(memory, i)}
                    >
                      <Pencil size={14} />
                    </button>
                  )}
                  <button
                    className="navbar-btn"
                    style={{ color: '#e05555', width: 30, height: 30 }}
                    onClick={() => setConfirmDeleteId(id)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <div className="page">
      <Toast toast={toast} />
      <div className="navbar">
        <button className="navbar-btn" onClick={() => navigate('/home')}>
          <ArrowLeft size={20} />
        </button>
        <div style={{ flex: 1, textAlign: 'center', fontWeight: 600, fontSize: 16 }}>我的记忆</div>
        <div style={{ width: 36 }} />
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              flex: 1, background: 'none', border: 'none', padding: '11px 0',
              fontSize: 13,
              color: tab === t.key ? 'var(--accent)' : 'var(--text-muted)',
              borderBottom: tab === t.key ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer', transition: 'color 0.15s',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="scroll-area">
        {loading ? (
          <div className="empty-state"><p style={{ color: 'var(--text-muted)' }}>加载中...</p></div>
        ) : memories.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🧠</div>
            <p>暂无{TABS.find(t => t.key === tab)?.label}</p>
          </div>
        ) : (
          <div style={{ paddingTop: 8 }}>
            {memories.map((m, i) => renderMemory(m, i))}
          </div>
        )}
      </div>
    </div>
  );
}
