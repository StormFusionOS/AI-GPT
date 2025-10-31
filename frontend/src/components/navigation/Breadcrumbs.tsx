import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

const PATH_LABELS: Record<string, string> = {
  '/': 'Dashboard',
  '/targets': 'Targets',
  '/schedules': 'Schedules',
  '/jobs': 'Jobs',
  '/config': 'Config',
  '/logs': 'Logs',
  '/media': 'Media & Backups',
  '/snapshots': 'Snapshots',
  '/quarantine': 'Quarantine',
  '/proxies': 'Proxies & UAs',
  '/settings': 'Settings',
};

interface BreadcrumbsProps {
  pathname: string;
}

export function Breadcrumbs({ pathname }: BreadcrumbsProps) {
  const segments = pathname.split('/').filter(Boolean);
  const crumbs = segments.length === 0 ? ['/'] : segments.map((_, index, arr) => `/${arr.slice(0, index + 1).join('/')}`);

  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center gap-1 text-sm text-muted-foreground">
        {crumbs.map((path, index) => {
          const label = PATH_LABELS[path] ?? path.replace('/', '');
          const isLast = index === crumbs.length - 1;
          return (
            <li key={path} className="flex items-center gap-1">
              {!isLast ? (
                <Link to={path} className="transition-colors hover:text-foreground">
                  {label}
                </Link>
              ) : (
                <span className={cn('text-foreground')}>{label}</span>
              )}
              {!isLast && <span>/</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
