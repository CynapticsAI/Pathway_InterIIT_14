import { SplitChatView } from "@/components/chat/SplitChatView";
import { MainLayout } from "@/components/layout/MainLayout";

export default function Home() {
  return (
    <MainLayout>
      <SplitChatView />
    </MainLayout>
  );
}
