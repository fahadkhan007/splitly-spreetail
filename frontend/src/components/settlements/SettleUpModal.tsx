import { useState } from 'react';
import { X } from 'lucide-react';
import { settlements } from '../../api';
import type { GroupDetailOut } from '../../api';

interface SettleUpModalProps {
  isOpen: boolean;
  onClose: () => void;
  group: GroupDetailOut;
  onSuccess: () => void;
}

export function SettleUpModal({ isOpen, onClose, group, onSuccess }: SettleUpModalProps) {
  const [payerId, setPayerId] = useState('');
  const [payeeId, setPayeeId] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!payerId || !payeeId || !amount || !date) {
      setError('Please fill in all required fields.');
      return;
    }
    if (payerId === payeeId) {
      setError('Payer and payee cannot be the same person.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await settlements.createSettlement(group.id, {
        payer_user_id: payerId,
        payee_user_id: payeeId,
        amount: parseFloat(amount),
        currency: group.base_currency,
        settlement_date: date,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to record settlement.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        width: '100%',
        maxWidth: '400px',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--color-border)'
        }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0 }}>Settle up</h2>
          <button onClick={onClose} style={{ color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
          {error && (
            <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Who paid?</label>
              <select className="form-input" value={payerId} onChange={e => setPayerId(e.target.value)} required>
                <option value="">Select member...</option>
                {group.members.map(m => (
                  <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                ))}
              </select>
            </div>
            <div style={{ color: 'var(--color-text-muted)', fontWeight: 600, paddingTop: '1.5rem' }}>&rarr;</div>
            <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Who received?</label>
              <select className="form-input" value={payeeId} onChange={e => setPayeeId(e.target.value)} required>
                <option value="">Select member...</option>
                {group.members.map(m => (
                  <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Amount ({group.base_currency})</label>
            <input 
              type="number" 
              className="form-input" 
              step="0.01" 
              min="0.01"
              value={amount} 
              onChange={e => setAmount(e.target.value)} 
              required 
              placeholder="0.00"
            />
          </div>

          <div className="form-group">
            <label>Date</label>
            <input 
              type="date" 
              className="form-input" 
              value={date} 
              onChange={e => setDate(e.target.value)} 
              required 
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '2rem' }}>
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
