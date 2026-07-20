import { AnimatePresence, motion } from 'framer-motion';

const TYPE_COLORS = {
  error: '#ef4444',
  success: '#10b981',
  info: '#4A7DFF',
};

export default function Toast({ toast }) {
  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          key={toast.message}
          initial={{ opacity: 0, y: -12, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.96 }}
          transition={{ duration: 0.2 }}
          style={{
            position: 'absolute',
            top: 64,
            left: 16,
            right: 16,
            background: TYPE_COLORS[toast.type] || TYPE_COLORS.error,
            color: 'white',
            padding: '12px 16px',
            borderRadius: 12,
            fontSize: 13,
            fontWeight: 500,
            zIndex: 999,
            boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
            textAlign: 'center',
            pointerEvents: 'none',
          }}
        >
          {toast.message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
