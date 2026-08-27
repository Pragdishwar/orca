import React from 'react';
import ConversationPane from '../components/platform/ConversationPane';
import MapPane from '../components/platform/MapPane';
import EvidencePane from '../components/platform/EvidencePane';

export default function PlatformTab() {
  return (
    <div className="flex h-[calc(100vh-140px)] gap-4 overflow-hidden">
      {/* Left Pane - Conversation */}
      <div className="w-1/3 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <ConversationPane />
      </div>

      {/* Centre Pane - MapLibre */}
      <div className="w-1/3 flex flex-col rounded-xl overflow-hidden shadow-sm border border-gray-200 bg-gray-100">
        <MapPane />
      </div>

      {/* Right Pane - Evidence & Reasoning */}
      <div className="w-1/3 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <EvidencePane />
      </div>
    </div>
  );
}
