import React, { useState, useEffect } from "react";
import { ChevronDown, Loader2 } from 'lucide-react';
import apiService, { Space } from "../services/api";

const FlowchartGenerator: React.FC = () => {
  const [spaceKey, setSpaceKey] = useState("");
  const [pageTitle, setPageTitle] = useState("");
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [pages, setPages] = useState<string[]>([]);
  const [isLoadingSpaces, setIsLoadingSpaces] = useState(false);
  const [isLoadingPages, setIsLoadingPages] = useState(false);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load spaces on mount
  useEffect(() => {
    const loadSpaces = async () => {
      setIsLoadingSpaces(true);
      try {
        const response = await apiService.getSpaces();
        setSpaces(response.spaces);
        console.log("[FlowchartGenerator] Fetched spaces:", response.spaces); // DEBUG
      } catch (err) {
        setError("Failed to load spaces. Please check your backend connection.");
        console.error("[FlowchartGenerator] Error fetching spaces:", err); // DEBUG
      } finally {
        setIsLoadingSpaces(false);
      }
    };
    loadSpaces();
  }, []);

  // Load pages when spaceKey changes
  useEffect(() => {
    const loadPages = async () => {
      if (!spaceKey) {
        setPages([]);
        console.warn("[FlowchartGenerator] No valid spaceKey provided to loadPages:", spaceKey); // DEBUG
        return;
      }
      setIsLoadingPages(true);
      try {
        const response = await apiService.getPages(spaceKey);
        setPages(response.pages);
        console.log("[FlowchartGenerator] Fetched pages for spaceKey", spaceKey, ":", response.pages); // DEBUG
      } catch (err) {
        setError("Failed to load pages. Please check your space key.");
        setPages([]);
        console.error("[FlowchartGenerator] Error fetching pages:", err); // DEBUG
      } finally {
        setIsLoadingPages(false);
      }
    };
    loadPages();
  }, [spaceKey]);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setImageBase64(null);
    try {
      const result = await apiService.generateFlowchart(spaceKey, pageTitle);
      setImageBase64(result.image_base64);
    } catch (err: any) {
      setError("Failed to generate flowchart. Please check space key and page title.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white/60 backdrop-blur-xl rounded-xl p-8 border border-white/20 shadow-lg">
          <h2 className="text-2xl font-bold mb-6 text-center">AI Flowchart Generator</h2>
          {error && <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">{error}</div>}
          <div className="mb-6">
            {/* Space Dropdown */}
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Confluence Space</label>
            <div className="relative">
              <select
                value={spaceKey}
                onChange={e => { setSpaceKey(e.target.value); setPageTitle(""); }}
                disabled={isLoadingSpaces}
                className="w-full p-3 border border-white/30 rounded-lg focus:ring-2 focus:ring-confluence-blue focus:border-confluence-blue appearance-none bg-white/70 backdrop-blur-sm disabled:bg-gray-100"
              >
                <option value="">{isLoadingSpaces ? 'Loading spaces...' : 'Choose a space...'}</option>
                {spaces.map(space => (
                  <option key={space.key} value={space.key}>{space.name} ({space.key})</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            </div>
          </div>
          <div className="mb-6">
            {/* Page Dropdown */}
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Page Title</label>
            <div className="relative">
              <select
                value={pageTitle}
                onChange={e => setPageTitle(e.target.value)}
                disabled={!spaceKey || isLoadingPages}
                className="w-full p-3 border border-white/30 rounded-lg focus:ring-2 focus:ring-confluence-blue focus:border-confluence-blue appearance-none bg-white/70 backdrop-blur-sm disabled:bg-gray-100"
              >
                <option value="">{isLoadingPages ? 'Loading pages...' : (!spaceKey ? 'Select a space first...' : 'Choose a page...')}</option>
                {pages.map(page => (
                  <option key={page} value={page}>{page}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            </div>
          </div>
          <button
            className="w-full bg-confluence-blue/90 backdrop-blur-sm text-white py-3 px-4 rounded-lg hover:bg-confluence-blue disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors border border-white/10"
            onClick={handleGenerate}
            disabled={!spaceKey || !pageTitle || loading}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Generating...</span>
              </>
            ) : (
              <span>Generate Flowchart</span>
            )}
          </button>
          {imageBase64 && (
            <div className="mt-8 text-center">
              <h3 className="font-semibold mb-2">Generated Flowchart:</h3>
              <img
                src={`data:image/png;base64,${imageBase64}`}
                alt="Flowchart"
                className="border rounded shadow mx-auto"
                style={{ maxWidth: "100%" }}
              />
              <a
                href={`data:image/png;base64,${imageBase64}`}
                download={`${pageTitle}_flowchart.png`}
                className="block mt-2 text-confluence-blue underline"
              >
                Download PNG
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FlowchartGenerator;