import React, { useState } from "react";
import apiService from "../services/api";

const FlowchartGenerator: React.FC = () => {
  const [spaceKey, setSpaceKey] = useState("");
  const [pageTitle, setPageTitle] = useState("");
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <div className="p-6 max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">AI Flowchart Generator</h2>
      <div className="mb-2">
        <label className="block mb-1 font-medium">Space Key</label>
        <input
          className="border rounded px-2 py-1 w-full"
          value={spaceKey}
          onChange={e => setSpaceKey(e.target.value)}
          placeholder="e.g. DEMO"
        />
      </div>
      <div className="mb-2">
        <label className="block mb-1 font-medium">Page Title</label>
        <input
          className="border rounded px-2 py-1 w-full"
          value={pageTitle}
          onChange={e => setPageTitle(e.target.value)}
          placeholder="e.g. My Flowchart Page"
        />
      </div>
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded mt-2"
        onClick={handleGenerate}
        disabled={loading}
      >
        {loading ? "Generating..." : "Generate Flowchart"}
      </button>
      {error && <div className="text-red-600 mt-2">{error}</div>}
      {imageBase64 && (
        <div className="mt-6">
          <h3 className="font-semibold mb-2">Generated Flowchart:</h3>
          <img
            src={`data:image/png;base64,${imageBase64}`}
            alt="Flowchart"
            className="border rounded shadow"
            style={{ maxWidth: "100%" }}
          />
          <a
            href={`data:image/png;base64,${imageBase64}`}
            download={`${pageTitle}_flowchart.png`}
            className="block mt-2 text-blue-700 underline"
          >
            Download PNG
          </a>
        </div>
      )}
    </div>
  );
};

export default FlowchartGenerator; 