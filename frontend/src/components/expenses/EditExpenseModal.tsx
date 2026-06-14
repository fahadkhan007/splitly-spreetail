import { useState, useEffect } from 'react';
import { X, Edit3 } from 'lucide-react';
import { expenses } from '../../api';
import type { ExpenseOut, GroupDetailOut } from '../../api';

interface EditExpenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  group: GroupDetailOut;
  expense: ExpenseOut | null;
  onSuccess: () => void;
}

export function EditExpenseModal({ isOpen, onClose, group, expense, onSuccess }: EditExpenseModalProps) {
  const [description, setDescription] = useState('');
  const [expenseDate, setExpenseDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (expense && isOpen) {
      setDescription(expense.description);
      setExpenseDate(expense.expense_date.split('T')[0]); // format for input type="date"
    }
  }, [expense, isOpen]);

  if (!isOpen || !expense) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description || !expenseDate) {
      setError('Please provide a description and a date.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await expenses.updateExpense(group.id, expense.id, {
        description,
        expense_date: expenseDate,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update expense.');
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
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Edit3 size={20} /> Edit Expense
          </h2>
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

          <div className="form-group">
            <label>Description</label>
            <input 
              type="text" 
              className="form-input" 
              value={description} 
              onChange={e => setDescription(e.target.value)} 
              required 
            />
          </div>

          <div className="form-group">
            <label>Date</label>
            <input 
              type="date" 
              className="form-input" 
              value={expenseDate} 
              onChange={e => setExpenseDate(e.target.value)} 
              required 
            />
          </div>

          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
            Note: You cannot change the amount or split of an existing expense. If those are incorrect, delete this expense and create a new one.
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
