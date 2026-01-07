import { useChatContext } from '@/contexts/ChatContext';

export const useChat = () => {
  return useChatContext();
};

export default useChat;