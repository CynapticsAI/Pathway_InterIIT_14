'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { usePortfolio } from '@/contexts/PortfolioContext';
import { MainLayout } from '@/components/layout/MainLayout';
import { PortfolioStats } from '@/components/portfolio/PortfolioStats';
import { StocksList } from '@/components/portfolio/StocksList';
import { AddStockForm } from '@/components/portfolio/AddStockForm';
import { CSVUploader } from '@/components/portfolio/CSVUploader';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { cn } from '@/lib/utils';

export default function PortfolioPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthContext();
  const { portfolio, refreshPortfolio } = usePortfolio();
  const [showAddStock, setShowAddStock] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  if (authLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[70vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--color-primary)]"></div>
        </div>
      </MainLayout>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <MainLayout>
      <div className="h-full overflow-y-auto">
        {/* Header */}
        <div className={cn(
          'bg-[var(--color-surface)]',
          'elevation-2',
          'sticky top-0 z-10'
        )}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-[var(--color-foreground)]">
                  My Portfolio
                </h1>
                <p className="text-[var(--color-muted)] mt-1">
                  Track your stock holdings with real-time P&L
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  onClick={() => setShowAddStock(!showAddStock)}
                  variant={showAddStock ? "secondary" : "primary"}
                >
                  <Icon name={showAddStock ? "close" : "plus"} size="sm" className="mr-2" />
                  {showAddStock ? 'Cancel' : 'Add Stock'}
                </Button>
                <Button
                  onClick={refreshPortfolio}
                  variant="secondary"
                >
                  <Icon name="refresh" size="sm" className="mr-2" />
                  Refresh
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-8 pb-8">
            {/* Portfolio Statistics */}
            <section>
              <PortfolioStats />
            </section>

            {/* Add Stock Section - Conditionally Rendered */}
            {showAddStock && (
              <div className="space-y-6">
                {/* Add Stock Form */}
                <section>
                  <AddStockForm />
                </section>

                {/* CSV Uploader */}
                <section>
                  <CSVUploader />
                </section>
              </div>
            )}

            {/* Stocks List */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-[var(--color-foreground)]">
                  Holdings
                </h2>
                <p className="text-sm text-[var(--color-muted)]">
                  {portfolio?.total_stocks || 0} stocks
                </p>
              </div>
              <StocksList />
            </section>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
