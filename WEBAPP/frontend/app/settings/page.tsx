'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { useTheme } from '@/components/theme/ThemeProvider';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { cn } from '@/lib/utils';
import type { ThemeName } from '@/lib/themes';
import { userService } from '@/lib/api/userService';
import type { UserSettings } from '@/lib/api/types';

export default function SettingsPage() {
  const { isDark, toggleTheme, colorTheme, setColorTheme } = useTheme();
  
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [settingsSuccess, setSettingsSuccess] = useState<string | null>(null);

  const [drawdown, setDrawdown] = useState(20.0);
  const [beta, setBeta] = useState(1.0);
  const [hurdleRate, setHurdleRate] = useState(8.0);
  const [sectorLimits, setSectorLimits] = useState<Record<string, number>>({});
  const [whitelist, setWhitelist] = useState<string[]>([]);
  const [blacklist, setBlacklist] = useState<string[]>([]);
  
  const [newWhitelistDomain, setNewWhitelistDomain] = useState('');
  const [newBlacklistDomain, setNewBlacklistDomain] = useState('');
  const [newSectorName, setNewSectorName] = useState('');
  const [newSectorLimit, setNewSectorLimit] = useState(10.0);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setIsLoadingSettings(true);
      setSettingsError(null);
      const settings = await userService.getSettings();
      setUserSettings(settings);
      
      // Ensure numeric values are converted to numbers
      setDrawdown(Number(settings.drawdown));
      setBeta(Number(settings.beta));
      setHurdleRate(Number(settings.hurdle_rate));
      setSectorLimits(settings.sector_exposure_limits);
      setWhitelist(settings.whitelist);
      setBlacklist(settings.blacklist);
    } catch (error: any) {
      console.error('Failed to load settings:', error);
      setSettingsError(error?.response?.data?.message || 'Failed to load settings');
    } finally {
      setIsLoadingSettings(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setIsSavingSettings(true);
      setSettingsError(null);
      setSettingsSuccess(null);

      await userService.partialUpdateSettings({
        drawdown,
        beta,
        hurdle_rate: hurdleRate,
        sector_exposure_limits: sectorLimits,
        whitelist,
        blacklist,
      });

      setSettingsSuccess('Settings saved successfully!');
      setTimeout(() => setSettingsSuccess(null), 3000);
      await loadSettings();
    } catch (error: any) {
      console.error('Failed to save settings:', error);
      setSettingsError(
        error?.response?.data?.message || error?.message || 'Failed to save settings'
      );
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleResetToDefaults = () => {
    setDrawdown(20.0);
    setBeta(1.0);
    setHurdleRate(8.0);
    setSectorLimits({
      technology: 30.0, healthcare: 20.0, financial: 20.0, consumer: 15.0,
      industrial: 15.0, energy: 10.0, utilities: 10.0, real_estate: 10.0,
      materials: 10.0, communication: 15.0, consumer_staples: 15.0
    });
    setWhitelist([
      "sec.gov", "irs.gov", "yahoo.com", "bloomberg.com", "reuters.com",
      "cnbc.com", "marketwatch.com", "investopedia.com", "ft.com",
      "morningstar.com", "nasdaq.com", "nyse.com", "stlouisfed.org",
      "bea.gov", "home.treasury.gov", "spglobal.com", "moodys.com",
      "koyfin.com", "tickertape.in"
    ]);
    setBlacklist([]);
  };

  const handleAddSector = () => {
    if (newSectorName.trim() && !sectorLimits[newSectorName.trim()]) {
      setSectorLimits({ ...sectorLimits, [newSectorName.trim()]: newSectorLimit });
      setNewSectorName('');
      setNewSectorLimit(10.0);
    }
  };

  const handleRemoveSector = (sector: string) => {
    const newLimits = { ...sectorLimits };
    delete newLimits[sector];
    setSectorLimits(newLimits);
  };

  const handleUpdateSectorLimit = (sector: string, value: number) => {
    setSectorLimits({ ...sectorLimits, [sector]: value });
  };

  const handleAddWhitelistDomain = () => {
    if (newWhitelistDomain.trim() && !whitelist.includes(newWhitelistDomain.trim())) {
      setWhitelist([...whitelist, newWhitelistDomain.trim()]);
      setNewWhitelistDomain('');
    }
  };

  const handleRemoveWhitelistDomain = (domain: string) => {
    setWhitelist(whitelist.filter(d => d !== domain));
  };

  const handleAddBlacklistDomain = () => {
    if (newBlacklistDomain.trim() && !blacklist.includes(newBlacklistDomain.trim())) {
      setBlacklist([...blacklist, newBlacklistDomain.trim()]);
      setNewBlacklistDomain('');
    }
  };

  const handleRemoveBlacklistDomain = (domain: string) => {
    setBlacklist(blacklist.filter(d => d !== domain));
  };

  const themeOptions: Array<{
    key: ThemeName;
    name: string;
    description: string;
    emoji: string;
    primaryColor: string;
  }> = [
    { key: 'sky-blue', name: 'Sky Blue', description: 'Professional and trustworthy', emoji: '✨', primaryColor: '#0EA5E9' },
    { key: 'emerald-pro', name: 'Emerald', description: 'Growth and prosperity', emoji: '💚', primaryColor: '#10B981' },
    { key: 'violet-luxury', name: 'Violet', description: 'Luxury and sophistication', emoji: '💜', primaryColor: '#8B5CF6' },
    { key: 'orange-energy', name: 'Orange', description: 'Energetic and bold', emoji: '🧡', primaryColor: '#F97316' },
    { key: 'rose-elegant', name: 'Rose', description: 'Elegant and refined', emoji: '🌹', primaryColor: '#F43F5E' },
    { key: 'slate-minimal', name: 'Slate', description: 'Minimal and neutral', emoji: '⚫', primaryColor: '#475569' },
    { key: 'indigo-deep', name: 'Indigo', description: 'Corporate and stable', emoji: '🔵', primaryColor: '#6366F1' },
    { key: 'teal-modern', name: 'Teal', description: 'Fresh and innovative', emoji: '🌊', primaryColor: '#14B8A6' },
    { key: 'amber-warm', name: 'Amber', description: 'Warm and inviting', emoji: '🟡', primaryColor: '#F59E0B' },
    { key: 'red-bold', name: 'Red', description: 'Bold and powerful', emoji: '🔴', primaryColor: '#DC2626' },
  ];

  return (
    <MainLayout>
      <div className="h-full overflow-y-auto bg-[var(--color-background)] p-6 pb-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[var(--color-foreground)] mb-2">Settings</h1>
            <p className="text-[var(--color-muted)]">Customize your risk management parameters and application appearance</p>
          </div>

          <div className={cn('bg-[var(--color-surface)] rounded-lg elevation-2 p-6 mb-6')}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-1">Risk Management Settings</h2>
                <p className="text-sm text-[var(--color-muted)]">Configure your portfolio risk parameters and data source preferences</p>
              </div>
              <Button onClick={handleResetToDefaults} variant="ghost" size="sm" disabled={isLoadingSettings || isSavingSettings}>
                <Icon name="refresh" size={16} />
                <span className="ml-2">Reset to Defaults</span>
              </Button>
            </div>

            {settingsError && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <p className="text-sm text-red-500">{settingsError}</p>
              </div>
            )}
            {settingsSuccess && (
              <div className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                <p className="text-sm text-green-500">{settingsSuccess}</p>
              </div>
            )}

            {isLoadingSettings ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
              </div>
            ) : (
              <div className="space-y-8">
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-[var(--color-foreground)]">Risk Parameters</h3>
                  
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-[var(--color-foreground)]">Max Drawdown</label>
                      <span className="text-lg font-bold text-[var(--color-foreground)]">{drawdown.toFixed(1)}%</span>
                    </div>
                    <input type="range" min="0" max="100" step="0.5" value={drawdown}
                      onChange={(e) => setDrawdown(parseFloat(e.target.value))}
                      className="w-full h-2 bg-[var(--color-surface-elevated)] rounded-lg appearance-none cursor-pointer accent-[var(--color-foreground)]"
                    />
                    <p className="mt-1 text-xs text-[var(--color-muted)]">Maximum acceptable portfolio drawdown (0-100%)</p>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-[var(--color-foreground)]">Portfolio Beta</label>
                      <span className="text-lg font-bold text-[var(--color-foreground)]">{beta.toFixed(2)}</span>
                    </div>
                    <input type="range" min="-5" max="5" step="0.05" value={beta}
                      onChange={(e) => setBeta(parseFloat(e.target.value))}
                      className="w-full h-2 bg-[var(--color-surface-elevated)] rounded-lg appearance-none cursor-pointer accent-[var(--color-foreground)]"
                    />
                    <p className="mt-1 text-xs text-[var(--color-muted)]">Portfolio beta relative to market (-5 to 5)</p>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-[var(--color-foreground)]">Hurdle Rate</label>
                      <span className="text-lg font-bold text-[var(--color-foreground)]">{hurdleRate.toFixed(1)}%</span>
                    </div>
                    <input type="range" min="0" max="50" step="0.5" value={hurdleRate}
                      onChange={(e) => setHurdleRate(parseFloat(e.target.value))}
                      className="w-full h-2 bg-[var(--color-surface-elevated)] rounded-lg appearance-none cursor-pointer accent-[var(--color-foreground)]"
                    />
                    <p className="mt-1 text-xs text-[var(--color-muted)]">Minimum acceptable return rate (0-50%)</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-[var(--color-foreground)] mb-4">Sector Exposure Limits</h3>
                  
                  <div className="flex gap-2 mb-4">
                    <input type="text" placeholder="Sector name (e.g., technology)" value={newSectorName}
                      onChange={(e) => setNewSectorName(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSector()}
                      className="flex-1 px-3 py-2 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                    />
                    <input type="number" min="0" max="100" step="0.5" value={newSectorLimit}
                      onChange={(e) => setNewSectorLimit(parseFloat(e.target.value) || 0)}
                      className="w-24 px-3 py-2 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                    />
                    <Button onClick={handleAddSector} variant="primary" size="sm">
                      <Icon name="plus" size={16} />
                      <span className="ml-1">Add</span>
                    </Button>
                  </div>

                  <div className="space-y-3">
                    {Object.entries(sectorLimits).map(([sector, limit]) => (
                      <div key={sector} className="p-3 rounded-lg bg-[var(--color-surface-elevated)]">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-[var(--color-foreground)] capitalize">{sector.replace(/_/g, ' ')}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-[var(--color-foreground)] w-12 text-right">{limit.toFixed(1)}%</span>
                            <button onClick={() => handleRemoveSector(sector)} className="text-red-500 hover:text-red-600">
                              <Icon name="close" size={16} />
                            </button>
                          </div>
                        </div>
                        <input type="range" min="0" max="100" step="0.5" value={limit}
                          onChange={(e) => handleUpdateSectorLimit(sector, parseFloat(e.target.value))}
                          className="w-full h-1.5 bg-[var(--color-primary)] rounded-lg appearance-none cursor-pointer accent-[var(--color-foreground)]"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--color-foreground)] mb-4">Whitelist Domains</h3>
                    
                    <div className="flex gap-2 mb-3">
                      <input type="text" placeholder="domain.com" value={newWhitelistDomain}
                        onChange={(e) => setNewWhitelistDomain(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddWhitelistDomain()}
                        className="flex-1 px-3 py-2 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-foreground)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                      />
                      <Button onClick={handleAddWhitelistDomain} variant="primary" size="sm">
                        <Icon name="plus" size={16} />
                      </Button>
                    </div>

                    <div className="max-h-60 overflow-y-auto space-y-2">
                      {whitelist.map((domain) => (
                        <div key={domain} className="flex items-center justify-between p-2 rounded bg-[var(--color-surface-elevated)] group">
                          <span className="text-sm text-[var(--color-foreground)]">{domain}</span>
                          <button onClick={() => handleRemoveWhitelistDomain(domain)}
                            className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-600 transition-opacity">
                            <Icon name="close" size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-[var(--color-muted)]">{whitelist.length} allowed domain{whitelist.length !== 1 ? 's' : ''}</p>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-[var(--color-foreground)] mb-4">Blacklist Domains</h3>
                    
                    <div className="flex gap-2 mb-3">
                      <input type="text" placeholder="domain.com" value={newBlacklistDomain}
                        onChange={(e) => setNewBlacklistDomain(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddBlacklistDomain()}
                        className="flex-1 px-3 py-2 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-foreground)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                      />
                      <Button onClick={handleAddBlacklistDomain} variant="primary" size="sm">
                        <Icon name="plus" size={16} />
                      </Button>
                    </div>

                    <div className="max-h-60 overflow-y-auto space-y-2">
                      {blacklist.length === 0 ? (
                        <div className="text-center py-8 text-[var(--color-muted)] text-sm">No blocked domains</div>
                      ) : (
                        blacklist.map((domain) => (
                          <div key={domain} className="flex items-center justify-between p-2 rounded bg-[var(--color-surface-elevated)] group">
                            <span className="text-sm text-[var(--color-foreground)]">{domain}</span>
                            <button onClick={() => handleRemoveBlacklistDomain(domain)}
                              className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-600 transition-opacity">
                              <Icon name="close" size={14} />
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                    <p className="mt-2 text-xs text-[var(--color-muted)]">{blacklist.length} blocked domain{blacklist.length !== 1 ? 's' : ''}</p>
                  </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-[var(--color-border)]">
                  <Button onClick={handleSaveSettings} variant="primary" size="lg" disabled={isSavingSettings}>
                    {isSavingSettings ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span className="ml-2">Saving...</span>
                      </>
                    ) : (
                      <>
                        <Icon name="check" size={20} />
                        <span className="ml-2">Save Settings</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div className={cn('bg-[var(--color-surface)] rounded-lg elevation-2 p-6 mb-6')}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-1">Dark Mode</h2>
                <p className="text-sm text-[var(--color-muted)]">Toggle between light and dark appearance</p>
              </div>
              <Button onClick={toggleTheme} variant="ghost" size="lg" className="ml-4">
                <Icon name={isDark ? 'sun' : 'moon'} size={24} />
                <span className="ml-2">{isDark ? 'Light Mode' : 'Dark Mode'}</span>
              </Button>
            </div>
          </div>

          <div className={cn('bg-[var(--color-surface)] rounded-lg elevation-2 p-6')}>
            <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-1">Color Theme</h2>
            <p className="text-sm text-[var(--color-muted)] mb-6">Choose your preferred color scheme</p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {themeOptions.map((option) => {
                const isActive = colorTheme === option.key;
                return (
                  <button key={option.key} onClick={() => setColorTheme(option.key)}
                    className={cn('relative p-4 rounded-lg transition-all duration-200 hover:elevation-2 cursor-pointer border-2 text-left',
                      isActive ? 'border-[var(--color-primary)] elevation-2' : 'border-transparent bg-[var(--color-surface-elevated)]'
                    )}>
                    {isActive && (
                      <div className="absolute top-2 right-2">
                        <div className="bg-[var(--color-primary)] text-white rounded-full p-1">
                          <Icon name="check" size={14} />
                        </div>
                      </div>
                    )}
                    <div className="w-full h-16 rounded-lg mb-3 elevation-1"
                      style={{ background: `linear-gradient(135deg, ${option.primaryColor}, ${option.primaryColor}dd)` }}
                    />
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">{option.emoji}</span>
                      <h3 className="font-semibold text-[var(--color-foreground)]">{option.name}</h3>
                    </div>
                    <p className="text-xs text-[var(--color-muted)]">{option.description}</p>
                  </button>
                );
              })}
            </div>

            <div className="mt-8 p-6 bg-[var(--color-surface-elevated)] rounded-lg">
              <h3 className="text-lg font-semibold text-[var(--color-foreground)] mb-4">Preview</h3>
              <div className="flex flex-wrap gap-3">
                <Button variant="primary">Primary Button</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="danger">Danger</Button>
              </div>
              <div className="mt-4 flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Icon name="trending-up" className="text-[var(--color-success)]" />
                  <span className="text-[var(--color-success)] font-semibold">+$1,234.56</span>
                </div>
                <div className="flex items-center gap-2">
                  <Icon name="trending-down" className="text-[var(--color-danger)]" />
                  <span className="text-[var(--color-danger)] font-semibold">-$987.65</span>
                </div>
              </div>
            </div>

            <div className={cn('mt-6 p-4 rounded-lg bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/20')}>
              <div className="flex items-start gap-3">
                <Icon name="info" className="text-[var(--color-primary)] mt-0.5" />
                <div>
                  <p className="text-sm text-[var(--color-foreground)] font-medium mb-1">Theme applied instantly</p>
                  <p className="text-xs text-[var(--color-muted)]">
                    Your theme preference is saved automatically and will be applied across all pages.
                    P&L colors (green/red) remain consistent for clarity.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
