import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  GraduationCap, 
  Home, 
  Search, 
  TrendingUp, 
  User, 
  LogOut,
  Settings,
  BookOpen,
  Users,
  Menu,
  Info,
  LogIn
} from 'lucide-react';
import { Chatbot } from './shared/Chatbot';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigationItems = [
    { path: '/home', label: 'Home', icon: Home, auth: true },
    { path: '/courses', label: 'Courses', icon: BookOpen, auth: false },
    //{ path: '/search', label: 'Search', icon: Search, auth: true },
    { path: '/progress', label: 'Progress', icon: TrendingUp, auth: true },
    { path: '/about-us', label: 'About Us', icon: Users, auth: false },
  ];

  const publicNavItems = navigationItems.filter(item => !item.auth);
  const privateNavItems = navigationItems.filter(item => item.auth);

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex min-h-screen w-full flex-col bg-gray-50">
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between gap-4 border-b bg-white px-4 md:px-6">
        <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
          <Link
            to="/home"
            className="flex items-center gap-2 text-lg font-semibold md:text-base"
          >
            <GraduationCap className="h-6 w-6" />
            <span className="font-bold">NovaLearn</span>
          </Link>
          {(user ? navigationItems : publicNavItems).map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`transition-colors hover:text-foreground ${
                isActive(item.path)
                  ? 'text-foreground'
                  : 'text-muted-foreground'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        
        <div className="flex items-center gap-4 md:ml-auto md:gap-2 lg:gap-4">
          {user ? (
            <Button onClick={handleLogout} variant="outline">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          ) : (
            <Button asChild>
              <Link to="/login">
                <LogIn className="h-4 w-4 mr-2" />
                Login
              </Link>
            </Button>
          )}
        </div>
      </header>

      <main className="flex-1 p-4 md:p-6 lg:p-8">
        {children}
      </main>
      <Chatbot />
    </div>
  );
};

export default Layout;
