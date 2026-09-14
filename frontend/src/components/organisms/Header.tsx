'use client';

import { MenuIcon, UserCircle, LogOut, Settings as SettingsIcon, User } from 'lucide-react';
import { ThemeToggle } from '@/components/molecules/ThemeToggle';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface HeaderProps {
  onMobileMenuToggle?: () => void;
}

export function Header({ onMobileMenuToggle }: HeaderProps) {
  const pathname = usePathname();
  
  // Hide TAPS branding on execution-summary and module-details pages
  const hideTapsBranding = pathname === '/execution-summary' || pathname === '/module-details';
  
  return (
    <header className="flex h-16 flex-col border-b bg-card">
      {/* Top Row: Mobile Menu Toggle + Logo + Actions */}
      <div className="flex h-16 items-center justify-between px-4 md:px-6">
        {/* Left Section: Mobile Menu Toggle + Logo/Branding */}
        <div className="flex items-center gap-3">
          {/* Mobile Menu Toggle - Only visible on mobile */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onMobileMenuToggle}
            className="md:hidden"
            aria-label="Toggle mobile menu"
          >
            <MenuIcon className="h-6 w-6" />
          </Button>

          {/* Application Logo/Branding - Hidden on execution-summary and module-details */}
          {!hideTapsBranding && (
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
                T
              </div>
              <h1 className="text-xl font-bold tracking-tight">TAPS</h1>
            </div>
          )}
        </div>

        {/* Right Section: Theme Toggle + User Profile */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Profile Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                aria-label="User profile menu"
                className="h-9 w-9"
              >
                <UserCircle className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">User Account</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    user@example.com
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/profile" className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  <span>Profile</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/settings" className="cursor-pointer">
                  <SettingsIcon className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer text-destructive focus:text-destructive" variant="destructive">
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Breadcrumbs removed as per navigation consistency requirements */}
    </header>
  );
}
