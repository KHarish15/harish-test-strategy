import React, { useState, useEffect } from 'react';
import ModeSelector from './components/ModeSelector';
import AgentMode from './components/AgentMode';
import AIPoweredSearch from './components/AIPoweredSearch';
import VideoSummarizer from './components/VideoSummarizer';
import CodeAssistant from './components/CodeAssistant';
import ImpactAnalyzer from './components/ImpactAnalyzer';
import TestSupportTool from './components/TestSupportTool';
import DiagramTools from './components/DiagramTools';
import CircularLauncher from './components/CircularLauncher';
import FlowchartGenerator from './components/FlowchartGenerator';
import axios from "axios";

export type FeatureType = 'search' | 'video' | 'code' | 'impact' | 'test' | 'diagram' | null;
export type AppMode = 'agent' | 'tool' | null;

export async function generateFlowchart(spaceKey: string, pageTitle: string, apiKey?: string) {
  const response = await axios.post(
    `${process.env.REACT_APP_API_URL || "https://backend-az2r.onrender.com"}/flowchart-generator`,
    {
      space_key: spaceKey,
      page_title: pageTitle,
    },
    {
      headers: apiKey ? { "x-api-key": apiKey } : {},
    }
  );
  return response.data;
}

function App() {
  const [activeFeature, setActiveFeature] = useState<FeatureType>(null);
  const [isAppOpen, setIsAppOpen] = useState(false);
  const [autoSpaceKey, setAutoSpaceKey] = useState<string | null>(null);
  const [appMode, setAppMode] = useState<AppMode>(null);

  // Extract space key from URL parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const spaceKey = urlParams.get('space');
    if (spaceKey) {
      setAutoSpaceKey(spaceKey);
    }
  }, []);

  const renderActiveFeature = () => {
    switch (activeFeature) {
      case 'search':
        return <AIPoweredSearch onClose={() => setActiveFeature(null)} onFeatureSelect={setActiveFeature} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />;
      case 'video':
        return <VideoSummarizer onClose={() => setActiveFeature(null)} onFeatureSelect={setActiveFeature} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />;
      case 'code':
        return <CodeAssistant onClose={() => setActiveFeature(null)} onFeatureSelect={setActiveFeature} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />;
      case 'impact':
        return <ImpactAnalyzer onClose={() => setActiveFeature(null)} onFeatureSelect={setActiveFeature} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />;
      case 'test':
        return <TestSupportTool onClose={() => setActiveFeature(null)} onFeatureSelect={setActiveFeature} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />;
      case 'diagram':
        return <DiagramTools />;
      default:
        return <AIPoweredSearch onClose={() => setActiveFeature(null)} onFeatureSelect={setActiveFeature} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />;
    }
  };

  const handleLauncherClick = () => {
    setIsAppOpen(true);
    // Don't set a default feature, let user choose mode first
  };

  const handleAppClose = () => {
    setIsAppOpen(false);
    setActiveFeature(null);
    setAppMode(null);
  };

  const handleModeSelect = (mode: AppMode) => {
    setAppMode(mode);
    if (mode === 'tool' && !activeFeature) {
      setActiveFeature('search');
    }
  };

  return (
    <div className="min-h-screen bg-white p-4">
      {!isAppOpen && (
        <CircularLauncher onClick={handleLauncherClick} />
      )}
      {isAppOpen && (
        <div>
          {/* Add a simple navigation bar for feature selection */}
          <div className="flex overflow-x-auto gap-2 mb-4 whitespace-nowrap w-full">
            <button className="min-w-max bg-gray-200 px-3 py-1 rounded" onClick={() => setActiveFeature('search')}>AI Powered Search</button>
            <button className="min-w-max bg-gray-200 px-3 py-1 rounded" onClick={() => setActiveFeature('video')}>Video Summarizer</button>
            <button className="min-w-max bg-gray-200 px-3 py-1 rounded" onClick={() => setActiveFeature('code')}>Code Assistant</button>
            <button className="min-w-max bg-gray-200 px-3 py-1 rounded" onClick={() => setActiveFeature('impact')}>Impact Analyzer</button>
            <button className="min-w-max bg-gray-200 px-3 py-1 rounded" onClick={() => setActiveFeature('test')}>Test Support Tool</button>
            <button className="min-w-max bg-blue-500 text-white px-3 py-1 rounded" onClick={() => setActiveFeature('diagram')}>Diagram Tools</button>
          </div>
          {!appMode ? (
            <ModeSelector onModeSelect={handleModeSelect} onClose={handleAppClose} />
          ) : appMode === 'agent' ? (
            <AgentMode onClose={handleAppClose} onModeSelect={setAppMode} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />
          ) : appMode === 'tool' && activeFeature ? (
            renderActiveFeature()
          ) : appMode === 'tool' ? (
            <AIPoweredSearch onClose={handleAppClose} onFeatureSelect={setActiveFeature} autoSpaceKey={autoSpaceKey} isSpaceAutoConnected={!!autoSpaceKey} />
          ) : null}
        </div>
      )}
    </div>
  );
}

export default App;