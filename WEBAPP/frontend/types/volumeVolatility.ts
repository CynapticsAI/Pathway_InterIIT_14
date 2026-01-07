// Volume volatility data types for real-time WebSocket data

export interface VolumeSpikeData {
  timestamp: string;
  symbol: string;
  current_close: number;
  current_volume: number;
  current_range: number;
  volume_stats: [number, number]; // [avg, std]
  range_stats: [number, number]; // [avg, std]
  bar_count: number;
  avg_volume: number;
  std_volume: number;
  avg_range: number;
  std_range: number;
  volume_zscore: number;
  volatility_zscore: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  diff: number;
  time: number;
}

export interface VolumeSpikeMessage {
  type: 'volume_spike';
  data: VolumeSpikeData;
}

export interface VolumeVolatilityItem {
  timestamp: string;
  symbol: string;
  currentClose: number;
  currentVolume: number;
  volumeZScore: number;
  volatilityZScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  time: number;
}
