// News data types for real-time WebSocket data

export interface NewsItemData {
  dt_utc: string;
  ticker: string;
  source: string;
  title: string;
  url: string;
  diff: number;
  time: number;
}

export interface NewsMessage {
  type: 'news';
  data: NewsItemData;
}

export interface NewsItem {
  timestamp: string;
  ticker: string;
  source: string;
  title: string;
  url: string;
  time: number;
}
