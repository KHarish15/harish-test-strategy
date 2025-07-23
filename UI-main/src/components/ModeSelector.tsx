import React, { useState } from 'react';
import { Zap, Wrench, X } from 'lucide-react';
import type { AppMode } from '../App';

interface ModeSelectorProps {
  onModeSelect: (mode: AppMode) => void;
  onClose: () => void;
}

const ModeSelector: React.FC<ModeSelectorProps> = ({ onModeSelect, onClose }) => {
  const [selectedMode, setSelectedMode] = useState<'agent' | 'tool'>('agent');

  const handleModeChange = (mode: 'agent' | 'tool') => {
    setSelectedMode(mode);
  };

  const handleConfirm = () => {
    onModeSelect(selectedMode);
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-40 p-4 animate-fadeIn">
      <div className="bg-white/80 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-slideInUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-confluence-blue/90 to-confluence-light-blue/90 backdrop-blur-xl p-6 text-white border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="text-center flex-1">
              <h2 className="text-2xl font-bold">Choose Your Mode</h2>
              <p className="text-blue-100/90 mt-1">How would you like to interact with the AI?</p>
            </div>
            <button onClick={onClose} className="text-white hover:bg-white/10 rounded-full p-2 backdrop-blur-sm transition-colors">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Mode Selection */}
        <div className="p-8">
          {/* Segmented Toggle */}
          <div className="relative bg-gray-100/80 backdrop-blur-sm rounded-xl p-1 mb-6 border border-white/20">
            <div 
              className={`absolute top-1 bottom-1 w-1/2 bg-white rounded-lg shadow-md transition-all duration-300 ease-out ${
                selectedMode === 'agent' ? 'left-1' : 'left-1/2'
              }`}
              style={{
                background: selectedMode === 'agent' 
                  ? 'linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(234, 88, 12, 0.1) 100%)'
                  : 'linear-gradient(135deg, rgba(38, 132, 255, 0.1) 0%, rgba(0, 82, 204, 0.1) 100%)',
                borderColor: selectedMode === 'agent' ? 'rgba(249, 115, 22, 0.2)' : 'rgba(38, 132, 255, 0.2)',
                borderWidth: '1px'
              }}
            />
            
            <div className="relative flex">
              <button
                onClick={() => handleModeChange('agent')}
                className={`flex-1 py-3 px-4 text-center font-medium transition-all duration-300 rounded-lg ${
                  selectedMode === 'agent'
                    ? 'text-orange-600 z-10'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Agent Mode
              </button>
              <button
                onClick={() => handleModeChange('tool')}
                className={`flex-1 py-3 px-4 text-center font-medium transition-all duration-300 rounded-lg ${
                  selectedMode === 'tool'
                    ? 'text-confluence-blue z-10'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                Tool Mode
              </button>
            </div>
          </div>

          {/* Mode Description */}
          <div className="mb-6">
            {selectedMode === 'agent' ? (
              <div className="bg-gradient-to-br from-orange-50/80 to-orange-100/80 backdrop-blur-sm rounded-xl p-6 border border-orange-200/50">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-orange-500/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                    <Zap className="w-5 h-5 text-orange-600" />
                  </div>
                  <h3 className="text-lg font-bold text-orange-800">Agent Mode</h3>
                </div>
                <p className="text-orange-700 text-sm leading-relaxed">
                  Goal-based assistance with AI planning and execution. Describe what you want to achieve, 
                  and the AI will create a plan, execute it step by step, and provide comprehensive results 
                  with reasoning and follow-up options.
                </p>
              </div>
            ) : (
              <div className="bg-gradient-to-br from-blue-50/80 to-blue-100/80 backdrop-blur-sm rounded-xl p-6 border border-blue-200/50">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-confluence-blue/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                    <Wrench className="w-5 h-5 text-confluence-blue" />
                  </div>
                  <h3 className="text-lg font-bold text-confluence-blue">Tool Mode</h3>
                </div>
                <p className="text-blue-700 text-sm leading-relaxed">
                  Access individual tools like AI Powered Search, Code Assistant, Video Summarizer, 
                  Impact Analyzer, Test Support Tool, and Image Insights. Choose specific tools 
                  for targeted tasks and workflows.
                </p>
              </div>
            )}
          </div>

          {/* Confirm Button */}
          <button
            onClick={handleConfirm}
            className={`w-full py-3 px-6 rounded-xl font-semibold text-white transition-all duration-300 hover:scale-105 shadow-lg ${
              selectedMode === 'agent'
                ? 'bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 hover:shadow-orange-500/30'
                : 'bg-gradient-to-r from-confluence-blue to-confluence-light-blue hover:from-confluence-blue hover:to-blue-600 hover:shadow-blue-500/30'
            }`}
          >
            Continue with {selectedMode === 'agent' ? 'Agent' : 'Tool'} Mode
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModeSelector; 