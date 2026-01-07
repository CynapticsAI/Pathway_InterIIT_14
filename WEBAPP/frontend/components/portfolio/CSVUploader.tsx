/**
 * CSV Uploader Component - Modern Design
 * 
 * Updated with elevation, semantic colors, and improved styling
 */

'use client';

import React, { useState, useRef } from 'react';
import { usePortfolio } from '@/contexts/PortfolioContext';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { cn } from '@/lib/utils';
import type { BulkUploadData, BulkUploadResponse } from '@/types/portfolio';

export function CSVUploader() {
  const { bulkUpload, isLoading } = usePortfolio();
  const [uploadResult, setUploadResult] = useState<BulkUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const parseCSV = (csvText: string): BulkUploadData['stocks'] => {
    const lines = csvText.trim().split('\n');
    
    if (lines.length < 2) {
      throw new Error('CSV file must contain header and at least one data row');
    }

    const header = lines[0].toLowerCase().split(',').map((h) => h.trim());
    const symbolIndex = header.indexOf('symbol');
    const quantityIndex = header.indexOf('quantity');
    const costBasisIndex = header.indexOf('cost_basis');

    if (symbolIndex === -1 || quantityIndex === -1 || costBasisIndex === -1) {
      throw new Error('CSV must have columns: symbol, quantity, cost_basis');
    }

    const stocks: BulkUploadData['stocks'] = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const values = line.split(',').map((v) => v.trim());
      
      const symbol = values[symbolIndex];
      const quantity = parseFloat(values[quantityIndex]);
      const cost_basis = parseFloat(values[costBasisIndex]);

      if (!symbol || isNaN(quantity) || isNaN(cost_basis)) {
        throw new Error(`Invalid data at line ${i + 1}`);
      }

      stocks.push({
        symbol: symbol.toUpperCase(),
        quantity,
        cost_basis,
      });
    }

    return stocks;
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setUploadResult(null);

    // Check file type
    if (!file.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }

    // Check file size (max 1MB)
    if (file.size > 1024 * 1024) {
      setError('File size must be less than 1MB');
      return;
    }

    try {
      const text = await file.text();
      const stocks = parseCSV(text);

      if (stocks.length === 0) {
        setError('No valid stocks found in CSV');
        return;
      }

      // Upload to backend
      const result = await bulkUpload({ stocks });
      setUploadResult(result);

      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      console.error('CSV upload error:', err);
      setError(err?.message || 'Failed to process CSV file');
    }
  };

  const handleDismissResult = () => {
    setUploadResult(null);
    setError(null);
  };

  return (
    <div className={cn(
      'bg-[var(--color-surface)]',
      'rounded-lg elevation-2 p-6'
    )}>
      <h3 className="text-lg font-semibold mb-4 text-[var(--color-foreground)]">Bulk Import from CSV</h3>
      
      <div className="space-y-4">
        {/* File Input */}
        <div>
          <label
            htmlFor="csv-upload"
            className="block text-sm font-medium text-[var(--color-foreground)] mb-2"
          >
            Upload CSV File
          </label>
          <input
            ref={fileInputRef}
            type="file"
            id="csv-upload"
            accept=".csv"
            onChange={handleFileChange}
            disabled={isLoading}
            className="block w-full text-sm text-[var(--color-foreground)] file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-[var(--color-primary)] file:text-white hover:file:bg-[var(--color-primary-hover)] file:cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <p className="text-xs text-[var(--color-muted)] mt-1">
            Expected format: symbol,quantity,cost_basis
          </p>
        </div>

        {/* CSV Format Example */}
        <div className={cn(
          'bg-[var(--color-surface-elevated)]',
          'rounded-lg elevation-1 p-4'
        )}>
          <p className="text-sm font-medium text-[var(--color-foreground)] mb-2">CSV Example:</p>
          <pre className="text-xs text-[var(--color-muted)] font-mono overflow-x-auto">
{`symbol,quantity,cost_basis
NVDA,50,85.00
TSLA,60,195.50
AAPL,85,150.25
MSFT,45,315.00
AMZN,100,130.80`}
          </pre>
        </div>

        {/* Error Message */}
        {error && (
          <div className={cn(
            'bg-[var(--color-danger)]/10',
            'rounded-lg elevation-1 p-4'
          )}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Icon name="alert" size={18} className="text-[var(--color-danger)]" />
                  <p className="text-sm font-medium text-[var(--color-danger)]">Error</p>
                </div>
                <p className="text-sm text-[var(--color-danger)] opacity-90 ml-6">{error}</p>
              </div>
              <Button
                onClick={handleDismissResult}
                variant="ghost"
                size="sm"
                className="text-[var(--color-danger)] hover:text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10"
              >
                <Icon name="close" size={18} />
              </Button>
            </div>
          </div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <div className={cn(
            'bg-[var(--color-success)]/10',
            'rounded-lg elevation-1 p-4'
          )}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Icon name="check" size={18} className="text-[var(--color-success)]" />
                  <p className="text-sm font-medium text-[var(--color-success)]">Upload Complete</p>
                </div>
                <div className="text-sm text-[var(--color-success)] opacity-90 ml-6 mt-2 space-y-1">
                  <div className="flex items-center gap-2">
                    <Icon name="check" size={14} />
                    <p>Created: {uploadResult.created} stocks</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Icon name="check" size={14} />
                    <p>Updated: {uploadResult.updated} stocks</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Icon name="check" size={14} />
                    <p>Total: {uploadResult.total_processed} processed</p>
                  </div>
                  {uploadResult.errors.length > 0 && (
                    <div className="mt-2">
                      <p className="font-medium">Errors:</p>
                      <ul className="list-disc list-inside ml-2">
                        {uploadResult.errors.map((err, i) => (
                          <li key={i} className="text-[var(--color-danger)]">
                            {err.symbol}: {err.error}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
              <Button
                onClick={handleDismissResult}
                variant="ghost"
                size="sm"
                className="text-[var(--color-success)] hover:text-[var(--color-success)] hover:bg-[var(--color-success)]/10"
              >
                <Icon name="close" size={18} />
              </Button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-4">
            <Icon name="refresh" size={32} className="animate-spin text-[var(--color-primary)]" />
            <span className="ml-3 text-sm text-[var(--color-muted)]">
              Uploading stocks...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
