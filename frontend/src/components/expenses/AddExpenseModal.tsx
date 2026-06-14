import { useState } from 'react';
import { X, Users, DollarSign, Percent, PieChart } from 'lucide-react';
import { expenses } from '../../api';
import type { GroupDetailOut, SplitType, SplitInput } from '../../api';

interface AddExpenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  group: GroupDetailOut;
  onSuccess: () => void;
}

export function AddExpenseModal({ isOpen, onClose, group, onSuccess }: AddExpenseModalProps) {
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState(group.base_currency);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [paidByUserId, setPaidByUserId] = useState('');
  const [splitType, setSplitType] = useState<SplitType>('EQUAL');
  
  // To handle custom splits:
  // For EQUAL: we can default to all members (empty array sent to backend). But let's let them uncheck members.
  // For others: we need values.
  const [selectedMembers, setSelectedMembers] = useState<Set<string>>(new Set(group.members.map(m => m.user_id)));
  const [splitValues, setSplitValues] = useState<Record<string, string>>({});

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleToggleMember = (userId: string) => {
    const newSet = new Set(selectedMembers);
    if (newSet.has(userId)) {
      newSet.delete(userId);
      // Remove their split value if any
      const newVals = { ...splitValues };
      delete newVals[userId];
      setSplitValues(newVals);
    } else {
      newSet.add(userId);
    }
    setSelectedMembers(newSet);
  };

  const handleSplitValueChange = (userId: string, val: string) => {
    setSplitValues(prev => ({ ...prev, [userId]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description || !amount || !currency || !date || !paidByUserId) {
      setError('Please fill in all required fields.');
      return;
    }

    if (selectedMembers.size === 0) {
      setError('You must select at least one member to split with.');
      return;
    }

    setIsLoading(true);
    setError('');

    // Prepare splits payload
    let splitsPayload: SplitInput[] = [];

    if (splitType === 'EQUAL') {
      // If EQUAL and all members are selected, we can send empty array to backend.
      if (selectedMembers.size === group.members.length) {
        splitsPayload = [];
      } else {
        // Send selected members with value 0
        splitsPayload = Array.from(selectedMembers).map(uid => ({ user_id: uid, value: 0 }));
      }
    } else {
      // For UNEQUAL, PERCENTAGE, SHARE, we need values
      for (const uid of Array.from(selectedMembers)) {
        const val = parseFloat(splitValues[uid] || '0');
        splitsPayload.push({ user_id: uid, value: val });
      }
    }

    try {
      await expenses.createExpense(group.id, {
        description,
        amount: parseFloat(amount),
        currency,
        expense_date: date,
        paid_by_user_id: paidByUserId,
        split_type: splitType,
        splits: splitsPayload
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create expense.');
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
        maxWidth: '500px',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--color-border)'
        }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0 }}>Add an expense</h2>
          <button onClick={onClose} style={{ color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
          <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
            {error && (
              <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.875rem' }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group" style={{ flex: 2, marginBottom: 0 }}>
                <label>Description</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={description} 
                  onChange={e => setDescription(e.target.value)} 
                  required 
                  placeholder="e.g. Dinner, Groceries"
                />
              </div>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label>Date</label>
                <input 
                  type="date" 
                  className="form-input" 
                  value={date} 
                  onChange={e => setDate(e.target.value)} 
                  required 
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="form-group" style={{ flex: 2, marginBottom: 0 }}>
                <label>Amount</label>
                <div style={{ position: 'relative' }}>
                  <span style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }}>$</span>
                  <input 
                    type="number" 
                    className="form-input" 
                    style={{ paddingLeft: '2rem' }}
                    step="0.01" 
                    min="0.01"
                    value={amount} 
                    onChange={e => setAmount(e.target.value)} 
                    required 
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label>Currency</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={currency} 
                  onChange={e => setCurrency(e.target.value.toUpperCase())} 
                  required 
                  maxLength={3}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Paid by</label>
              <select className="form-input" value={paidByUserId} onChange={e => setPaidByUserId(e.target.value)} required>
                <option value="">Select member...</option>
                {group.members.map(m => (
                  <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <label style={{ marginBottom: '0.5rem', display: 'block' }}>Split Type</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
                <button 
                  type="button" 
                  className={`btn ${splitType === 'EQUAL' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
                  onClick={() => setSplitType('EQUAL')}
                >
                  <Users size={16} /> Equal
                </button>
                <button 
                  type="button" 
                  className={`btn ${splitType === 'UNEQUAL' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
                  onClick={() => setSplitType('UNEQUAL')}
                >
                  <DollarSign size={16} /> Exact
                </button>
                <button 
                  type="button" 
                  className={`btn ${splitType === 'PERCENTAGE' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
                  onClick={() => setSplitType('PERCENTAGE')}
                >
                  <Percent size={16} /> Percent
                </button>
                <button 
                  type="button" 
                  className={`btn ${splitType === 'SHARE' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
                  onClick={() => setSplitType('SHARE')}
                >
                  <PieChart size={16} /> Shares
                </button>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
              <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-main)', display: 'block', marginBottom: '0.5rem' }}>
                Split among:
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {group.members.map(m => (
                  <div key={m.user_id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <input 
                      type="checkbox" 
                      checked={selectedMembers.has(m.user_id)}
                      onChange={() => handleToggleMember(m.user_id)}
                      style={{ width: '16px', height: '16px', accentColor: 'var(--color-brand)' }}
                    />
                    <span style={{ flex: 1, fontSize: '0.875rem', color: selectedMembers.has(m.user_id) ? 'var(--color-text-main)' : 'var(--color-text-muted)' }}>
                      {m.display_name}
                    </span>
                    
                    {splitType !== 'EQUAL' && selectedMembers.has(m.user_id) && (
                      <div style={{ width: '100px' }}>
                        <input 
                          type="number"
                          className="form-input"
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem', height: '30px' }}
                          placeholder={splitType === 'PERCENTAGE' ? '%' : splitType === 'SHARE' ? 'shares' : '0.00'}
                          value={splitValues[m.user_id] || ''}
                          onChange={e => handleSplitValueChange(m.user_id, e.target.value)}
                          step="0.01"
                          required
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem', padding: '1.25rem 1.5rem', borderTop: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-surface)' }}>
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
