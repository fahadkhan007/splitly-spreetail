import { Routes, Route } from 'react-router-dom';
import { Landing } from './pages/Landing';
import { MainLayout } from './layouts/MainLayout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { GroupView } from './pages/GroupView';
import { GroupSettingsPage } from './pages/GroupSettingsPage';
import { ImportPage } from './pages/ImportPage';
import { ReportsPage } from './pages/ReportsPage';
import { AcceptInvitePage } from './pages/AcceptInvitePage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected Layout */}
      <Route element={<MainLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/groups/:groupId/settings" element={<GroupSettingsPage />} />
        <Route path="/groups/:groupId/import" element={<ImportPage />} />
        <Route path="/groups/:groupId/reports" element={<ReportsPage />} />
        <Route path="/groups/:groupId" element={<GroupView />} />
        <Route path="/invitations/accept" element={<AcceptInvitePage />} />
        <Route path="*" element={<div style={{ padding: '2rem' }}>404 Not Found</div>} />
      </Route>
    </Routes>
  );
}

export default App;
