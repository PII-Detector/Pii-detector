import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { FileUp, ArrowDownToLine, ShieldCheck } from "lucide-react";
import { renderAsync } from "docx-preview";
import { ToastContainer, toast } from "react-toastify";
import { motion } from "framer-motion";
import "react-toastify/dist/ReactToastify.css";

function App() {
  const [file, setFile] = useState(null);
  const [originalURL, setOriginalURL] = useState(null);
  const [redactedURL, setRedactedURL] = useState(null);
  const [redactedBlob, setRedactedBlob] = useState(null);
  const [loading, setLoading] = useState(false);
  const docxContainer = useRef(null);

  const handleFileChange = (e) => {
    const uploaded = e.target.files[0];
    setFile(uploaded);
    setOriginalURL(URL.createObjectURL(uploaded));
    setRedactedURL(null);
    setRedactedBlob(null);
    toast.info("File uploaded successfully.");
  };

  const handleRedact = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/redact", formData, {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: response.data.type });
      setRedactedBlob(blob);
      setRedactedURL(URL.createObjectURL(blob));
      toast.success("Redaction successful.");
    } catch (error) {
      toast.error(error?.response?.data?.message || "Redaction failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!redactedBlob) return;
    const link = document.createElement("a");
    link.href = redactedURL;
    link.download = `redacted_${file.name}`;
    link.click();
    toast.success("Download started.");
  };

  useEffect(() => {
    if (file && file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const arrayBuffer = e.target.result;
        await renderAsync(arrayBuffer, docxContainer.current);
      };
      reader.readAsArrayBuffer(file);
    }
  }, [file]);

  const renderPreview = (url, type, isRedacted = false) => {
    if (type.includes("pdf")) {
      return <iframe src={url} width="100%" height="500px" className="rounded-lg border shadow" title="PDF preview" />;
    } else if (type.includes("image")) {
      return <img src={url} alt="preview" className="max-w-full max-h-[500px] text-center object-contain rounded-lg shadow" />;
    } else if (type.includes("officedocument.wordprocessingml.document")) {
      return (
        <div className="p-4 border rounded bg-blue-50 text-blue-800">
          DOCX file uploaded. Preview:
          <div ref={docxContainer} className="mt-2 max-h-[500px] overflow-auto bg-white p-2 shadow" />
          {isRedacted && <p className="mt-2 text-green-600 font-medium">Redacted DOCX ready. Click download below.</p>}
        </div>
      );
    } else {
      return <p className="text-gray-600">Preview not supported for this file type.</p>;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f0f9ff] via-[#e0f2fe] to-[#f0fdf4] p-6">
      <ToastContainer />
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="max-w-5xl mx-auto bg-white rounded-2xl shadow-2xl p-8"
      >
        <h1 className="text-4xl font-extrabold text-center text-slate-800 mb-6 flex items-center justify-center gap-3">
          <ShieldCheck className="text-blue-600" /> PII Document Redactor
        </h1>

        <div className="mb-6 text-center">
          <label className="cursor-pointer inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-full shadow hover:bg-blue-700 transition">
            <FileUp className="mr-2" /> Upload File
            <input type="file" onChange={handleFileChange} className="hidden" />
          </label>
        </div>

        {originalURL && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-slate-700 mb-2">Original File Preview:</h2>
            {renderPreview(originalURL, file?.type)}
          </div>
        )}

        <div className="text-center">
          <button
            onClick={handleRedact}
            disabled={!file || loading}
            className="px-6 py-3 bg-purple-600 text-white font-semibold rounded-full shadow hover:bg-purple-700 disabled:opacity-50 transition"
          >
            {loading ? "Redacting..." : "Redact File"}
          </button>
        </div>

        {redactedURL && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-10"
          >
            <h2 className="text-lg font-semibold text-slate-700 mb-2">Redacted File Preview:</h2>
            {renderPreview(redactedURL, redactedBlob.type, true)}

            <div className="text-center mt-4">
              <button
                onClick={handleDownload}
                className="px-6 py-3 bg-green-600 text-white font-semibold rounded-full shadow hover:bg-green-700 transition inline-flex items-center"
              >
                <ArrowDownToLine className="mr-2" /> Download Redacted File
              </button>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}

export default App;
