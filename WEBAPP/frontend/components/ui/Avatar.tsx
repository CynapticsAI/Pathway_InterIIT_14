interface AvatarProps {
  type: 'user' | 'ai';
  size?: 'sm' | 'md' | 'lg';
}

export function Avatar({ type, size = 'md' }: AvatarProps) {
  const sizes = {
    sm: 'w-6 h-6 text-sm',
    md: 'w-8 h-8 text-base',
    lg: 'w-10 h-10 text-lg',
  };

  const emoji = type === 'user' ? '👤' : '🤖';
  const bgColor = type === 'user' 
    ? 'bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)]' 
    : 'bg-[var(--color-ai-message)]';

  return (
    <div 
      className={`
        ${sizes[size]} 
        ${bgColor}
        rounded-full 
        flex items-center justify-center 
        shadow-md
        flex-shrink-0
      `}
    >
      <span className="select-none">{emoji}</span>
    </div>
  );
}
