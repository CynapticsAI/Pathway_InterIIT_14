/**
 * Icon Component - Using Lucide React (Material Design Icons)
 * 
 * Modern icon component replacing emoji-based system
 * Supports all Lucide icons with consistent sizing and styling
 */

import { LucideIcon } from 'lucide-react';
import {
  Send,
  Paperclip,
  Mic,
  Settings,
  X,
  Minimize2,
  Maximize2,
  Menu,
  Moon,
  Sun,
  Trash2,
  Edit,
  Copy,
  Home,
  MessageSquare,
  TrendingUp,
  Briefcase,
  Star,
  Bell,
  HelpCircle,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
  Download,
  Upload,
  Plus,
  Minus,
  Check,
  AlertCircle,
  Info,
  BarChart3,
  PieChart,
  Activity,
  DollarSign,
  TrendingDown,
  RefreshCw,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  User,
  Users,
  Calendar,
  Clock,
  MapPin,
  Mail,
  Phone,
  Globe,
  Link,
  ExternalLink,
  FileText,
  Image,
  Video,
  Music,
  File,
  Folder,
  Archive,
  Share2,
  Heart,
  Bookmark,
  ThumbsUp,
  ThumbsDown,
  MessageCircle,
  MoreVertical,
  MoreHorizontal,
  LogOut,
  LogIn,
  Zap,
  Target,
  Award,
  TrendingUpDown,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export type IconName =
  | 'send'
  | 'attachment'
  | 'mic'
  | 'settings'
  | 'close'
  | 'minimize'
  | 'maximize'
  | 'menu'
  | 'moon'
  | 'sun'
  | 'trash'
  | 'edit'
  | 'copy'
  | 'home'
  | 'message'
  | 'trending-up'
  | 'briefcase'
  | 'star'
  | 'bell'
  | 'help'
  | 'chevron-right'
  | 'chevron-left'
  | 'chevron-down'
  | 'chevron-up'
  | 'search'
  | 'filter'
  | 'download'
  | 'upload'
  | 'plus'
  | 'minus'
  | 'check'
  | 'alert'
  | 'info'
  | 'bar-chart'
  | 'pie-chart'
  | 'activity'
  | 'dollar'
  | 'trending-down'
  | 'refresh'
  | 'eye'
  | 'eye-off'
  | 'lock'
  | 'unlock'
  | 'user'
  | 'users'
  | 'calendar'
  | 'clock'
  | 'map-pin'
  | 'mail'
  | 'phone'
  | 'globe'
  | 'link'
  | 'external-link'
  | 'file-text'
  | 'image'
  | 'video'
  | 'music'
  | 'file'
  | 'folder'
  | 'archive'
  | 'share'
  | 'heart'
  | 'bookmark'
  | 'thumbs-up'
  | 'thumbs-down'
  | 'message-circle'
  | 'more-vertical'
  | 'more-horizontal'
  | 'logout'
  | 'login'
  | 'zap'
  | 'target'
  | 'award'
  | 'trending'
  | 'arrow-up'
  | 'arrow-down'
  | 'arrow-left'
  | 'arrow-right';

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface IconProps {
  name: IconName;
  size?: IconSize | number;
  className?: string;
  strokeWidth?: number;
}

// Icon mapping
const iconMap: Record<IconName, LucideIcon> = {
  send: Send,
  attachment: Paperclip,
  mic: Mic,
  settings: Settings,
  close: X,
  minimize: Minimize2,
  maximize: Maximize2,
  menu: Menu,
  moon: Moon,
  sun: Sun,
  trash: Trash2,
  edit: Edit,
  copy: Copy,
  home: Home,
  message: MessageSquare,
  'trending-up': TrendingUp,
  briefcase: Briefcase,
  star: Star,
  bell: Bell,
  help: HelpCircle,
  'chevron-right': ChevronRight,
  'chevron-left': ChevronLeft,
  'chevron-down': ChevronDown,
  'chevron-up': ChevronUp,
  search: Search,
  filter: Filter,
  download: Download,
  upload: Upload,
  plus: Plus,
  minus: Minus,
  check: Check,
  alert: AlertCircle,
  info: Info,
  'bar-chart': BarChart3,
  'pie-chart': PieChart,
  activity: Activity,
  dollar: DollarSign,
  'trending-down': TrendingDown,
  refresh: RefreshCw,
  eye: Eye,
  'eye-off': EyeOff,
  lock: Lock,
  unlock: Unlock,
  user: User,
  users: Users,
  calendar: Calendar,
  clock: Clock,
  'map-pin': MapPin,
  mail: Mail,
  phone: Phone,
  globe: Globe,
  link: Link,
  'external-link': ExternalLink,
  'file-text': FileText,
  image: Image,
  video: Video,
  music: Music,
  file: File,
  folder: Folder,
  archive: Archive,
  share: Share2,
  heart: Heart,
  bookmark: Bookmark,
  'thumbs-up': ThumbsUp,
  'thumbs-down': ThumbsDown,
  'message-circle': MessageCircle,
  'more-vertical': MoreVertical,
  'more-horizontal': MoreHorizontal,
  logout: LogOut,
  login: LogIn,
  zap: Zap,
  target: Target,
  award: Award,
  trending: TrendingUpDown,
  'arrow-up': ArrowUp,
  'arrow-down': ArrowDown,
  'arrow-left': ArrowLeft,
  'arrow-right': ArrowRight,
};

// Size mapping
const sizeMap: Record<IconSize, number> = {
  xs: 16,
  sm: 20,
  md: 24,
  lg: 32,
  xl: 40,
};

export function Icon({ 
  name, 
  size = 'md', 
  className = '',
  strokeWidth = 2 
}: IconProps) {
  const IconComponent = iconMap[name];
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in icon map`);
    return null;
  }

  const iconSize = typeof size === 'number' ? size : sizeMap[size];

  return (
    <IconComponent
      size={iconSize}
      strokeWidth={strokeWidth}
      className={cn('flex-shrink-0', className)}
    />
  );
}

