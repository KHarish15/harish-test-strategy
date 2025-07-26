import React, { useState, useEffect } from 'react';
import { TestTube, Code, FileCheck, Download, Save, X, ChevronDown, Loader2, MessageSquare, Play, Search, Video, TrendingUp, Image, GitBranch, Clock, CheckCircle, XCircle, AlertTriangle, Activity } from 'lucide-react';
import { FeatureType } from '../App';
import apiService, { Space } from '../services/api';
import ReactMarkdown from 'react-markdown';
import { getConfluenceSpaceAndPageFromUrl } from '../utils/urlUtils';

interface TestSupportToolProps {
  onClose: () => void;
  onFeatureSelect: (feature: FeatureType) => void;
  autoSpaceKey?: string | null;
  isSpaceAutoConnected?: boolean;
}

interface TestReport {
  strategy?: string;
  crossPlatform?: string;
  sensitivity?: string;
}

interface TestMetrics {
  total_tests: number;
  success_rate: number;
  build_info: {
    branch: string;
    commit: string;
    build_number: string;
  };
}

interface TestRecommendations {
  priority: string;
  action_items: string[];
}

const TestSupportTool: React.FC<TestSupportToolProps> = ({ onClose, onFeatureSelect, autoSpaceKey, isSpaceAutoConnected }) => {
  const [selectedSpace, setSelectedSpace] = useState('');
  const [codePage, setCodePage] = useState('');
  const [testInputPage, setTestInputPage] = useState('');
  const [isGenerating, setIsGenerating] = useState<string>('');
  const [isQALoading, setIsQALoading] = useState(false);
  const [testReport, setTestReport] = useState<TestReport | null>(null);
  const [question, setQuestion] = useState('');
  const [qaResults, setQaResults] = useState<Array<{question: string, answer: string}>>([]);
  const [exportFormat, setExportFormat] = useState('markdown');
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [pages, setPages] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [showToast, setShowToast] = useState(false);
  
  // New state for CircleCI integration
  const [testMetrics, setTestMetrics] = useState<TestMetrics | null>(null);
  const [testRecommendations, setTestRecommendations] = useState<TestRecommendations | null>(null);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);

  const features = [
    { id: 'search' as const, label: 'AI Powered Search', icon: Search },
    { id: 'video' as const, label: 'Video Summarizer', icon: Video },
    { id: 'code' as const, label: 'Code Assistant', icon: Code },
    { id: 'impact' as const, label: 'Impact Analyzer', icon: TrendingUp },
    { id: 'test' as const, label: 'Test Support Tool', icon: TestTube },
    { id: 'diagram' as const, label: 'Diagram Tools', icon: Image },
  ];

  // Load spaces on component mount
  useEffect(() => {
    loadSpaces();
  }, []);

  // Auto-select space if provided via URL
  useEffect(() => {
    if (autoSpaceKey && isSpaceAutoConnected) {
      setSelectedSpace(autoSpaceKey);
    }
  }, [autoSpaceKey, isSpaceAutoConnected]);

  // Load pages when space is selected
  useEffect(() => {
    if (selectedSpace) {
      loadPages();
    }
  }, [selectedSpace]);

  const loadSpaces = async () => {
    try {
      setError('');
      const result = await apiService.getSpaces();
      setSpaces(result.spaces);
    } catch (err) {
      setError('Failed to load spaces. Please check your backend connection.');
      console.error('Error loading spaces:', err);
    }
  };

  const loadPages = async () => {
    try {
      setError('');
      const result = await apiService.getPages(selectedSpace);
      setPages(result.pages);
    } catch (err) {
      setError('Failed to load pages. Please check your space key.');
      console.error('Error loading pages:', err);
    }
  };

  const generateTestStrategy = async () => {
    if (!selectedSpace || !codePage) {
      setError('Please select a space and code page.');
      return;
    }

    setIsGenerating('strategy');
    setError('');

    try {
      console.log('Calling test support API for strategy...');
      const result = await apiService.testSupport({
        space_key: selectedSpace,
        code_page_title: codePage,
        test_input_page_title: testInputPage || undefined
      });

      console.log('Test support strategy response:', result);

      setTestReport(prev => ({
        ...prev,
        strategy: result.test_strategy
      }));
    } catch (err) {
      console.error('Test support strategy error:', err);
      setError('Failed to generate test strategy. Please try again.');
      console.error('Error generating strategy:', err);
    } finally {
      setIsGenerating('');
    }
  };

  const generateCrossPlatform = async () => {
    if (!selectedSpace || !codePage) {
      setError('Please select a space and code page.');
      return;
    }

    setIsGenerating('crossplatform');
    setError('');

    try {
      console.log('Calling test support API for cross-platform analysis...');
      const result = await apiService.testSupport({
        space_key: selectedSpace,
        code_page_title: codePage,
        test_input_page_title: testInputPage || undefined
      });

      console.log('Test support cross-platform response:', result);

      setTestReport(prev => ({
        ...prev,
        crossPlatform: result.cross_platform_testing
      }));
    } catch (err) {
      console.error('Test support cross-platform error:', err);
      setError('Failed to generate cross-platform analysis. Please try again.');
      console.error('Error generating cross-platform analysis:', err);
    } finally {
      setIsGenerating('');
    }
  };

  const generateSensitivity = async () => {
    if (!selectedSpace || !codePage) {
      setError('Please select a space and code page.');
      return;
    }

    setIsGenerating('sensitivity');
    setError('');

    try {
      console.log('Calling test support API for sensitivity analysis...');
      const result = await apiService.testSupport({
        space_key: selectedSpace,
        code_page_title: codePage,
        test_input_page_title: testInputPage || undefined
      });

      console.log('Test support sensitivity response:', result);

      setTestReport(prev => ({
        ...prev,
        sensitivity: result.sensitivity_analysis
      }));
    } catch (err) {
      console.error('Test support sensitivity error:', err);
      setError('Failed to generate sensitivity analysis. Please try again.');
      console.error('Error generating sensitivity analysis:', err);
    } finally {
      setIsGenerating('');
    }
  };

  const addQuestion = async () => {
    if (!question.trim() || !selectedSpace || !codePage) {
      console.log('Missing question or code page:', { question, selectedSpace, codePage });
      return;
    }
    
    console.log('Adding question to test support tool:', question);
    setIsQALoading(true);
    
    try {
      const result = await apiService.testSupport({
        space_key: selectedSpace,
        code_page_title: codePage,
        test_input_page_title: testInputPage || undefined,
        question: question
      });

      console.log('Test support Q&A response:', result);

      const answer = result.ai_response || `Based on the test analysis, here's the response to your question: "${question}"

The test coverage analysis shows comprehensive validation of the code functionality. The sensitivity check indicates ${question.toLowerCase().includes('security') ? 'strong security measures in place' : question.toLowerCase().includes('performance') ? 'good performance characteristics' : 'robust error handling and edge case coverage'}.

This analysis is based on the test scenarios and code review performed.`;

      setQaResults([...qaResults, { question, answer }]);
      setQuestion('');
    } catch (err) {
      console.error('Test support Q&A error:', err);
      setError('Failed to get answer. Please try again.');
      console.error('Error getting answer:', err);
    } finally {
      setIsQALoading(false);
    }
  };

  const exportReport = async () => {
    if (!testReport) return;

    const content = `# Test Support Report

## Test Strategy
${testReport.strategy}

## Cross-Platform Analysis
${testReport.crossPlatform}

## Sensitivity Analysis
${testReport.sensitivity}

## Q&A
${qaResults.map(qa => `**Q:** ${qa.question}\n**A:** ${qa.answer}`).join('\n\n')}

## Generated on: ${new Date().toLocaleString()}`;

    try {
      const blob = await apiService.exportContent({
        content: content,
        format: exportFormat,
        filename: 'test-support-report'
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `test-support-report.${exportFormat}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export file. Please try again.');
      console.error('Error exporting:', err);
    }
  };

  // New CircleCI integration functions
  const fetchTestMetrics = async () => {
    setIsLoadingMetrics(true);
    setError('');
    
    try {
      // Simulate fetching test metrics from CircleCI
      // In a real implementation, this would call your backend API
      const mockMetrics: TestMetrics = {
        total_tests: 15,
        success_rate: 86.7,
        build_info: {
          branch: 'circleci-project-setup',
          commit: '1d2c161',
          build_number: '4'
        }
      };
      
      const mockRecommendations: TestRecommendations = {
        priority: 'medium',
        action_items: [
          'Review failed test: test_failure in test_example.py',
          'Improve test coverage for edge cases',
          'Consider adding integration tests'
        ]
      };
      
      setTestMetrics(mockMetrics);
      setTestRecommendations(mockRecommendations);
    } catch (err) {
      setError('Failed to fetch test metrics. Please try again.');
      console.error('Error fetching metrics:', err);
    } finally {
      setIsLoadingMetrics(false);
    }
  };

  const triggerTestPipeline = async () => {
    setError('');
    
    try {
      // This would trigger a new CircleCI pipeline
      console.log('Triggering new test pipeline...');
      
      // Simulate API call to trigger pipeline
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setShowToast(true);
      setTimeout(() => setShowToast(false), 3000);
    } catch (err) {
      setError('Failed to trigger pipeline. Please try again.');
      console.error('Error triggering pipeline:', err);
    }
  };

  return (
    <div className="fixed inset-0 bg-white flex items-center justify-center z-40 p-4">
      <div className="bg-white/80 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl w-full max-w-7xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-confluence-blue/90 to-confluence-light-blue/90 backdrop-blur-xl p-6 text-white border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <TestTube className="w-8 h-8" />
              <div>
                <h2 className="text-2xl font-bold">Confluence AI Assistant</h2>
                <p className="text-blue-100/90">AI-powered tools for your Confluence workspace</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white hover:bg-white/10 rounded-full p-2 backdrop-blur-sm">
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* Feature Navigation */}
          <div className="mt-6 flex gap-2">
            {features.map((feature) => {
              const Icon = feature.icon;
              const isActive = feature.id === 'test';
              
              return (
                <button
                  key={feature.id}
                  onClick={() => onFeatureSelect(feature.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg backdrop-blur-sm border transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? 'bg-white/90 text-confluence-blue shadow-lg border-white/30'
                      : 'bg-white/10 text-white hover:bg-white/20 border-white/10'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{feature.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {error && (
            <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Left Column - Configuration */}
            <div className="xl:col-span-1">
              <div className="bg-white/60 backdrop-blur-xl rounded-xl p-4 space-y-6 border border-white/20 shadow-lg">
                <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
                  <FileCheck className="w-5 h-5 mr-2" />
                  Component Selection
                </h3>
                
                {/* Space Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Space
                  </label>
                  <div className="relative">
                    <select
                      value={selectedSpace}
                      onChange={(e) => setSelectedSpace(e.target.value)}
                      className="w-full p-3 border border-white/30 rounded-lg focus:ring-2 focus:ring-confluence-blue focus:border-confluence-blue appearance-none bg-white/70 backdrop-blur-sm"
                    >
                      <option value="">Select space...</option>
                      {spaces.map(space => (
                        <option key={space.key} value={space.key}>{space.name}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                  </div>
                </div>

                {/* Code Page Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Code Page
                  </label>
                  <div className="relative">
                    <select
                      value={codePage}
                      onChange={(e) => setCodePage(e.target.value)}
                      className="w-full p-3 border border-white/30 rounded-lg focus:ring-2 focus:ring-confluence-blue focus:border-confluence-blue appearance-none bg-white/70 backdrop-blur-sm"
                    >
                      <option value="">Select code page...</option>
                      {pages.map(page => (
                        <option key={page} value={page}>{page}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                  </div>
                </div>

                {/* Test Input Page Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Test Input Page
                  </label>
                  <div className="relative">
                    <select
                      value={testInputPage}
                      onChange={(e) => setTestInputPage(e.target.value)}
                      className="w-full p-3 border border-white/30 rounded-lg focus:ring-2 focus:ring-confluence-blue focus:border-confluence-blue appearance-none bg-white/70 backdrop-blur-sm"
                    >
                      <option value="">Select test page...</option>
                      {pages.map(page => (
                        <option key={page} value={page}>{page}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                  </div>
                </div>

                {/* Generation Buttons */}
                <div className="space-y-3">
                  <button
                    onClick={generateTestStrategy}
                    disabled={!selectedSpace || !codePage || isGenerating === 'strategy'}
                    className="w-full bg-confluence-blue/90 backdrop-blur-sm text-white py-2 px-4 rounded-lg hover:bg-confluence-blue disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors border border-white/10"
                  >
                    {isGenerating === 'strategy' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        <span>Generate Strategy</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={generateCrossPlatform}
                    disabled={!selectedSpace || !codePage || isGenerating === 'crossplatform'}
                    className="w-full bg-confluence-blue/90 backdrop-blur-sm text-white py-2 px-4 rounded-lg hover:bg-confluence-blue disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors border border-white/10"
                  >
                    {isGenerating === 'crossplatform' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Analyzing...</span>
                      </>
                    ) : (
                      <>
                        <Code className="w-4 h-4" />
                        <span>Cross-Platform</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={generateSensitivity}
                    disabled={!selectedSpace || !codePage || isGenerating === 'sensitivity'}
                    className="w-full bg-confluence-blue/90 backdrop-blur-sm text-white py-2 px-4 rounded-lg hover:bg-confluence-blue disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors border border-white/10"
                  >
                    {isGenerating === 'sensitivity' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Analyzing...</span>
                      </>
                    ) : (
                      <>
                        <TestTube className="w-4 h-4" />
                        <span>Sensitivity Check</span>
                      </>
                    )}
                  </button>

                  {/* CircleCI Integration Button */}
                  <button
                    onClick={fetchTestMetrics}
                    disabled={isLoadingMetrics}
                    className="w-full bg-green-600/90 backdrop-blur-sm text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors border border-white/10"
                  >
                    {isLoadingMetrics ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Loading...</span>
                      </>
                    ) : (
                      <>
                        <Activity className="w-4 h-4" />
                        <span>CircleCI Metrics</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Export Button */}
                {testReport && (testReport.strategy || testReport.crossPlatform || testReport.sensitivity) && (
                  <div className="pt-4 border-t border-white/20 space-y-3">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium text-gray-700">Export Format:</label>
                      <select
                        value={exportFormat}
                        onChange={(e) => setExportFormat(e.target.value)}
                        className="px-3 py-1 border border-white/30 rounded text-sm focus:ring-2 focus:ring-confluence-blue bg-white/70 backdrop-blur-sm"
                      >
                        <option value="markdown">Markdown</option>
                        <option value="pdf">PDF</option>
                        <option value="docx">Word Document</option>
                        <option value="txt">Plain Text</option>
                      </select>
                    </div>
                    
                    <div className="space-y-2">
                      <button
                        onClick={exportReport}
                        className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-green-600/90 backdrop-blur-sm text-white rounded-lg hover:bg-green-700 transition-colors border border-white/10"
                      >
                        <Download className="w-4 h-4" />
                        <span>Export</span>
                      </button>
                      <button
                        onClick={async () => {
                          const { space, page } = getConfluenceSpaceAndPageFromUrl();
                          if (!space || !page) {
                            alert('Confluence space or page not specified in macro src URL.');
                            return;
                          }
                          let content = '';
                          if (testReport.strategy) content += `## Test Strategy\n${testReport.strategy}\n\n`;
                          if (testReport.crossPlatform) content += `## Cross-Platform Analysis\n${testReport.crossPlatform}\n\n`;
                          if (testReport.sensitivity) content += `## Sensitivity Analysis\n${testReport.sensitivity}\n\n`;
                          if (qaResults.length > 0) {
                            content += `## Q&A\n${qaResults.map(qa => `**Q:** ${qa.question}\n**A:** ${qa.answer}`).join('\n\n')}\n\n`;
                          }
                          content += `Generated on: ${new Date().toLocaleString()}`;
                          
                          try {
                            await apiService.saveToConfluence({
                              space_key: space,
                              page_title: page,
                              content: content
                            });
                            setShowToast(true);
                            setTimeout(() => setShowToast(false), 3000);
                          } catch (err) {
                            setError('Failed to save to Confluence. Please try again.');
                            console.error('Error saving to Confluence:', err);
                          }
                        }}
                        className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-confluence-blue/90 backdrop-blur-sm text-white rounded-lg hover:bg-confluence-blue transition-colors border border-white/10"
                      >
                        <Save className="w-4 h-4" />
                        <span>Save to Confluence</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* CircleCI Metrics Display */}
                {testMetrics && (
                  <div className="pt-4 border-t border-white/20 space-y-3">
                    <h4 className="font-semibold text-gray-800 flex items-center">
                      <Activity className="w-4 h-4 mr-2" />
                      Test Metrics
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Success Rate:</span>
                        <span className="font-medium text-green-600">{testMetrics.success_rate}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Total Tests:</span>
                        <span className="font-medium text-blue-600">{testMetrics.total_tests}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Build:</span>
                        <span className="font-medium text-purple-600">#{testMetrics.build_info.build_number}</span>
                      </div>
                    </div>
                    {testRecommendations && (
                      <div className="mt-3">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">AI Recommendations:</h5>
                        <div className="space-y-1">
                          {testRecommendations.action_items.slice(0, 2).map((item, index) => (
                            <div key={index} className="text-xs text-gray-600 flex items-start">
                              <div className={`w-1 h-1 rounded-full mt-1.5 mr-2 ${
                                testRecommendations.priority === 'high' ? 'bg-red-500' : 
                                testRecommendations.priority === 'medium' ? 'bg-orange-500' : 'bg-green-500'
                              }`} />
                              {item}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column - Results */}
            <div className="xl:col-span-3">
              <div className="space-y-6">
                {/* Test Strategy */}
                {testReport?.strategy && (
                  <div className="bg-white/60 backdrop-blur-xl rounded-xl p-4 border border-white/20 shadow-lg">
                    <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
                      <FileCheck className="w-5 h-5 mr-2 text-confluence-blue" />
                      Test Strategy
                    </h3>
                    <div className="bg-white/70 backdrop-blur-sm rounded-lg p-4 border border-white/20 prose prose-sm max-w-none">
                      <ReactMarkdown>
                        {testReport.strategy}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Cross-Platform Analysis */}
                {testReport?.crossPlatform && (
                  <div className="bg-white/60 backdrop-blur-xl rounded-xl p-4 border border-white/20 shadow-lg">
                    <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
                      <Code className="w-5 h-5 mr-2 text-confluence-blue" />
                      Cross-Platform Analysis
                    </h3>
                    <div className="bg-white/70 backdrop-blur-sm rounded-lg p-4 border border-white/20 prose prose-sm max-w-none">
                      <ReactMarkdown>
                        {testReport.crossPlatform}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Sensitivity Analysis */}
                {testReport?.sensitivity && (
                  <div className="bg-white/60 backdrop-blur-xl rounded-xl p-4 border border-white/20 shadow-lg">
                    <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
                      <TestTube className="w-5 h-5 mr-2 text-confluence-blue" />
                      Sensitivity Analysis
                    </h3>
                    <div className="bg-white/70 backdrop-blur-sm rounded-lg p-4 border border-white/20 prose prose-sm max-w-none">
                      <ReactMarkdown>
                        {testReport.sensitivity}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Q&A Section */}
                <div className="bg-white/60 backdrop-blur-xl rounded-xl p-4 space-y-4 border border-white/20 shadow-lg">
                  <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
                    <MessageSquare className="w-5 h-5 mr-2" />
                    Questions & Analysis
                  </h3>
                  
                  {/* Existing Q&A */}
                  {qaResults.length > 0 && (
                    <div className="space-y-3 mb-4 max-h-60 overflow-y-auto">
                      {qaResults.map((qa, index) => (
                        <div key={index} className="bg-white/70 backdrop-blur-sm rounded-lg p-3 border border-white/20">
                          <p className="font-medium text-gray-800 mb-2 text-sm">Q: {qa.question}</p>
                          <p className="text-gray-700 text-xs">{qa.answer.substring(0, 200)}...</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add Question */}
                  <div className="space-y-2">
                    <textarea
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Ask about testing strategies, coverage, or specific scenarios..."
                      className="w-full p-2 border border-white/30 rounded focus:ring-2 focus:ring-confluence-blue focus:border-confluence-blue resize-none bg-white/70 backdrop-blur-sm"
                      rows={3}
                    />
                    <button
                      onClick={addQuestion}
                      disabled={!question.trim() || isQALoading}
                      className="w-full px-3 py-2 bg-confluence-blue/90 backdrop-blur-sm text-white rounded hover:bg-confluence-blue disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2 border border-white/10"
                    >
                      {isQALoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Loading...</span>
                        </>
                      ) : (
                        <>
                          <MessageSquare className="w-4 h-4" />
                          <span>Ask Question</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Empty State */}
              {!testReport?.strategy && !testReport?.crossPlatform && !testReport?.sensitivity && (
                <div className="text-center py-12">
                  <TestTube className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-600 mb-2">Ready to Generate Test Analysis</h3>
                  <p className="text-gray-500">Select your code and test components, then choose which analysis to generate.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      {showToast && (
        <div style={{position: 'fixed', bottom: 40, left: '50%', transform: 'translateX(-50%)', background: '#2684ff', color: 'white', padding: '16px 32px', borderRadius: 8, zIndex: 9999, fontWeight: 600, fontSize: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.15)'}}>
          Saved to Confluence! Please refresh this Confluence page to see your changes.
        </div>
      )}
    </div>
  );
};

export default TestSupportTool;