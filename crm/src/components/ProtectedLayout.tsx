import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { Role, useAuth } from '../lib/auth-context';

interface Props {
  roles: Role[];
}

const ProtectedLayout = ({ roles }: Props) => {
  const { token, role } = useAuth();
  const location = useLocation();

  if (!token || !role || !roles.includes(role)) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default ProtectedLayout;
