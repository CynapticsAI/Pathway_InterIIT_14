'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Icon, IconName } from '../ui/Icon';
import { cn } from '@/lib/utils';

interface MenuItem {
  id: string;
  label: string;
  icon: IconName;
  path?: string;
  badge?: number;
}

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
  activeItem?: string;
  onItemClick?: (id: string) => void;
}

const menuItems: MenuItem[] = [
  { id: 'home', label: 'Home', icon: 'home', path: '/' },
  { id: 'portfolio', label: 'Portfolio', icon: 'briefcase', path: '/portfolio' },
  { id: 'notifications', label: 'Notifications', icon: 'bell', path: '/notifications' },
];

const bottomItems: MenuItem[] = [
  { id: 'settings', label: 'Settings', icon: 'settings', path: '/settings' },
];

export function Sidebar({ isOpen, onClose, activeItem = 'home', onItemClick }: SidebarProps) {
  const [isHovered, setIsHovered] = useState(false);
  const pathname = usePathname();
  const isExpanded = isOpen || isHovered;

  const handleItemClick = (id: string) => {
    onItemClick?.(id);
    if (window.innerWidth < 1024) {
      onClose?.();
    }
  };

  const isItemActive = (item: MenuItem) => {
    if (item.path) {
      return pathname === item.path;
    }
    return activeItem === item.id;
  };

  return (
    <>
      <aside
        className={cn(
          'fixed left-0 top-16 bottom-0',
          'bg-[var(--color-surface)]',
          'border-r border-[var(--color-border)]',
          'transition-all duration-300 ease-in-out',
          'z-40 elevation-2',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
          isExpanded ? 'w-60' : 'w-16'
        )}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="flex flex-col h-full py-4">
          <nav className="flex-1 px-2 space-y-1">
            {menuItems.map((item) => {
              const active = isItemActive(item);
              return (
                <Link
                  key={item.id}
                  href={item.path || '#'}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
                    'transition-smooth group relative',
                    active
                      ? 'bg-[var(--color-primary)] text-white elevation-2' 
                      : 'text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                  )}
                >
                  <Icon name={item.icon} size="sm" className="flex-shrink-0" />
                  <span className={cn('text-sm', isExpanded ? 'opacity-100' : 'opacity-0 w-0')}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>
          <div className="px-2 my-2">
            <div className="border-t border-[var(--color-border)]" />
          </div>
          <nav className="px-2 space-y-1">
            {bottomItems.map((item) => {
              const active = isItemActive(item);
              return (
                <Link
                  key={item.id}
                  href={item.path || '#'}
                  onClick={() => handleItemClick(item.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
                    'transition-smooth group relative',
                    active
                      ? 'bg-[var(--color-primary)] text-white elevation-2' 
                      : 'text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                  )}
                >
                  <Icon name={item.icon} size="sm" className="flex-shrink-0" />
                  <span className={cn('text-sm', isExpanded ? 'opacity-100' : 'opacity-0 w-0')}>
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>
    </>
  );
}
