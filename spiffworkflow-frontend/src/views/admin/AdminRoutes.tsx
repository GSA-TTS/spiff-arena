import { Route, Routes } from 'react-router-dom';
import AdminGroupList from './AdminGroupList';
import AdminGroupNew from './AdminGroupNew';
import AdminGroupShow from './AdminGroupShow';
import AdminPendingMembers from './AdminPendingMembers';
import AdminDashboard from './AdminDashboard';
import AdminProcessInstanceTasks from './AdminProcessInstanceTasks';

export default function AdminRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AdminDashboard />} />
      <Route path="groups" element={<AdminGroupList />} />
      <Route path="groups/new" element={<AdminGroupNew />} />
      <Route path="groups/:group_id" element={<AdminGroupShow />} />
      <Route path="pending" element={<AdminPendingMembers />} />
      <Route
        path="process-instances/:process_instance_id/tasks"
        element={<AdminProcessInstanceTasks />}
      />
    </Routes>
  );
}
