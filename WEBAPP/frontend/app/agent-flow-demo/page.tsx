'use client';

import { AgentFlowchart } from '@/components/charts/AgentFlowchart';

export default function AgentFlowDemoPage() {
  return (
    <div className="h-screen w-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto h-full flex flex-col">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            🤖 Agent Workflow Demonstration
          </h1>
          <p className="text-gray-400">
            Visualize how the AI orchestrator coordinates between Research and RAG agents
          </p>
        </div>
        
        <div className="flex-1 bg-gray-800/50 rounded-xl shadow-2xl overflow-hidden">
          <AgentFlowchart />
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <h3 className="text-white font-semibold mb-2">🎯 Orchestrator</h3>
            <p className="text-gray-400 text-sm">
              Routes queries to the appropriate agent based on the type of information needed
            </p>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <h3 className="text-white font-semibold mb-2">🔍 Research Agent</h3>
            <p className="text-gray-400 text-sm">
              Fetches real-time market data, news, and external information from APIs
            </p>
          </div>
          
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <h3 className="text-white font-semibold mb-2">🧠 RAG Agent</h3>
            <p className="text-gray-400 text-sm">
              Queries the knowledge base for historical analysis and contextual information
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
