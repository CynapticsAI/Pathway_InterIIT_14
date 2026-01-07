'use client';

import { useState, useEffect, ReactNode } from 'react';
import { TopNavBar } from './TopNavBar';
import { Sidebar } from './Sidebar';
import { AuthModal } from '../auth/AuthModal';
import { Greet } from '../greeting';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [showGreeting, setShowGreeting] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeMenuItem, setActiveMenuItem] = useState('home');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');

  useEffect(() => {
    // Check if greeting has been shown in this session
    const greetingShown = sessionStorage.getItem('greetingShown');
    
    if (!greetingShown) {
      // Show greeting only if it hasn't been shown this session
      setShowGreeting(true);
      
      const timer = setTimeout(() => {
        setShowGreeting(false);
        // Mark greeting as shown for this session
        sessionStorage.setItem('greetingShown', 'true');
      }, 2500);

      return () => clearTimeout(timer);
    }
  }, []);

  const handleLogin = () => {
    setAuthMode('login');
    setIsAuthModalOpen(true);
  };

  const handleSignup = () => {
    setAuthMode('signup');
    setIsAuthModalOpen(true);
  };

  const handleSwitchAuthMode = () => {
    setAuthMode(authMode === 'login' ? 'signup' : 'login');
  };

  const handleMenuItemClick = (id: string) => {
    setActiveMenuItem(id);
    // Future: Handle other menu items as needed
  };

  if (showGreeting) {
    return <Greet />;
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      {/* Top Navigation Bar */}
      <TopNavBar
        onMenuClick={() => setIsSidebarOpen(!isSidebarOpen)}
        onLogin={handleLogin}
        onSignup={handleSignup}
      />

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        activeItem={activeMenuItem}
        onItemClick={handleMenuItemClick}
      />

      {/* Main Content Area */}
      <main className="
        pt-16 lg:pl-16
        min-h-screen
        transition-all duration-300
      ">
        <div className="h-[calc(100vh-4rem)]">
          {children}
        </div>
      </main>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        mode={authMode}
        onSwitchMode={handleSwitchAuthMode}
      />
    </div>
  );
}
