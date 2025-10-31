import { LayoutDashboard, MessagesSquare, Users, CalendarClock, Megaphone, FileText, Settings, ClipboardCheck, Inbox } from 'lucide-react';

import type { UserRole } from '@/contexts/AuthContext';

export interface NavigationItem {
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  path: string;
  roles?: UserRole[];
}

export const NAVIGATION_ITEMS: NavigationItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { label: 'Inbox', icon: Inbox, path: '/inbox' },
  { label: 'Leads', icon: MessagesSquare, path: '/leads' },
  { label: 'Calendar', icon: CalendarClock, path: '/calendar' },
  { label: 'Campaigns', icon: Megaphone, path: '/campaigns' },
  { label: 'Quotes & Invoices', icon: FileText, path: '/quotes' },
  { label: 'Review Queue', icon: ClipboardCheck, path: '/review-queue', roles: ['admin', 'manager', 'tech'] },
  { label: 'Content', icon: Users, path: '/content', roles: ['admin', 'manager'] },
  { label: 'Settings', icon: Settings, path: '/settings', roles: ['admin'] }
];
