import React, { useState } from "react";
import ImageInsights from "./ImageInsights";
import FlowchartGenerator from "./FlowchartGenerator";

const DiagramTools: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chart' | 'flowchart'>('chart');

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex gap-4 mb-6">
        <button
          className={`px-4 py-2 rounded font-semibold ${activeTab === 'chart' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}
          onClick={() => setActiveTab('chart')}
        >
          Chart Builder
        </button>
        <button
          className={`px-4 py-2 rounded font-semibold ${activeTab === 'flowchart' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}
          onClick={() => setActiveTab('flowchart')}
        >
          Flowchart Generator
        </button>
      </div>
      {activeTab === 'chart' ? <ImageInsights /> : <FlowchartGenerator />}
    </div>
  );
};

export default DiagramTools; 