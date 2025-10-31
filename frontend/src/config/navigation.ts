export interface NavItem {
  label: string;
  to: string;
  icon: string;
}

export const SCRAPER_NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: 'layout-dashboard' },
  { label: 'Targets', to: '/targets', icon: 'radar' },
  { label: 'Schedules', to: '/schedules', icon: 'calendar-clock' },
  { label: 'Jobs', to: '/jobs', icon: 'workflow' },
  { label: 'Config', to: '/config', icon: 'settings-2' },
  { label: 'Logs', to: '/logs', icon: 'list' },
  { label: 'Snapshots', to: '/snapshots', icon: 'image' },
  { label: 'Quarantine', to: '/quarantine', icon: 'shield-alert' },
  { label: 'Proxies & UAs', to: '/proxies', icon: 'globe' },
  { label: 'Settings', to: '/settings', icon: 'sliders' },
];
