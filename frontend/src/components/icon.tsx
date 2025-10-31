import * as React from 'react';
import {
  CalendarClock,
  Globe2,
  Image as ImageIcon,
  LayoutDashboard,
  List,
  Radar,
  Settings2,
  ShieldAlert,
  Sliders,
  Workflow,
} from 'lucide-react';

const iconMap = {
  'layout-dashboard': LayoutDashboard,
  radar: Radar,
  'calendar-clock': CalendarClock,
  workflow: Workflow,
  settings: Settings2,
  'settings-2': Settings2,
  list: List,
  image: ImageIcon,
  'shield-alert': ShieldAlert,
  globe: Globe2,
  sliders: Sliders,
} as const;

export type IconName = keyof typeof iconMap;

interface IconProps extends React.SVGProps<SVGSVGElement> {
  name: string;
  className?: string;
}

export function Icon({ name, ...props }: IconProps) {
  const Component = iconMap[name as IconName] ?? LayoutDashboard;
  return <Component aria-hidden="true" {...props} />;
}
