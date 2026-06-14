import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Settings, UserMinus, UserPlus, Shield, LogOut, Save, AlertTriangle } from 'lucide-react';
import { groups } from '../api';
import type { GroupDetailOut, InvitationOut } from '../api';
import { useAuth } from '../context/AuthContext';
import { InviteMemberModal } from '../components/groups/InviteMemberModal';

export function GroupSettingsPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  
  const [group, setGroup] = useState<GroupDetailOut | null>(null);
  const [pendingInvites, setPendingInvites] = useState<InvitationOut[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const triggerRefresh = () => setRefreshTrigger(prev => prev + 1);

  useEffect(() => {
    if (!groupId) return;

    setIsLoading(true);
    Promise.all([
      groups.getGroupById(groupId),
      groups.getPendingInvites(groupId).catch(() => []) // non-admins might fail, that's fine
    ])
      .then(([g, invites]) => {
        setGroup(g);
        setPendingInvites(invites);
        setEditName(g.name);
        setEditDescription(g.description || '');
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load group settings.');
      })
      .finally(() => setIsLoading(false));
  }, [groupId, refreshTrigger]);

  const handleSaveGroupInfo = async () => {
    if (!groupId) return;
    setIsEditing(true);
    try {
      await groups.updateGroup(groupId, editName, editDescription);
      triggerRefresh();
      alert('Group updated successfully.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update group.');
    } finally {
      setIsEditing(false);
    }
  };

  const handleCloseGroup = async () => {
    if (!groupId) return;
    if (!window.confirm('Are you absolutely sure you want to CLOSE this group? This action cannot be undone.')) return;
    try {
      await groups.closeGroup(groupId);
      navigate('/dashboard');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to close group.');
    }
  };

  const handleRemoveMember = async (userId: string, name: string) => {
    if (!groupId) return;
    if (!window.confirm(`Are you sure you want to remove ${name} from the group?`)) return;

    try {
      await groups.removeMember(groupId, userId);
      triggerRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove member.');
    }
  };

  const handleLeaveGroup = async () => {
    if (!groupId) return;
    if (!window.confirm('Are you sure you want to leave this group? You will no longer be able to see its expenses.')) return;

    try {
      await groups.leaveGroup(groupId);
      navigate('/dashboard');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to leave group.');
    }
  };

  if (isLoading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading settings...</div>;
  }

  if (error || !group) {
    return <div style={{ padding: '2rem', color: '#ef4444' }}>{error || 'Group not found'}</div>;
  }

  const currentUserMembership = group.members.find(m => m.user_id === currentUser?.id);
  const isAdmin = currentUserMembership?.role === 'ADMIN';

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        borderBottom: '1px solid var(--color-border)',
        paddingBottom: '1rem'
      }}>
        <div>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
            <Link to={`/groups/${groupId}`} style={{ color: 'var(--color-brand)' }}>&larr; Back to group</Link>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Settings size={24} /> Group Settings
          </h1>
        </div>
      </div>

      {isAdmin && (
        <div style={{ backgroundColor: 'white', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', padding: '1.5rem', marginBottom: '2rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: '0 0 1rem 0' }}>General Settings</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '400px' }}>
            <div className="form-group">
              <label>Group Name</label>
              <input 
                type="text" 
                className="form-input" 
                value={editName} 
                onChange={e => setEditName(e.target.value)} 
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <input 
                type="text" 
                className="form-input" 
                value={editDescription} 
                onChange={e => setEditDescription(e.target.value)} 
              />
            </div>
            <div>
              <button 
                className="btn btn-primary" 
                onClick={handleSaveGroupInfo} 
                disabled={isEditing || !editName}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <Save size={16} /> Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ backgroundColor: 'white', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', overflow: 'hidden' }}>
        <div style={{ 
          padding: '1.5rem', 
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0 }}>Members</h3>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>
              Manage who has access to this group.
            </p>
          </div>
          {isAdmin && (
            <button className="btn btn-primary" onClick={() => setIsInviteOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <UserPlus size={16} /> Invite Member
            </button>
          )}
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead style={{ backgroundColor: 'var(--color-bg-surface)', borderBottom: '1px solid var(--color-border)' }}>
            <tr>
              <th style={{ padding: '0.75rem 1.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Name</th>
              <th style={{ padding: '0.75rem 1.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Role</th>
              <th style={{ padding: '0.75rem 1.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {group.members.map(member => (
              <tr key={member.user_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ 
                      width: '32px', height: '32px', borderRadius: '50%', 
                      backgroundColor: 'var(--color-bg-surface)', display: 'flex', 
                      alignItems: 'center', justifyContent: 'center', fontWeight: 600,
                      color: 'var(--color-text-muted)'
                    }}>
                      {member.display_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      {member.display_name}
                      {member.user_id === currentUser?.id && <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 400 }}>(You)</span>}
                    </div>
                  </div>
                </td>
                <td style={{ padding: '1rem 1.5rem' }}>
                  {member.role === 'ADMIN' ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', backgroundColor: '#eff6ff', color: '#1d4ed8', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                      <Shield size={12} /> ADMIN
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Member</span>
                  )}
                </td>
                <td style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>
                  {isAdmin && member.user_id !== currentUser?.id && (
                    <button 
                      onClick={() => handleRemoveMember(member.user_id, member.display_name)}
                      style={{ 
                        color: '#ef4444', 
                        background: 'none', 
                        border: '1px solid #fee2e2', 
                        padding: '0.5rem', 
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'background-color 0.2s'
                      }}
                      title="Remove member"
                      onMouseEnter={e => e.currentTarget.style.backgroundColor = '#fee2e2'}
                      onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <UserMinus size={16} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isAdmin && pendingInvites.length > 0 && (
        <div style={{ backgroundColor: 'white', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', overflow: 'hidden', marginTop: '2rem' }}>
          <div style={{ 
            padding: '1.5rem', 
            borderBottom: '1px solid var(--color-border)',
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: 0 }}>Pending Invitations</h3>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', margin: '0.25rem 0 0' }}>
              Invited users who have not yet accepted.
            </p>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ backgroundColor: 'var(--color-bg-surface)', borderBottom: '1px solid var(--color-border)' }}>
              <tr>
                <th style={{ padding: '0.75rem 1.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Email</th>
                <th style={{ padding: '0.75rem 1.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Status</th>
                <th style={{ padding: '0.75rem 1.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', textAlign: 'right' }}>Sent At</th>
              </tr>
            </thead>
            <tbody>
              {pendingInvites.map(inv => (
                <tr key={inv.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>{inv.invited_email}</td>
                  <td style={{ padding: '1rem 1.5rem' }}>
                    <span style={{ fontSize: '0.75rem', backgroundColor: '#fef3c7', color: '#b45309', padding: '0.25rem 0.5rem', borderRadius: '4px', fontWeight: 600 }}>
                      Pending
                    </span>
                  </td>
                  <td style={{ padding: '1rem 1.5rem', textAlign: 'right', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    {new Date(inv.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          {isAdmin && (
            <button 
              onClick={handleCloseGroup}
              style={{ 
                display: 'flex', alignItems: 'center', gap: '0.5rem', 
                backgroundColor: 'white', color: '#991b1b', 
                border: '1px solid #f87171', padding: '0.75rem 1.5rem', 
                borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer' 
              }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor = '#fef2f2'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor = 'white'}
            >
              <AlertTriangle size={18} /> Close Group
            </button>
          )}
        </div>

        <button 
          onClick={handleLeaveGroup}
          style={{ 
            display: 'flex', alignItems: 'center', gap: '0.5rem', 
            backgroundColor: 'white', color: '#dc2626', 
            border: '1px solid #fca5a5', padding: '0.75rem 1.5rem', 
            borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer' 
          }}
          onMouseEnter={e => e.currentTarget.style.backgroundColor = '#fef2f2'}
          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'white'}
        >
          <LogOut size={18} /> Leave Group
        </button>
      </div>

      <InviteMemberModal  
        isOpen={isInviteOpen} 
        onClose={() => setIsInviteOpen(false)} 
        group={group} 
        onSuccess={triggerRefresh} 
      />
    </div>
  );
}
