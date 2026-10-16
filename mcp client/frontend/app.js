const { useState, useEffect, useMemo, useCallback } = React;

const API_BASE = "";

// SVG Icon Helper
function Icon({ name, size = 18, className = "" }) {
  const icons = {
    dashboard: <path d="M3 3h7v9H3V3zm11 0h7v5h-7V3zm0 9h7v9h-7v-9zM3 16h7v5H3v-5z"/>,
    upload: <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>,
    mapping: <path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>,
    tools: <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>,
    database: <path d="M4 6c0 1.66 3.58 3 8 3s8-1.34 8-3-3.58-3-8-3-8 1.34-8 3zm0 6c0 1.66 3.58 3 8 3s8-1.34 8-3M4 18c0 1.66 3.58 3 8 3s8-1.34 8-3M20 6v12M4 6v12"/>,
    validation: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zm-1-8l-3-3 1.41-1.41L11 11.17l5.59-5.59L18 7l-7 7z"/>,
    check: <polyline points="20 6 9 17 4 12"/>,
    alert: <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"/>,
    trash: <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>,
    refresh: <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>,
    plus: <path d="M12 5v14M5 12h14"/>,
    search: <g><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></g>,
    menu: <g><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></g>,
    edit: <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>,
    bot: <g><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4M8 16h.01M16 16h.01"/></g>,
    send: <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>,
    close: <g><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></g>,
    table: <g><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></g>,
    paperclip: <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>,
    file: <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6"/>
  };

  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      {icons[name] || null}
    </svg>
  );
}

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Global state
  const [dbRecords, setDbRecords] = useState([]);
  const [dbTotal, setDbTotal] = useState(0);
  const [activeColumns, setActiveColumns] = useState([]);
  const [qualityScore, setQualityScore] = useState(100);
  const [validationReport, setValidationReport] = useState(null);
  const [recentActivities, setRecentActivities] = useState([
    { id: 1, text: "System initialized with standardized SQLite database", time: "Just now", type: "success" }
  ]);
  const [toasts, setToasts] = useState([]);

  // Upload & Mapping state
  const [activeFile, setActiveFile] = useState(null);
  const [classificationResults, setClassificationResults] = useState([]);
  const [isClassifying, setIsClassifying] = useState(false);
  const [isStoring, setIsStoring] = useState(false);

  // Modal State for safety confirmations
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, title: "", message: "", onConfirm: null });
  const [editTargetRowId, setEditTargetRowId] = useState(null);

  // AI Assistant state
  const [isAssistantDrawerOpen, setIsAssistantDrawerOpen] = useState(false);
  const [assistantMessages, setAssistantMessages] = useState([
    {
      id: "m_welcome",
      role: "assistant",
      content: "Hello! I am your AI Data Assistant powered by OpenRouter and Model Context Protocol (MCP). I can search, query, inspect quality, add, edit, or delete records in your standardized database using real MCP tools. How can I help you today?",
      tool_called: null,
      data: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [isAssistantThinking, setIsAssistantThinking] = useState(false);

  // Remove toast helper
  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Add toast helper - automatically pops up and disappears after 3 seconds
  const addToast = useCallback((message, type = "success", duration = 3000) => {
    const id = "t_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const addActivity = useCallback((text, type = "info") => {
    setRecentActivities(prev => [{ id: Date.now(), text, time: "Just now", type }, ...prev.slice(0, 7)]);
  }, []);

  // Fetch Database View & Columns
  const fetchDatabase = useCallback(async (searchQuery = "") => {
    try {
      const resp = await fetch(`${API_BASE}/api/database/view?search=${encodeURIComponent(searchQuery)}&limit=1000`);
      const res = await resp.json();
      if (res.status === "success") {
        const records = res.data?.records || [];
        setDbRecords(records);
        setDbTotal(res.data?.total_count || records.length);
        if (res.schema?.columns) {
          setActiveColumns(res.schema.columns);
        }
      }
    } catch (err) {
      console.error("Failed to fetch database:", err);
    }
  }, []);

  // Fetch Data Quality Check
  const fetchHealthCheck = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/check_data?table=customers`);
      const data = await resp.json();
      if (data.status === "success") {
        setQualityScore(data.data_quality_score || 100);
        setValidationReport(data);
      }
    } catch (err) {
      console.error("Health check error:", err);
    }
  }, []);

  useEffect(() => {
    fetchDatabase();
    fetchHealthCheck();
  }, [fetchDatabase, fetchHealthCheck]);

  // AI Assistant Send Message Handler
  const handleSendAssistantMessage = useCallback(async (text, confirmedAction = null) => {
    if (!text && !confirmedAction) return;

    if (text) {
      const userMsg = {
        id: "usr_" + Date.now(),
        role: "user",
        content: text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setAssistantMessages(prev => [...prev, userMsg]);
    }

    setIsAssistantThinking(true);

    try {
      const historyPayload = assistantMessages.slice(-6).map(m => ({
        role: m.role,
        content: m.content || m.message || "",
        tool_called: m.tool_called,
        tool_args: m.tool_args,
        requires_confirmation: m.requires_confirmation
      }));

      const resp = await fetch(`${API_BASE}/api/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text || "",
          conversation_history: historyPayload,
          confirmed_action: confirmedAction
        })
      });

      const data = await resp.json();
      setIsAssistantThinking(false);

      if (!resp.ok) {
        setAssistantMessages(prev => [...prev, {
          id: "err_" + Date.now(),
          role: "assistant",
          status: "error",
          content: data.detail || "Error connecting to AI Assistant service.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
        return;
      }

      const asstMsg = {
        id: "asst_" + Date.now(),
        role: "assistant",
        status: data.status,
        content: data.message,
        tool_called: data.tool_called,
        tool_args: data.tool_args,
        data: data.data,
        data_type: data.data_type,
        preview: data.preview,
        requires_confirmation: data.requires_confirmation,
        executed: data.executed,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setAssistantMessages(prev => [...prev, asstMsg]);

      if (data.executed) {
        fetchDatabase();
        fetchHealthCheck();
        addToast(data.message || "Database updated by AI Assistant", "success");
        addActivity(`AI Assistant executed ${data.tool_called}: ${data.message}`, "success");
      }

    } catch (err) {
      setIsAssistantThinking(false);
      setAssistantMessages(prev => [...prev, {
        id: "err_" + Date.now(),
        role: "assistant",
        status: "error",
        content: "Network error communicating with AI Assistant: " + err.message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    }
  }, [assistantMessages, fetchDatabase, fetchHealthCheck, addToast, addActivity]);

  const handleConfirmAssistantAction = useCallback((toolName, toolArgs, messageId) => {
    setAssistantMessages(prev => prev.map(m => m.id === messageId ? { ...m, requires_confirmation: false } : m));
    handleSendAssistantMessage(null, { confirmed: true, tool_name: toolName, tool_args: toolArgs });
  }, [handleSendAssistantMessage]);

  const handleCancelAssistantAction = useCallback((messageId) => {
    setAssistantMessages(prev => prev.map(m => m.id === messageId ? { ...m, requires_confirmation: false, content: m.content + "\n\n(Operation cancelled by user — no database changes made.)" } : m));
    addToast("Operation cancelled", "info");
  }, [addToast]);

  // Assistant File Upload & Processing Handler
  const handleAssistantUpload = useCallback(async (file, userPrompt) => {
    if (!file) return;

    // 1. Frontend validation of file type
    const lowerName = file.name.toLowerCase();
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const isValid = validExtensions.some(ext => lowerName.endsWith(ext));
    if (!isValid) {
      addToast("Unsupported file type. Please upload a CSV or Excel file.", "error");
      setAssistantMessages(prev => [...prev, {
        id: "err_" + Date.now(),
        role: "assistant",
        status: "error",
        content: "Unsupported file type. Please upload a CSV or Excel file (.csv, .xlsx, or .xls).",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
      return;
    }

    // 2. Add user message with attachment tag
    const userMsg = {
      id: "usr_" + Date.now(),
      role: "user",
      content: userPrompt ? userPrompt : `Uploaded dataset: ${file.name}`,
      attachment: {
        name: file.name,
        size: (file.size / 1024).toFixed(1) + " KB"
      },
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setAssistantMessages(prev => [...prev, userMsg]);
    setIsAssistantThinking(true);

    try {
      // 3. Upload file via existing /api/upload
      const formData = new FormData();
      formData.append("file", file);
      const uploadResp = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData
      });
      const uploadText = await uploadResp.text();
      let uploadData;
      try {
        uploadData = JSON.parse(uploadText);
      } catch (e) {
        uploadData = { detail: uploadText || `Upload failed (Status ${uploadResp.status})` };
      }

      if (!uploadResp.ok) {
        setIsAssistantThinking(false);
        addToast(uploadData.detail || "Upload failed", "error");
        setAssistantMessages(prev => [...prev, {
          id: "err_" + Date.now(),
          role: "assistant",
          status: "error",
          content: uploadData.detail || "Unsupported file format. Please upload a CSV or Excel file.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
        return;
      }

      setActiveFile(uploadData);
      addToast(`File ${uploadData.filename} uploaded successfully`, "success");
      addActivity(`Uploaded "${uploadData.filename}" via AI Assistant (${uploadData.total_rows} records detected)`, "success");

      // 4. Classify columns via existing /api/classify_columns
      const classifyResp = await fetch(`${API_BASE}/api/classify_columns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: uploadData.file_id,
          filepath: uploadData.filepath,
          format: uploadData.format
        })
      });
      const classifyText = await classifyResp.text();
      let classifyData;
      try {
        classifyData = JSON.parse(classifyText);
      } catch (e) {
        classifyData = { detail: classifyText || `Classification failed (Status ${classifyResp.status})` };
      }
      setIsAssistantThinking(false);

      if (!classifyResp.ok) {
        addToast(classifyData.detail || "Classification failed", "error");
        setAssistantMessages(prev => [...prev, {
          id: "err_" + Date.now(),
          role: "assistant",
          status: "error",
          content: classifyData.detail || "Column classification failed.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
        return;
      }

      const results = classifyData.classification || [];
      setClassificationResults(results);

      const unconfirmedCount = results.filter(c => c.requires_confirmation).length;
      if (unconfirmedCount > 0) {
        addToast(`${unconfirmedCount} column(s) require your manual confirmation`, "warning");
        addActivity(`Column classification: ${unconfirmedCount} require user confirmation`, "warning");
      } else {
        addToast("All columns matched with high confidence (≥ 90%)!", "success");
        addActivity("All columns standardized automatically with ≥ 90% confidence", "success");
      }

      // 5. Build assistant explanation based on user instruction and confidence
      let explanation = "";
      const lowerPrompt = (userPrompt || "").toLowerCase();
      if (lowerPrompt.includes("check") || lowerPrompt.includes("column") || lowerPrompt.includes("map")) {
        explanation = `Analyzed "${uploadData.filename}" (${uploadData.format.toUpperCase()}, ${uploadData.total_rows} records, ${uploadData.columns.length} columns). Here is the schema mapping analysis against your database:`;
      } else if (unconfirmedCount > 0) {
        explanation = `File "${uploadData.filename}" uploaded and analyzed. ${unconfirmedCount} column(s) have confidence below 90% and require your confirmation before saving to SQLite. Please review the mappings below:`;
      } else {
        explanation = `File "${uploadData.filename}" uploaded successfully (${uploadData.format.toUpperCase()}, ${uploadData.total_rows} records). All columns matched with high confidence (≥ 90%). Please review the mappings and confirm ingestion:`;
      }

      // 6. Append Assistant message with interactive mapping results
      setAssistantMessages(prev => [...prev, {
        id: "asst_map_" + Date.now(),
        role: "assistant",
        status: "success",
        content: explanation,
        file_info: uploadData,
        data_type: "column_mapping",
        mapping_results: results,
        target_columns: classifyData.target_columns || activeColumns.map(c => c.column_name || c),
        requires_mapping_confirm: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

    } catch (err) {
      setIsAssistantThinking(false);
      addToast("Error: " + err.message, "error");
      setAssistantMessages(prev => [...prev, {
        id: "err_" + Date.now(),
        role: "assistant",
        status: "error",
        content: "Error during file upload and column classification: " + err.message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    }
  }, [addToast, addActivity, activeColumns]);

  const handleConfirmMappingIngest = useCallback(async (messageId, fileInfo, currentMappings) => {
    // Disable buttons on the mapping card
    setAssistantMessages(prev => prev.map(m => m.id === messageId ? { ...m, requires_mapping_confirm: false, confirmed_mappings: currentMappings } : m));
    setIsAssistantThinking(true);
    addToast("Validating and storing standardized records into SQLite...", "info");

    try {
      const resp = await fetch(`${API_BASE}/api/standardize_and_store`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileInfo.file_id,
          filepath: fileInfo.filepath,
          format: fileInfo.format,
          mappings: currentMappings.map(c => ({
            input_column: c.input_column,
            standardized_column: c.standardized_column,
            confidence: c.confidence,
            method: c.method
          }))
        })
      });

      const respText = await resp.text();
      let data;
      try {
        data = JSON.parse(respText);
      } catch (e) {
        data = { detail: respText || `Server returned error (${resp.status})` };
      }

      setIsAssistantThinking(false);

      if (!resp.ok) {
        addToast(data.detail || "Failed to store data", "error");
        setAssistantMessages(prev => [...prev, {
          id: "err_" + Date.now(),
          role: "assistant",
          status: "error",
          content: data.detail || "Failed to standardize and store records.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
        return;
      }

      addToast(`${data.inserted_count} records standardized and stored into SQLite!`, "success");
      addActivity(`Standardized and stored ${data.inserted_count} records from "${fileInfo.filename}"`, "success");

      // Synchronize live database & health checks
      fetchDatabase();
      fetchHealthCheck();

      // Append success message with readable validation stats
      setAssistantMessages(prev => [...prev, {
        id: "asst_stored_" + Date.now(),
        role: "assistant",
        status: "success",
        content: `Standardization & Ingestion Complete!\n\nSuccessfully standardized and stored ${data.inserted_count} records from "${fileInfo.filename}" into the SQLite database.`,
        data_type: "ingestion_result",
        inserted_count: data.inserted_count,
        validation_report: data.validation_report,
        executed: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

    } catch (err) {
      setIsAssistantThinking(false);
      addToast("Network error storing data: " + err.message, "error");
      setAssistantMessages(prev => [...prev, {
        id: "err_" + Date.now(),
        role: "assistant",
        status: "error",
        content: "Network error storing standardized data: " + err.message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    }
  }, [fetchDatabase, fetchHealthCheck, addToast, addActivity]);

  const handleCancelMapping = useCallback((messageId) => {
    setAssistantMessages(prev => prev.map(m => m.id === messageId ? { ...m, requires_mapping_confirm: false, content: m.content + "\n\n(Standardization cancelled by user — no records stored in database.)" } : m));
    addToast("File processing cancelled", "info");
  }, [addToast]);

  // Handle File Upload
  const handleFileUpload = async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    addToast(`Uploading ${file.name}...`, "info");
    try {
      const resp = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData
      });
      const data = await resp.json();

      if (!resp.ok) {
        addToast(data.detail || "Upload failed", "error");
        return;
      }

      setActiveFile(data);
      addToast(`File ${data.filename} uploaded successfully`, "success");
      addActivity(`Uploaded file "${data.filename}" (${data.total_rows} records detected)`, "success");

      // Auto start classification and transition to mapping
      classifyColumns(data);
    } catch (err) {
      addToast("Network error uploading file: " + err.message, "error");
    }
  };

  // Classify Columns
  const classifyColumns = async (fileObj) => {
    setIsClassifying(true);
    addToast("Analyzing columns and calculating confidence...", "info");
    try {
      const resp = await fetch(`${API_BASE}/api/classify_columns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileObj.file_id,
          filepath: fileObj.filepath,
          format: fileObj.format
        })
      });
      const data = await resp.json();
      setIsClassifying(false);

      if (!resp.ok) {
        addToast(data.detail || "Classification failed", "error");
        return;
      }

      setClassificationResults(data.classification || []);
      const unconfirmedCount = data.classification.filter(c => c.requires_confirmation).length;
      
      if (unconfirmedCount > 0) {
        addToast(`${unconfirmedCount} column(s) require your manual confirmation`, "warning");
        addActivity(`Column classification completed: ${unconfirmedCount} need confirmation`, "warning");
      } else {
        addToast("All columns matched with high confidence (≥ 90%)!", "success");
        addActivity("All columns standardized automatically with ≥ 90% confidence", "success");
      }

      setActiveTab("mapping");
    } catch (err) {
      setIsClassifying(false);
      addToast("Error during column classification: " + err.message, "error");
    }
  };

  // Save & Ingest
  const handleSaveStandardized = async () => {
    if (!activeFile || classificationResults.length === 0) return;

    setIsStoring(true);
    addToast("Validating, cleaning, and storing records into SQLite...", "info");

    const mappings = classificationResults.map(c => ({
      input_column: c.input_column,
      standardized_column: c.standardized_column,
      confidence: c.confidence,
      method: c.method
    }));

    try {
      const resp = await fetch(`${API_BASE}/api/standardize_and_store`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: activeFile.file_id,
          filepath: activeFile.filepath,
          format: activeFile.format,
          mappings: mappings
        })
      });
      const data = await resp.json();
      setIsStoring(false);

      if (!resp.ok) {
        addToast(data.detail || "Failed to store standardized data", "error");
        return;
      }

      addToast(`${data.inserted_count} records standardized and stored into database!`, "success");
      addActivity(`Standardized and stored ${data.inserted_count} records from "${activeFile.filename}"`, "success");
      
      fetchDatabase();
      fetchHealthCheck();
      setActiveTab("database");
    } catch (err) {
      setIsStoring(false);
      addToast("Network error storing data: " + err.message, "error");
    }
  };

  // Cancel & Clear Upload without saving
  const handleClearUpload = () => {
    if (!activeFile && (!classificationResults || classificationResults.length === 0)) {
      addToast("No active upload to clear", "info");
      return;
    }

    setConfirmModal({
      isOpen: true,
      title: "Cancel & Clear Uploaded Data?",
      message: `Are you sure you want to discard "${activeFile?.filename || 'the uploaded file'}" and clear all detected column mappings without saving to the database?`,
      confirmText: "Yes, Clear & Discard",
      confirmBtnClass: "btn btn-danger",
      onConfirm: () => {
        const discardedName = activeFile?.filename;
        setActiveFile(null);
        setClassificationResults([]);
        addToast(`Uploaded dataset "${discardedName || 'file'}" cleared without saving.`, "info");
        addActivity(`Discarded uploaded dataset "${discardedName || 'file'}" without saving`, "info");
        setActiveTab("upload");
      }
    });
  };

  const pendingConfirmCount = useMemo(() => {
    return classificationResults.filter(c => c.requires_confirmation).length;
  }, [classificationResults]);

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-header">
          <div className="brand-group">
            <div className="brand-icon">M</div>
            {!sidebarCollapsed && (
              <div>
                <div className="brand-title">DataStandard</div>
                <div className="brand-subtitle">MCP Enterprise Engine</div>
              </div>
            )}
          </div>
          <button 
            className="sidebar-toggle-btn"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title="Toggle Sidebar"
          >
            <Icon name="menu" size={16} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {[
            { id: "dashboard", label: "Dashboard", icon: "dashboard" },
            { id: "upload", label: "Upload Data", icon: "upload" },
            { id: "mapping", label: "Column Mapping", icon: "mapping", badge: pendingConfirmCount > 0 ? `${pendingConfirmCount}` : null, badgeType: "warn" },
            { id: "tools", label: "Database Tools", icon: "tools" },
            { id: "database", label: "Database", icon: "database", badge: `${dbTotal}`, badgeType: "count" },
            { id: "validation", label: "Validation", icon: "validation" },
            { id: "assistant", label: "AI Assistant", icon: "bot", badge: "AI", badgeType: "ai" }
          ].map(tab => (
            <button
              key={tab.id}
              className={`nav-item ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="nav-icon"><Icon name={tab.icon} /></span>
              {!sidebarCollapsed && <span className="nav-label">{tab.label}</span>}
              {!sidebarCollapsed && tab.badge && (
                <span className={`nav-badge ${tab.badgeType === "warn" ? "nav-badge-warn" : tab.badgeType === "ai" ? "nav-badge-ai" : "nav-badge-count"}`}>
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="server-status-pill">
            <span className="status-dot"></span>
            {!sidebarCollapsed && <span>MCP Server Connected</span>}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-navbar">
          <div className="top-navbar-title">
            <span>
              {activeTab === "dashboard" && "Enterprise Data Dashboard"}
              {activeTab === "upload" && "Upload CSV / Excel Dataset"}
              {activeTab === "mapping" && "Column Mapping & Standardization"}
              {activeTab === "tools" && "Database Tools"}
              {activeTab === "database" && "SQLite Database Explorer"}
              {activeTab === "validation" && "Data Quality & Validation Report"}
              {activeTab === "assistant" && "AI Assistant — Natural Language MCP Database Controller"}
            </span>
          </div>

          <div className="top-navbar-actions">
            <button 
              className={`btn ${isAssistantDrawerOpen ? "btn-primary" : "btn-outline"}`} 
              onClick={() => setIsAssistantDrawerOpen(prev => !prev)}
              title="Toggle AI Assistant Column / Side Panel"
            >
              <Icon name="bot" size={15} /> AI Assistant Panel
            </button>
            <button className="btn btn-outline" onClick={() => { fetchDatabase(); fetchHealthCheck(); addToast("Database refreshed", "info"); }}>
              <Icon name="refresh" size={15} /> Refresh
            </button>
            <button className="btn btn-primary" onClick={() => setActiveTab("upload")}>
              <Icon name="upload" size={15} /> Upload Data
            </button>
          </div>
        </header>

        <main className="content-body animate-fade">
          {activeTab === "dashboard" && (
            <DashboardView 
              dbTotal={dbTotal}
              columnsCount={activeColumns.length}
              qualityScore={qualityScore}
              activeFile={activeFile}
              pendingConfirmCount={pendingConfirmCount}
              recentActivities={recentActivities}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === "upload" && (
            <UploadView 
              activeFile={activeFile}
              onUpload={handleFileUpload}
              isClassifying={isClassifying}
              onProceedToMapping={() => setActiveTab("mapping")}
              onClearUpload={handleClearUpload}
            />
          )}

          {activeTab === "mapping" && (
            <ColumnMappingView 
              results={classificationResults}
              setResults={setClassificationResults}
              targetColumns={activeColumns}
              activeFile={activeFile}
              onSave={handleSaveStandardized}
              onClearUpload={handleClearUpload}
              isStoring={isStoring}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === "tools" && (
            <MCPToolsView 
              activeColumns={activeColumns}
              fetchDatabase={fetchDatabase}
              addToast={addToast}
              addActivity={addActivity}
              setConfirmModal={setConfirmModal}
              editTargetRowId={editTargetRowId}
              setEditTargetRowId={setEditTargetRowId}
            />
          )}

          {activeTab === "database" && (
            <DatabaseView 
              records={dbRecords}
              total={dbTotal}
              fetchDatabase={fetchDatabase}
              addToast={addToast}
              addActivity={addActivity}
              setConfirmModal={setConfirmModal}
              onEditRow={(id) => {
                setEditTargetRowId(id);
                setActiveTab("tools");
              }}
            />
          )}

          {activeTab === "validation" && (
            <ValidationView 
              validationReport={validationReport}
              qualityScore={qualityScore}
              fetchHealthCheck={fetchHealthCheck}
              fetchDatabase={fetchDatabase}
              addToast={addToast}
              addActivity={addActivity}
              setConfirmModal={setConfirmModal}
            />
          )}

          {activeTab === "assistant" && (
            <AIAssistantView 
              messages={assistantMessages}
              onSendMessage={handleSendAssistantMessage}
              onSendFile={handleAssistantUpload}
              isThinking={isAssistantThinking}
              onConfirmAction={handleConfirmAssistantAction}
              onCancelAction={handleCancelAssistantAction}
              onConfirmMappingIngest={handleConfirmMappingIngest}
              onCancelMapping={handleCancelMapping}
              targetColumns={activeColumns}
              onToast={addToast}
            />
          )}
        </main>
      </div>

      {/* Side-by-side AI Assistant Column / Drawer */}
      <AIAssistantDrawer 
        isOpen={isAssistantDrawerOpen}
        onClose={() => setIsAssistantDrawerOpen(false)}
        messages={assistantMessages}
        onSendMessage={handleSendAssistantMessage}
        onSendFile={handleAssistantUpload}
        isThinking={isAssistantThinking}
        onConfirmAction={handleConfirmAssistantAction}
        onCancelAction={handleCancelAssistantAction}
        onConfirmMappingIngest={handleConfirmMappingIngest}
        onCancelMapping={handleCancelMapping}
        targetColumns={activeColumns}
        onToast={addToast}
      />

      {/* Confirmation Modal */}
      {confirmModal.isOpen && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-title">{confirmModal.title}</div>
            <div className="modal-desc">{confirmModal.message}</div>
            <div className="modal-actions">
              <button 
                className="btn btn-outline"
                onClick={() => setConfirmModal({ ...confirmModal, isOpen: false })}
              >
                Cancel
              </button>
              <button 
                className={confirmModal.confirmBtnClass || "btn btn-danger"}
                onClick={() => {
                  if (confirmModal.onConfirm) confirmModal.onConfirm();
                  setConfirmModal({ ...confirmModal, isOpen: false });
                }}
              >
                {confirmModal.confirmText || "Confirm Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Toast Alerts */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            {t.type === "success" && <Icon name="check" size={16} />}
            {t.type === "warning" && <Icon name="alert" size={16} />}
            {t.type === "error" && <Icon name="alert" size={16} />}
            {t.type === "info" && <Icon name="refresh" size={16} />}
            <span style={{ flex: 1 }}>{t.message}</span>
            <button 
              className="toast-close" 
              onClick={() => removeToast(t.id)} 
              title="Close"
              aria-label="Close"
            >
              &times;
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// 1. Dashboard Component
// ------------------------------------------------------------------
function DashboardView({ dbTotal, columnsCount, qualityScore, activeFile, pendingConfirmCount, recentActivities, setActiveTab }) {
  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-primary">
            <Icon name="database" size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Total Records</span>
            <span className="stat-value">{dbTotal}</span>
            <span className="stat-subtext">Stored in SQLite customers table</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-success">
            <Icon name="mapping" size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Active Columns</span>
            <span className="stat-value">{columnsCount || 5}</span>
            <span className="stat-subtext">Standard schema definitions</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-warning">
            <Icon name="validation" size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Data Quality</span>
            <span className="stat-value">{qualityScore}%</span>
            <span className="stat-subtext">Automated integrity rating</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-primary">
            <Icon name="upload" size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Active Dataset</span>
            <span className="stat-value" style={{ fontSize: '18px', marginTop: '6px' }}>
              {activeFile ? activeFile.filename : "None uploaded"}
            </span>
            <span className="stat-subtext">{activeFile ? `${activeFile.total_rows} rows` : "Upload a CSV or Excel"}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
        {/* Quick Action Shortcuts */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Quick Actions</div>
              <div className="card-desc">Standard workflow shortcuts for common tasks</div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div 
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0', cursor: 'pointer' }}
              onClick={() => setActiveTab("upload")}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ padding: '8px', background: '#eff6ff', borderRadius: '8px', color: '#2563eb' }}><Icon name="upload" /></span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px' }}>Upload New File</div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>Import CSV or Excel (.xlsx)</div>
                </div>
              </div>
              <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '12px' }}>Go</button>
            </div>

            <div 
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0', cursor: 'pointer' }}
              onClick={() => setActiveTab("tools")}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ padding: '8px', background: '#ecfdf5', borderRadius: '8px', color: '#059669' }}><Icon name="tools" /></span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px' }}>Run Database Tools</div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>Check, extract, add or delete records</div>
                </div>
              </div>
              <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '12px' }}>Go</button>
            </div>

            <div 
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 16px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0', cursor: 'pointer' }}
              onClick={() => setActiveTab("database")}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ padding: '8px', background: '#fef3c7', borderRadius: '8px', color: '#d97706' }}><Icon name="database" /></span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px' }}>Explore Database</div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>View all {dbTotal} standardized entries</div>
                </div>
              </div>
              <button className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '12px' }}>Go</button>
            </div>
          </div>
        </div>

        {/* Recent Activity Timeline */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recent Activity</div>
              <div className="card-desc">Audit trail of preprocessing & MCP operations</div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {recentActivities.map(act => (
              <div key={act.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 12px', background: '#ffffff', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: act.type === 'success' ? '#10b981' : act.type === 'warning' ? '#f59e0b' : '#3b82f6' }}></span>
                <div style={{ flex: 1, fontSize: '13px', fontWeight: 500, color: '#334155' }}>{act.text}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>{act.time}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// 2. Upload Data Component
// ------------------------------------------------------------------
function UploadView({ activeFile, onUpload, isClassifying, onProceedToMapping, onClearUpload }) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Upload Tabular Dataset</div>
            <div className="card-desc">Upload CSV or Excel (.xlsx, .xls) files. Format detection and encoding are handled automatically.</div>
          </div>
        </div>

        <div 
          className={`upload-zone ${isDragOver ? "dragover" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById("hiddenFileInput").click()}
        >
          <input 
            type="file" 
            id="hiddenFileInput" 
            accept=".csv, .xlsx, .xls" 
            style={{ display: 'none' }}
            onChange={(e) => { if (e.target.files.length > 0) onUpload(e.target.files[0]); }}
          />
          <div className="upload-zone-icon">📁</div>
          <div className="upload-zone-title">Click to browse or drop file here</div>
          <div className="upload-zone-sub">Supported formats: CSV, Excel (.xlsx, .xls)</div>
        </div>

        {activeFile && (
          <div style={{ marginTop: '20px', padding: '16px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <span style={{ fontSize: '24px' }}>📄</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '14.5px' }}>{activeFile.filename}</div>
                <div style={{ fontSize: '12px', color: '#64748b', display: 'flex', gap: '10px', marginTop: '2px' }}>
                  <span>Format: <strong>{activeFile.format.toUpperCase()}</strong></span>
                  <span>&bull;</span>
                  <span>{activeFile.total_rows} records detected</span>
                  <span>&bull;</span>
                  <span>{activeFile.columns.length} columns</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button 
                type="button"
                className="btn btn-outline"
                disabled={isClassifying}
                onClick={onClearUpload}
                title="Discard and clear this file"
              >
                <Icon name="trash" size={14} /> Clear Upload
              </button>
              <button 
                type="button"
                className="btn btn-primary"
                disabled={isClassifying}
                onClick={onProceedToMapping}
              >
                {isClassifying ? "Standardizing Columns..." : "Review Column Mapping →"}
              </button>
            </div>
          </div>
        )}
      </div>

      {activeFile && activeFile.preview_rows && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Detected Columns & Raw Preview</div>
              <div className="card-desc">First 5 records before standardization</div>
            </div>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  {activeFile.columns.map((col, idx) => (
                    <th key={idx}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activeFile.preview_rows.map((row, rIdx) => (
                  <tr key={rIdx}>
                    {activeFile.columns.map((col, cIdx) => (
                      <td key={cIdx}>{row[col] !== null && row[col] !== undefined ? String(row[col]) : "-"}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------------
// 3. Column Mapping Component
// ------------------------------------------------------------------
function ColumnMappingView({ results, setResults, targetColumns, activeFile, onSave, onClearUpload, isStoring, setActiveTab }) {
  const targetColNames = useMemo(() => {
    return targetColumns.map(c => c.column_name || c);
  }, [targetColumns]);

  const handleTargetChange = (index, newTarget) => {
    setResults(prev => {
      const copy = [...prev];
      copy[index] = {
        ...copy[index],
        standardized_column: newTarget,
        requires_confirmation: false,
        confidence: 1.0,
        confidence_pct: 100,
        method: "User confirmation"
      };
      return copy;
    });
  };

  const pendingCount = results.filter(r => r.requires_confirmation).length;

  if (!results || results.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <div style={{ fontSize: '36px', marginBottom: '12px' }}>📊</div>
        <div style={{ fontSize: '16px', fontWeight: 700 }}>No Active Dataset To Map</div>
        <div style={{ fontSize: '13px', color: '#64748b', marginTop: '6px' }}>Please upload a CSV or Excel file first to view and standardize column mappings.</div>
        <div style={{ marginTop: '18px' }}>
          <button 
            type="button" 
            className="btn btn-primary" 
            onClick={() => setActiveTab && setActiveTab("upload")}
          >
            <Icon name="upload" size={15} /> Upload Data File
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {pendingCount > 0 && (
        <div style={{ padding: '14px 18px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '10px', color: '#92400e', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '12px', fontSize: '13.5px' }}>
          <Icon name="alert" size={20} />
          <div>
            <strong>{pendingCount} column(s) require manual confirmation:</strong> Low-confidence mappings default to "No changes" to prevent unintended alterations. Please confirm or select the correct target column.
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Standardized Column Mapping Matrix</div>
            <div className="card-desc">Review confidence scores and classification source (Keyword/Alias, OpenRouter LLM, User confirmation)</div>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button 
              type="button"
              className="btn btn-outline"
              disabled={isStoring}
              onClick={onClearUpload}
              title="Discard current upload and clear all mappings without saving"
            >
              <Icon name="trash" size={14} /> Cancel &amp; Clear Upload
            </button>
            <button 
              type="button"
              className="btn btn-success"
              disabled={isStoring}
              onClick={onSave}
            >
              {isStoring ? "Saving to Database..." : "💾 Standardize, Validate & Save to SQLite"}
            </button>
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Input Column</th>
                <th>Sample Values</th>
                <th>Standard Target Column</th>
                <th>Confidence</th>
                <th>Classification Method</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {results.map((item, index) => {
                const isConfirmed = !item.requires_confirmation;
                const isHighConf = item.confidence >= 0.90;

                return (
                  <tr key={index}>
                    <td style={{ fontWeight: 700 }}>{item.input_column}</td>
                    <td style={{ color: '#64748b', fontSize: '12.5px' }}>
                      {item.sample_values ? item.sample_values.join(", ") : "-"}
                    </td>
                    <td>
                      <select 
                        className={`form-select ${item.requires_confirmation ? "needs-confirm" : ""}`}
                        value={item.standardized_column}
                        onChange={(e) => handleTargetChange(index, e.target.value)}
                      >
                        {targetColNames.map(col => (
                          <option key={col} value={col}>{col}</option>
                        ))}
                        <option value="skip">— Skip (No changes) —</option>
                      </select>
                    </td>
                    <td>
                      <span className={`badge ${isHighConf ? "badge-success" : item.confidence >= 0.70 ? "badge-warning" : "badge-danger"}`}>
                        {item.confidence_pct}%
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${item.method === "OpenRouter LLM" ? "badge-primary" : item.method.includes("User") ? "badge-warning" : "badge-neutral"}`}>
                        {item.method}
                      </span>
                    </td>
                    <td>
                      {item.requires_confirmation ? (
                        <span className="badge badge-warning">Needs Confirmation</span>
                      ) : (
                        <span className="badge badge-success">✓ Accepted</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Bottom Action Bar */}
        <div style={{ padding: '16px 20px', background: '#f8fafc', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderRadius: '0 0 12px 12px' }}>
          <div style={{ fontSize: '13px', color: '#64748b' }}>
            Active Dataset: <strong>{activeFile?.filename}</strong> &bull; {results.length} columns &bull; {activeFile?.total_rows} records
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button 
              type="button"
              className="btn btn-outline"
              disabled={isStoring}
              onClick={onClearUpload}
              title="Discard current upload and clear all mappings without saving"
            >
              <Icon name="trash" size={14} /> Cancel &amp; Clear Upload
            </button>
            <button 
              type="button"
              className="btn btn-success"
              disabled={isStoring}
              onClick={onSave}
            >
              {isStoring ? "Saving..." : "💾 Standardize, Validate & Save to SQLite"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// 4. MCP Tools Component
// ------------------------------------------------------------------
function MCPToolsView({ activeColumns, fetchDatabase, addToast, addActivity, setConfirmModal, editTargetRowId, setEditTargetRowId }) {
  // Check Data State
  const [checkResult, setCheckResult] = useState(null);
  const [isChecking, setIsChecking] = useState(false);

  // Get Column State
  const [selectedExtractCol, setSelectedExtractCol] = useState("");
  const [columnResult, setColumnResult] = useState(null);
  const [isExtractingCols, setIsExtractingCols] = useState(false);

  // Extract Data State
  const [extractSearch, setExtractSearch] = useState("");
  const [extractedData, setExtractedData] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractPage, setExtractPage] = useState(1);
  const extractPageSize = 10;

  // Add Row State
  const [addRowData, setAddRowData] = useState({ Customer: "", Mail: "", Contact: "", Location: "", Date: "" });
  const [isAdding, setIsAdding] = useState(false);
  const [addResult, setAddResult] = useState(null);

  // Edit Data State
  const [editRowId, setEditRowId] = useState("");
  const [loadedRow, setLoadedRow] = useState(null);
  const [editForm, setEditForm] = useState({ customer_name: "", email: "", phone_number: "", city: "", signup_date: "" });
  const [isLoadingRow, setIsLoadingRow] = useState(false);
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);
  const [editRowDiff, setEditRowDiff] = useState(null);
  const [editResult, setEditResult] = useState(null);
  const [searchCustName, setSearchCustName] = useState("");
  const [isSearchingCust, setIsSearchingCust] = useState(false);
  const [nameSearchResults, setNameSearchResults] = useState(null);

  // Delete Row State
  const [deleteRowId, setDeleteRowId] = useState("");
  const [isDeletingRow, setIsDeletingRow] = useState(false);

  // Delete Column State
  const [deleteColName, setDeleteColName] = useState("");
  const [isDeletingCol, setIsDeletingCol] = useState(false);
  const [isDeletingDups, setIsDeletingDups] = useState(false);

  const handleSearchCustomerName = async () => {
    if (!searchCustName.trim()) {
      addToast("Please enter a customer name to search", "warning");
      return;
    }
    setIsSearchingCust(true);
    setNameSearchResults(null);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/search_customers?name=${encodeURIComponent(searchCustName.trim())}`);
      const data = await resp.json();
      setIsSearchingCust(false);
      if (data.status === "search_results" && Array.isArray(data.results)) {
        setNameSearchResults(data.results);
        addToast(`Found ${data.count} record(s) matching "${searchCustName}"`, "info");
      } else if (data.status === "error") {
        setNameSearchResults([]);
        addToast(data.message || "No matching customer found", "warning");
      } else {
        setNameSearchResults([]);
        addToast("No records found", "info");
      }
    } catch (err) {
      setIsSearchingCust(false);
      addToast("Customer search error: " + err.message, "error");
    }
  };

  const handleLoadRow = async (targetId) => {
    const idToLoad = targetId || editRowId;
    if (!idToLoad) {
      addToast("Please enter a valid Row ID to load", "warning");
      return;
    }
    setIsLoadingRow(true);
    setEditRowDiff(null);
    setEditResult(null);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/get_row?row_id=${idToLoad}`);
      const data = await resp.json();
      setIsLoadingRow(false);
      if (resp.ok && data.status === "success" && data.row) {
        setLoadedRow(data.row);
        setEditRowId(idToLoad);
        setEditForm({
          customer_name: data.row.customer_name || "",
          email: data.row.email || "",
          phone_number: data.row.phone_number || "",
          city: data.row.city || "",
          signup_date: data.row.signup_date || ""
        });
        addToast(`Loaded Row #${idToLoad} for editing`, "info");
      } else {
        addToast(data.detail || `Row with ID ${idToLoad} not found`, "error");
        setLoadedRow(null);
      }
    } catch (err) {
      setIsLoadingRow(false);
      addToast("Error fetching row: " + err.message, "error");
    }
  };

  useEffect(() => {
    if (editTargetRowId) {
      setEditRowId(editTargetRowId);
      handleLoadRow(editTargetRowId);
      if (setEditTargetRowId) setEditTargetRowId(null);
    }
  }, [editTargetRowId]);

  const handleReviewEdit = async () => {
    if (!editRowId || !loadedRow) {
      addToast("Please load a row first", "warning");
      return;
    }
    setIsSubmittingEdit(true);
    setEditResult(null);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/edit_data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          row_id: parseInt(editRowId, 10),
          updates: editForm,
          confirm: false
        })
      });
      const data = await resp.json();
      setIsSubmittingEdit(false);

      if (data.status === "error") {
        addToast(data.message, "error");
        setEditRowDiff(null);
      } else if (data.status === "info") {
        addToast(data.message, "info");
        setEditRowDiff(null);
      } else if (data.status === "needs_confirmation") {
        setEditRowDiff(data);
        addToast("Validation passed! Please review and confirm changes.", "info");
      }
    } catch (err) {
      setIsSubmittingEdit(false);
      addToast("Failed to preview edit: " + err.message, "error");
    }
  };

  const handleConfirmSaveEdit = async () => {
    if (!editRowId) return;
    setIsSubmittingEdit(true);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/edit_data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          row_id: parseInt(editRowId, 10),
          updates: editForm,
          confirm: true
        })
      });
      const data = await resp.json();
      setIsSubmittingEdit(false);

      if (data.status === "success") {
        setEditResult(data);
        setEditRowDiff(null);
        setLoadedRow(data.updated_row);
        addToast(`Row #${editRowId} updated successfully!`, "success");
        addActivity(`Updated Row #${editRowId} via edit_data`, "success");
        fetchDatabase();
      } else {
        addToast(data.message || "Failed to update row", "error");
      }
    } catch (err) {
      setIsSubmittingEdit(false);
      addToast("Error saving updates: " + err.message, "error");
    }
  };

  // Tool 1: Check Data
  const runCheckData = async () => {
    setIsChecking(true);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/check_data?table=customers`);
      const data = await resp.json();
      setIsChecking(false);
      setCheckResult(data);
      addToast(`Data quality report generated (${data.data_quality_score}%)`, "success");
      addActivity(`Executed check_data tool: score is ${data.data_quality_score}%`, "info");
    } catch (err) {
      setIsChecking(false);
      addToast("Failed to run check_data: " + err.message, "error");
    }
  };

  const handleDeleteDuplicatesMCP = () => {
    const count = checkResult?.duplicate_records || 0;
    if (count === 0) return;

    setConfirmModal({
      isOpen: true,
      title: "Delete Duplicate Records",
      message: `Are you sure you want to delete ${count} duplicate record(s)? The first unique instance of each record will be preserved.`,
      onConfirm: async () => {
        setIsDeletingDups(true);
        try {
          const resp = await fetch(`${API_BASE}/api/mcp/delete_duplicates`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ table: "customers", confirm: true })
          });
          const data = await resp.json();
          setIsDeletingDups(false);
          if (data.status === "success") {
            addToast(`Successfully deleted ${data.deleted_count} duplicate record(s)!`, "success");
            addActivity(`Deleted ${data.deleted_count} duplicate record(s) via Database tool`, "success");
            runCheckData();
            fetchDatabase();
          } else {
            addToast(data.message || "Failed to delete duplicates", "error");
          }
        } catch (err) {
          setIsDeletingDups(false);
          addToast("Error deleting duplicates: " + err.message, "error");
        }
      }
    });
  };

  // Tool: get_column
  const runGetColumn = async (targetCol = selectedExtractCol) => {
    setIsExtractingCols(true);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/get_columns`);
      const data = await resp.json();
      setIsExtractingCols(false);
      setColumnResult(data);
      const colCount = data.columns?.length || 0;
      if (targetCol) {
        addToast(`Extracted schema details for column "${targetCol}" via get_column`, "success");
        addActivity(`Executed get_column Database tool for "${targetCol}"`, "info");
      } else {
        addToast(`Extracted ${colCount} column definition(s) via get_column`, "success");
        addActivity(`Executed get_column Database tool: extracted ${colCount} columns`, "info");
      }
    } catch (err) {
      setIsExtractingCols(false);
      addToast("Failed to extract columns: " + err.message, "error");
    }
  };

  // Tool: Extract Data
  const runExtractData = async (query = extractSearch) => {
    setIsExtracting(true);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/extract_data?search=${encodeURIComponent(query)}&limit=1000`);
      const data = await resp.json();
      setIsExtracting(false);
      setExtractedData(data);
      setExtractPage(1);
      addToast(`Extracted ${data.returned_count || 0} record(s)`, "info");
    } catch (err) {
      setIsExtracting(false);
      addToast("Failed to extract data: " + err.message, "error");
    }
  };

  // Tool 5: Add Row
  const handleAddRow = async (e) => {
    e.preventDefault();
    if (!addRowData.Customer && !addRowData.Mail && !addRowData.Contact) {
      addToast("Please fill in at least Customer Name or Contact info", "warning");
      return;
    }

    setIsAdding(true);
    try {
      const resp = await fetch(`${API_BASE}/api/mcp/add_row`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row: addRowData, confirm_mappings: {} })
      });
      const data = await resp.json();
      setIsAdding(false);
      setAddResult(data);

      if (data.status === "success") {
        addToast("Record standardized and inserted successfully!", "success");
        addActivity(`Manually added customer "${addRowData.Customer || 'New Record'}"`, "success");
        setAddRowData({ Customer: "", Mail: "", Contact: "", Location: "", Date: "" });
        fetchDatabase();
      } else {
        addToast(data.message || "Could not add row", "warning");
      }
    } catch (err) {
      setIsAdding(false);
      addToast("Add row error: " + err.message, "error");
    }
  };

  // Tool 6: Delete Row
  const confirmDeleteRow = () => {
    const rowId = parseInt(deleteRowId);
    if (!rowId || isNaN(rowId) || rowId <= 0) {
      addToast("Please enter a valid numeric Row ID", "warning");
      return;
    }

    setConfirmModal({
      isOpen: true,
      title: `Delete Row #${rowId}?`,
      message: `Are you sure you want to permanently delete row ID #${rowId}? This operation cannot be undone.`,
      onConfirm: async () => {
        setIsDeletingRow(true);
        try {
          const resp = await fetch(`${API_BASE}/api/mcp/delete_row`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ row_id: rowId, confirm: true })
          });
          const data = await resp.json();
          setIsDeletingRow(false);

          if (data.status === "success") {
            addToast(`Row #${rowId} deleted successfully`, "success");
            addActivity(`Deleted row #${rowId} from database`, "info");
            setDeleteRowId("");
            fetchDatabase();
          } else {
            addToast(data.message || "Failed to delete row", "error");
          }
        } catch (err) {
          setIsDeletingRow(false);
          addToast("Delete row error: " + err.message, "error");
        }
      }
    });
  };

  // Tool 7: Delete Column
  const confirmDeleteColumn = () => {
    if (!deleteColName) {
      addToast("Please select a column to delete", "warning");
      return;
    }

    setConfirmModal({
      isOpen: true,
      title: `Delete Column "${deleteColName}"?`,
      message: `Warning: This will permanently remove column "${deleteColName}" and all associated data for all records. Continue?`,
      onConfirm: async () => {
        setIsDeletingCol(true);
        try {
          const resp = await fetch(`${API_BASE}/api/mcp/delete_column`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ column_name: deleteColName, confirm: true })
          });
          const data = await resp.json();
          setIsDeletingCol(false);

          if (data.status === "success") {
            addToast(`Column "${deleteColName}" deleted successfully`, "success");
            addActivity(`Removed column "${deleteColName}" from database`, "info");
            setDeleteColName("");
            fetchDatabase();
          } else {
            addToast(data.message || "Failed to delete column", "error");
          }
        } catch (err) {
          setIsDeletingCol(false);
          addToast("Delete column error: " + err.message, "error");
        }
      }
    });
  };

  return (
    <div>
      {/* 1. check data */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <span style={{ color: '#2563eb' }}>🔍</span> 1. check data &bull; Data Quality &amp; Duplicate Check
            </div>
            <div className="card-desc">Calculates data quality score, missing values &amp; duplicates across all stored records.</div>
          </div>
          <button className="btn btn-outline" disabled={isChecking} onClick={runCheckData}>
            {isChecking ? "Checking Quality..." : "Run Quality Check"}
          </button>
        </div>
        {checkResult && (
          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', fontSize: '13px', border: '1px solid #e2e8f0', marginTop: '6px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '8px' }}>
              <div style={{ background: '#fff', padding: '10px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11.5px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Quality Score</div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#059669', marginTop: '2px' }}>{checkResult.data_quality_score}%</div>
              </div>
              <div style={{ background: '#fff', padding: '10px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11.5px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Duplicate Rows</div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: checkResult.duplicate_records > 0 ? '#d97706' : '#1e293b', marginTop: '2px' }}>{checkResult.duplicate_records}</div>
              </div>
              <div style={{ background: '#fff', padding: '10px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11.5px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Total Inspected</div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#1e293b', marginTop: '2px' }}>{checkResult.total_records} rows</div>
              </div>
            </div>
            {checkResult.duplicate_records > 0 && (
              <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                <button 
                  className="btn btn-warning"
                  onClick={handleDeleteDuplicatesMCP}
                  disabled={isDeletingDups}
                >
                  <Icon name="trash" size={14} /> {isDeletingDups ? "Cleaning Duplicates..." : `Delete ${checkResult.duplicate_records} Duplicate(s)`}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2. add data */}
      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <div>
            <div className="card-title">
              <span style={{ color: '#059669' }}>➕</span> 2. add data &bull; Manual Data Entry
            </div>
            <div className="card-desc">Add a record directly without uploading a file. Field values are standardized and validated automatically.</div>
          </div>
        </div>
        <form onSubmit={handleAddRow}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>Customer Name:</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. John Doe"
                value={addRowData.Customer}
                onChange={(e) => setAddRowData({ ...addRowData, Customer: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>Email Address:</label>
              <input 
                type="email" 
                className="form-input" 
                placeholder="e.g. john@gmail.com"
                value={addRowData.Mail}
                onChange={(e) => setAddRowData({ ...addRowData, Mail: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>Contact / Mobile:</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. 9876543210"
                value={addRowData.Contact}
                onChange={(e) => setAddRowData({ ...addRowData, Contact: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>City / Location:</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="e.g. Hyderabad"
                value={addRowData.Location}
                onChange={(e) => setAddRowData({ ...addRowData, Location: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>Signup Date:</label>
              <input 
                type="date" 
                className="form-input"
                value={addRowData.Date}
                onChange={(e) => setAddRowData({ ...addRowData, Date: e.target.value })}
              />
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '18px' }}>
            <button type="submit" className="btn btn-primary" disabled={isAdding}>
              {isAdding ? "Adding Record..." : "+ Standardize & Add Record"}
            </button>
          </div>
        </form>
      </div>

      {/* 3. edit data */}
      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <div>
            <div className="card-title">
              <span style={{ color: '#2563eb' }}>✏️</span> 3. edit data &bull; Modify Existing Row
            </div>
            <div className="card-desc">
              Search the database by customer name or select by unique Row ID, modify column values, validate data formats, review old vs new values, confirm changes, and update database.
            </div>
          </div>
        </div>

        {/* Step 1: Record Selection (By Customer Name or by Row ID) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginBottom: '16px' }}>
          {/* Option A: Search by Customer Name */}
          <div style={{ background: '#f8fafc', padding: '12px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
              🔍 Search Database by Customer Name:
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text"
                className="form-input"
                placeholder="e.g. John, Alice, Smith..."
                value={searchCustName}
                onChange={(e) => setSearchCustName(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); handleSearchCustomerName(); } }}
              />
              <button 
                type="button" 
                className="btn btn-primary"
                disabled={isSearchingCust || !searchCustName.trim()}
                onClick={handleSearchCustomerName}
              >
                {isSearchingCust ? "Searching..." : "Search"}
              </button>
            </div>
          </div>

          {/* Option B: Direct Row ID */}
          <div style={{ background: '#f8fafc', padding: '12px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
              🔢 Or Select by Row ID:
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="number"
                className="form-input"
                placeholder="Row ID (e.g. 15)"
                min="1"
                value={editRowId}
                onChange={(e) => setEditRowId(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); handleLoadRow(); } }}
              />
              <button 
                type="button" 
                className="btn btn-outline"
                disabled={isLoadingRow || !editRowId}
                onClick={() => handleLoadRow()}
              >
                {isLoadingRow ? "Loading..." : "Load Row"}
              </button>
            </div>
          </div>
        </div>

        {/* Customer Name Search Results */}
        {nameSearchResults && (
          <div style={{ background: '#eff6ff', padding: '12px 14px', borderRadius: '8px', border: '1px solid #bfdbfe', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '12.5px', fontWeight: 600, color: '#1e40af' }}>
                Search Results for "{searchCustName}" ({nameSearchResults.length} found)
              </span>
              <button 
                type="button" 
                className="btn btn-outline" 
                style={{ padding: '2px 8px', fontSize: '11px' }}
                onClick={() => setNameSearchResults(null)}
              >
                Close Results
              </button>
            </div>
            {nameSearchResults.length === 0 ? (
              <div style={{ fontSize: '12.5px', color: '#64748b', fontStyle: 'italic' }}>
                No customer records found matching "{searchCustName}".
              </div>
            ) : (
              <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {nameSearchResults.map((m) => (
                  <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff', padding: '8px 12px', borderRadius: '6px', border: '1px solid #dbeafe', fontSize: '12.5px' }}>
                    <div>
                      <strong style={{ color: '#1e3a8a' }}>#{m.id} {m.customer_name || 'Unnamed'}</strong>
                      <span style={{ color: '#64748b', marginLeft: '10px' }}>{m.email || 'No email'}</span>
                      {m.city && <span style={{ color: '#94a3b8', marginLeft: '8px' }}>({m.city})</span>}
                    </div>
                    <button 
                      type="button" 
                      className="btn btn-primary" 
                      style={{ padding: '4px 10px', fontSize: '12px' }}
                      onClick={() => {
                        setEditRowId(m.id);
                        handleLoadRow(m.id);
                      }}
                    >
                      Select & Edit
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 2: Edit Form (Visible when row is loaded) */}
        {loadedRow && (
          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', paddingBottom: '10px', borderBottom: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#334155' }}>
                Editing Record <span className="badge badge-primary">ID #{loadedRow.id}</span>
              </div>
              <button 
                type="button" 
                className="btn btn-outline" 
                style={{ padding: '3px 8px', fontSize: '11px' }}
                onClick={() => { setLoadedRow(null); setEditRowDiff(null); setEditResult(null); }}
              >
                Clear
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>
                  Customer Name:
                </label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={editForm.customer_name} 
                  onChange={(e) => setEditForm({ ...editForm, customer_name: e.target.value })} 
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>
                  Email Address:
                </label>
                <input 
                  type="email" 
                  className="form-input" 
                  value={editForm.email} 
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} 
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>
                  Phone Number:
                </label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={editForm.phone_number} 
                  onChange={(e) => setEditForm({ ...editForm, phone_number: e.target.value })} 
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>
                  City / Location:
                </label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={editForm.city} 
                  onChange={(e) => setEditForm({ ...editForm, city: e.target.value })} 
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: '#475569' }}>
                  Signup Date:
                </label>
                <input 
                  type="date" 
                  className="form-input" 
                  value={editForm.signup_date} 
                  onChange={(e) => setEditForm({ ...editForm, signup_date: e.target.value })} 
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
              <button 
                type="button" 
                className="btn btn-outline"
                disabled={isSubmittingEdit}
                onClick={handleReviewEdit}
              >
                {isSubmittingEdit ? "Validating..." : "Review Changes Diff"}
              </button>
              <button 
                type="button" 
                className="btn btn-primary"
                disabled={isSubmittingEdit}
                onClick={handleConfirmSaveEdit}
              >
                {isSubmittingEdit ? "Saving..." : "Save Changes Now →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Confirmation Preview (Existing vs New Values) */}
        {editRowDiff && (
          <div style={{ padding: '16px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '10px', marginBottom: '16px' }}>
            <div style={{ fontWeight: 700, fontSize: '14px', color: '#92400e', marginBottom: '8px' }}>
              Review & Confirm Proposed Changes (Row #{editRowId})
            </div>
            
            <pre style={{ background: '#fef3c7', padding: '12px', borderRadius: '6px', fontSize: '13px', color: '#78350f', whiteSpace: 'pre-wrap', fontFamily: 'monospace', lineHeight: 1.6 }}>
              {editRowDiff.readable_preview}
            </pre>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '14px' }}>
              <button 
                className="btn btn-outline" 
                onClick={() => setEditRowDiff(null)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                disabled={isSubmittingEdit}
                onClick={handleConfirmSaveEdit}
              >
                {isSubmittingEdit ? "Updating Database..." : "Confirm & Save Changes"}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Success Result (Readable Updated Row) */}
        {editResult && (
          <div style={{ padding: '16px', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '10px', marginTop: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#065f46', fontWeight: 700, fontSize: '14px', marginBottom: '8px' }}>
              <Icon name="check" size={16} /> Data updated successfully.
            </div>
            <pre style={{ background: '#d1fae5', padding: '12px', borderRadius: '6px', fontSize: '13px', color: '#065f46', whiteSpace: 'pre-wrap', fontFamily: 'monospace', lineHeight: 1.6 }}>
              {editResult.readable_output}
            </pre>
          </div>
        )}
      </div>

      {/* 4. extract data */}
      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <div>
            <div className="card-title">
              <span style={{ color: '#7c3aed' }}>📋</span> 4. extract data &bull; Structured Query &amp; Table View
            </div>
            <div className="card-desc">Search and filter database records. Results are formatted as a responsive table, avoiding raw JSON.</div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
          <input 
            type="text" 
            className="form-input" 
            placeholder="Search records by customer name, email, phone, city..."
            value={extractSearch}
            onChange={(e) => setExtractSearch(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") runExtractData(extractSearch); }}
          />
          <button className="btn btn-primary" disabled={isExtracting} onClick={() => runExtractData(extractSearch)}>
            {isExtracting ? "Extracting..." : "Search & Extract"}
          </button>
        </div>

        {extractedData ? (
          <div>
            <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '8px', fontWeight: 500 }}>
              Found {extractedData.total_count || 0} matching record(s) in SQLite:
            </div>
            {extractedData.records && extractedData.records.length > 0 ? (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      {extractedData.columns.map((c, i) => (
                        <th key={i}>{c.replace(/_/g, " ").toUpperCase()}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {extractedData.records
                      .slice((extractPage - 1) * extractPageSize, extractPage * extractPageSize)
                      .map((r, rIdx) => (
                        <tr key={rIdx}>
                          {extractedData.columns.map((c, cIdx) => (
                            <td key={cIdx}>
                              {c === "id" ? <strong>#{r[c]}</strong> : r[c] !== null && r[c] !== undefined ? String(r[c]) : "-"}
                            </td>
                          ))}
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
                No records found matching query "{extractSearch}".
              </div>
            )}

            {/* Pagination */}
            {extractedData.records && extractedData.records.length > extractPageSize && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px' }}>
                <span style={{ fontSize: '12.5px', color: '#64748b' }}>
                  Showing page {extractPage} of {Math.ceil(extractedData.records.length / extractPageSize)}
                </span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    className="btn btn-outline" 
                    disabled={extractPage === 1}
                    onClick={() => setExtractPage(p => Math.max(1, p - 1))}
                  >
                    Previous
                  </button>
                  <button 
                    className="btn btn-outline" 
                    disabled={extractPage >= Math.ceil(extractedData.records.length / extractPageSize)}
                    onClick={() => setExtractPage(p => p + 1)}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', fontSize: '13.5px' }}>
            Click "Search & Extract" above to query records via Database tool.
          </div>
        )}
      </div>

      {/* Tools 5, 6, 7: delete row, delete column, get column */}
      <div style={{ marginTop: '20px' }}>
        <div className="tool-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))' }}>
          {/* 5. delete row */}
          <div className="tool-card">
            <div>
              <div className="tool-header">
                <div className="tool-icon" style={{ color: '#ef4444' }}>🗑️</div>
                <div>
                  <div className="tool-name">5. delete row</div>
                  <div className="tool-desc">Safely deletes a row by unique primary ID</div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#475569' }}>
                Requires explicit confirmation before deletion to prevent accidental multiple row loss.
              </p>
            </div>
            <div className="tool-body">
              <div style={{ display: 'flex', gap: '8px' }}>
                <input 
                  type="number" 
                  className="form-input" 
                  placeholder="Row ID (e.g. 1)" 
                  min="1"
                  value={deleteRowId}
                  onChange={(e) => setDeleteRowId(e.target.value)}
                />
                <button 
                  className="btn btn-danger" 
                  disabled={isDeletingRow || !deleteRowId}
                  onClick={confirmDeleteRow}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>

          {/* 6. delete column */}
          <div className="tool-card">
            <div>
              <div className="tool-header">
                <div className="tool-icon" style={{ color: '#ef4444' }}>✂️</div>
                <div>
                  <div className="tool-name">6. delete column</div>
                  <div className="tool-desc">Permanently removes a column from schema</div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#475569' }}>
                Protected columns (`id`, `created_at`) are automatically locked against deletion.
              </p>
            </div>
            <div className="tool-body">
              <div style={{ display: 'flex', gap: '8px' }}>
                <select 
                  className="form-select" 
                  style={{ flex: 1 }}
                  value={deleteColName}
                  onChange={(e) => setDeleteColName(e.target.value)}
                >
                  <option value="">— Select Column —</option>
                  {activeColumns.filter(c => (c.column_name || c) !== "id" && (c.column_name || c) !== "created_at").map((c, i) => (
                    <option key={i} value={c.column_name || c}>{c.column_name || c}</option>
                  ))}
                </select>
                <button 
                  className="btn btn-danger" 
                  disabled={isDeletingCol || !deleteColName}
                  onClick={confirmDeleteColumn}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>

          {/* 7. get column */}
          <div className="tool-card">
            <div>
              <div className="tool-header">
                <div className="tool-icon" style={{ color: '#2563eb' }}>📐</div>
                <div>
                  <div className="tool-name">7. get column</div>
                  <div className="tool-desc">Returns database schema, data types &amp; aliases</div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#475569' }}>
                Used by database engine &amp; LLM during classification to inspect schema, data types, aliases, and sample values.
              </p>
            </div>
            <div className="tool-body">
              <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                <select 
                  className="form-select" 
                  style={{ flex: 1, fontSize: '12px' }}
                  value={selectedExtractCol}
                  onChange={(e) => setSelectedExtractCol(e.target.value)}
                >
                  <option value="">All Columns</option>
                  {activeColumns.map((c, i) => {
                    const name = c.column_name || c;
                    return <option key={i} value={name}>{name}</option>;
                  })}
                </select>
                <button 
                  className="btn btn-outline" 
                  disabled={isExtractingCols}
                  onClick={() => runGetColumn(selectedExtractCol)}
                >
                  {isExtractingCols ? "Extracting..." : "Extract Column"}
                </button>
              </div>

              {columnResult ? (
                <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', fontSize: '12px', border: '1px solid #e2e8f0' }}>
                  {selectedExtractCol ? (
                    (() => {
                      const colInfo = columnResult.columns?.find(c => c.column_name === selectedExtractCol) || { column_name: selectedExtractCol, data_type: "TEXT" };
                      return (
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <span style={{ fontWeight: 700, color: '#1e3a8a', fontSize: '13px' }}>{colInfo.column_name}</span>
                            <span className="badge badge-primary">{colInfo.data_type}</span>
                          </div>
                          {colInfo.description && (
                            <div style={{ color: '#475569', marginBottom: '6px' }}>{colInfo.description}</div>
                          )}
                          {colInfo.aliases && colInfo.aliases.length > 0 && (
                            <div style={{ marginTop: '6px' }}>
                              <strong style={{ color: '#334155' }}>Aliases ({colInfo.aliases.length}):</strong>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px', maxHeight: '70px', overflowY: 'auto' }}>
                                {colInfo.aliases.slice(0, 8).map((a, idx) => (
                                  <span key={idx} className="badge badge-neutral" style={{ fontSize: '10px' }}>{a}</span>
                                ))}
                                {colInfo.aliases.length > 8 && (
                                  <span style={{ fontSize: '10px', color: '#64748b' }}>+{colInfo.aliases.length - 8} more</span>
                                )}
                              </div>
                            </div>
                          )}
                          {colInfo.sample_values && colInfo.sample_values.length > 0 && (
                            <div style={{ marginTop: '6px', color: '#059669', fontSize: '11.5px' }}>
                              <strong>Samples:</strong> {colInfo.sample_values.join(', ')}
                            </div>
                          )}
                        </div>
                      );
                    })()
                  ) : (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 600, color: '#334155' }}>
                          Extracted {columnResult.columns?.length || 0} Columns:
                        </span>
                        <span className="badge badge-success">Live Database</span>
                      </div>
                      <div style={{ maxHeight: '150px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {columnResult.columns?.map((c, i) => (
                          <div 
                            key={i} 
                            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', background: '#fff', borderRadius: '6px', border: '1px solid #e2e8f0', cursor: 'pointer' }}
                            onClick={() => setSelectedExtractCol(c.column_name)}
                            title="Click to view details"
                          >
                            <div>
                              <strong style={{ color: '#1e40af' }}>{c.column_name}</strong>
                              <span style={{ fontSize: '11px', color: '#64748b', marginLeft: '6px' }}>({c.aliases?.length || 0} aliases)</span>
                            </div>
                            <span className="badge badge-neutral" style={{ fontSize: '10px' }}>{c.data_type}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '8px', fontSize: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontWeight: 600, marginBottom: '6px', color: '#334155' }}>Active Database Columns:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
                    {activeColumns.map((c, i) => (
                      <span key={i} className="badge badge-neutral">{c.column_name || c}</span>
                    ))}
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>
                    Click <strong>"Extract Column"</strong> above to retrieve live schema, data types &amp; aliases via the Database tool.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// 5. Database Component
// ------------------------------------------------------------------
function DatabaseView({ records, total, fetchDatabase, addToast, addActivity, setConfirmModal, onEditRow }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 8;

  const filteredRecords = useMemo(() => {
    if (!searchTerm) return records;
    const term = searchTerm.toLowerCase();
    return records.filter(r => 
      Object.values(r).some(val => val !== null && val !== undefined && String(val).toLowerCase().includes(term))
    );
  }, [records, searchTerm]);

  const pagedRecords = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, page]);

  const totalPages = Math.ceil(filteredRecords.length / pageSize) || 1;

  const handleDeleteRow = (id, name) => {
    setConfirmModal({
      isOpen: true,
      title: `Delete Record #${id}?`,
      message: `Permanently delete customer "${name || 'N/A'}" (ID #${id})?`,
      onConfirm: async () => {
        try {
          const resp = await fetch(`${API_BASE}/api/mcp/delete_row`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ row_id: id, confirm: true })
          });
          const data = await resp.json();
          if (data.status === "success") {
            addToast(`Row #${id} deleted`, "success");
            addActivity(`Deleted record #${id} from database`, "info");
            fetchDatabase();
          } else {
            addToast(data.message || "Delete failed", "error");
          }
        } catch (err) {
          addToast("Error deleting row: " + err.message, "error");
        }
      }
    });
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">
            <span>SQLite Database: <strong>customers</strong></span>
            <span className="badge badge-primary">{total} Records</span>
          </div>
          <div className="card-desc">All standardized, validated records stored in the SQLite engine</div>
        </div>
        <button className="btn btn-outline" onClick={() => fetchDatabase()}>
          <Icon name="refresh" size={14} /> Refresh Data
        </button>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
        <input 
          type="text" 
          className="form-input" 
          placeholder="Filter records by name, email, city, date..."
          value={searchTerm}
          onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
        />
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer Name</th>
              <th>Email</th>
              <th>Phone Number</th>
              <th>City</th>
              <th>Signup Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {pagedRecords.length > 0 ? (
              pagedRecords.map(r => (
                <tr key={r.id}>
                  <td style={{ fontWeight: 700, color: '#64748b' }}>#{r.id}</td>
                  <td style={{ fontWeight: 600 }}>{r.customer_name || "-"}</td>
                  <td>
                    {r.email ? (
                      <a href={`mailto:${r.email}`} style={{ color: '#2563eb', textDecoration: 'none' }}>{r.email}</a>
                    ) : "-"}
                  </td>
                  <td>{r.phone_number || "-"}</td>
                  <td>{r.city || "-"}</td>
                  <td>{r.signup_date || "-"}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button 
                      className="btn btn-outline" 
                      style={{ padding: '4px 8px', fontSize: '11px', color: '#2563eb', marginRight: '6px' }}
                      onClick={() => onEditRow && onEditRow(r.id)}
                      title="Edit this record in edit_data tool"
                    >
                      <Icon name="edit" size={12} />
                    </button>
                    <button 
                      className="btn btn-outline" 
                      style={{ padding: '4px 8px', fontSize: '11px', color: '#ef4444' }}
                      onClick={() => handleDeleteRow(r.id, r.customer_name)}
                      title="Delete row"
                    >
                      <Icon name="trash" size={12} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: '#94a3b8' }}>
                  No records found in database matching your filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
        <span style={{ fontSize: '12.5px', color: '#64748b' }}>
          Page {page} of {totalPages} &bull; {filteredRecords.length} total entries
        </span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            className="btn btn-outline" 
            disabled={page === 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
          >
            Previous
          </button>
          <button 
            className="btn btn-outline" 
            disabled={page >= totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// 6. Validation Component
// ------------------------------------------------------------------
function ValidationView({ validationReport, qualityScore, fetchHealthCheck, fetchDatabase, addToast, addActivity, setConfirmModal }) {
  const [isValidating, setIsValidating] = useState(false);
  const [isDeletingDuplicates, setIsDeletingDuplicates] = useState(false);

  const handleRefresh = async () => {
    setIsValidating(true);
    await fetchHealthCheck();
    setIsValidating(false);
    addToast("Validation report updated", "success");
  };

  const report = validationReport || {};
  const duplicateCount = report.duplicate_records || 0;

  const handleDeleteDuplicates = () => {
    if (duplicateCount === 0) {
      addToast("No duplicate records found in database", "info");
      return;
    }

    const executeDelete = async () => {
      setIsDeletingDuplicates(true);
      try {
        const resp = await fetch(`${API_BASE}/api/mcp/delete_duplicates`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ table: "customers", confirm: true })
        });
        const data = await resp.json();
        setIsDeletingDuplicates(false);
        if (data.status === "success") {
          addToast(`Successfully deleted ${data.deleted_count} duplicate record(s)!`, "success");
          if (addActivity) addActivity(`Deleted ${data.deleted_count} duplicate record(s) from database`, "success");
          await fetchHealthCheck();
          if (fetchDatabase) await fetchDatabase();
        } else {
          addToast(data.message || "Failed to delete duplicates", "error");
        }
      } catch (err) {
        setIsDeletingDuplicates(false);
        addToast("Error deleting duplicates: " + err.message, "error");
      }
    };

    if (setConfirmModal) {
      setConfirmModal({
        isOpen: true,
        title: "Delete Duplicate Records",
        message: `Are you sure you want to permanently delete ${duplicateCount} duplicate record(s)? The first unique instance of each record will be preserved.`,
        onConfirm: executeDelete
      });
    } else {
      executeDelete();
    }
  };

  return (
    <div>
      {/* Action Banner for Duplicates */}
      {duplicateCount > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '10px', marginBottom: '20px', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '24px' }}>⚠️</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '14.5px', color: '#92400e' }}>
                {duplicateCount} Duplicate Record{duplicateCount > 1 ? 's' : ''} Detected
              </div>
              <div style={{ fontSize: '13px', color: '#b45309', marginTop: '2px' }}>
                Redundant rows with identical customer details were found. You can automatically delete duplicate rows and retain only unique records.
              </div>
            </div>
          </div>
          <button 
            className="btn btn-warning" 
            disabled={isDeletingDuplicates} 
            onClick={handleDeleteDuplicates}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '9px 18px', fontWeight: 600 }}
          >
            <Icon name="trash" size={14} /> {isDeletingDuplicates ? "Cleaning Duplicates..." : "Delete Duplicates"}
          </button>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper stat-success">
            <Icon name="check" size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Overall Integrity</span>
            <span className="stat-value">{qualityScore}%</span>
            <span className="stat-subtext">Quality index score</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-warning">
            <Icon name="alert" size={24} />
          </div>
          <div className="stat-info" style={{ flex: 1 }}>
            <span className="stat-label">Duplicates</span>
            <span className="stat-value">{duplicateCount}</span>
            <span className="stat-subtext">Identical records detected</span>
          </div>
          {duplicateCount > 0 && (
            <button 
              className="btn btn-warning" 
              style={{ padding: '6px 12px', fontSize: '12px', alignSelf: 'center', display: 'flex', alignItems: 'center', gap: '5px' }}
              onClick={handleDeleteDuplicates}
              disabled={isDeletingDuplicates}
            >
              <Icon name="trash" size={12} /> {isDeletingDuplicates ? "..." : "Delete"}
            </button>
          )}
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper stat-danger">
            <Icon name="alert" size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Invalid Formats</span>
            <span className="stat-value">
              {(report.invalid_emails || 0) + (report.invalid_phones || 0) + (report.invalid_dates || 0)}
            </span>
            <span className="stat-subtext">Email, phone or date errors</span>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Comprehensive Data Quality Breakdown</div>
            <div className="card-desc">Detailed results from the MCP `check_data` & `validate_data` engines</div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              className="btn btn-warning" 
              disabled={isDeletingDuplicates || duplicateCount === 0} 
              onClick={handleDeleteDuplicates}
              title={duplicateCount === 0 ? "No duplicates found" : "Delete all duplicate records"}
            >
              <Icon name="trash" size={14} /> {isDeletingDuplicates ? "Cleaning..." : "Delete Duplicates"}
            </button>
            <button className="btn btn-outline" disabled={isValidating} onClick={handleRefresh}>
              <Icon name="refresh" size={14} /> {isValidating ? "Validating..." : "Re-run Validation"}
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '20px' }}>
          <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 600, fontSize: '13px', color: '#475569' }}>Format Verification</div>
            <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Invalid Emails:</span>
                <strong style={{ color: (report.invalid_emails || 0) > 0 ? '#ef4444' : '#10b981' }}>{report.invalid_emails || 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Invalid Phones:</span>
                <strong style={{ color: (report.invalid_phones || 0) > 0 ? '#ef4444' : '#10b981' }}>{report.invalid_phones || 0}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Invalid Dates:</span>
                <strong style={{ color: (report.invalid_dates || 0) > 0 ? '#ef4444' : '#10b981' }}>{report.invalid_dates || 0}</strong>
              </div>
            </div>
          </div>

          <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 600, fontSize: '13px', color: '#475569' }}>Completeness & Missing Values</div>
            <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px' }}>
              {report.missing_values ? (
                Object.entries(report.missing_values).map(([col, count]) => (
                  <div key={col} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Missing {col}:</span>
                    <strong>{count}</strong>
                  </div>
                ))
              ) : (
                <div>No missing values recorded.</div>
              )}
            </div>
          </div>
        </div>

        <div style={{ padding: '14px', background: '#ecfdf5', borderRadius: '8px', border: '1px solid #a7f3d0', color: '#065f46', fontSize: '13.5px' }}>
          <strong>Summary:</strong> {report.summary || "All data complies with standardized schema specifications."}
        </div>
      </div>
    </div>
  );
}

// =========================================================
// AI ASSISTANT COMPONENTS (OpenRouter LLM + MCP Tools + File Upload)
// =========================================================

function InteractiveMappingCard({ message, targetColumns = [], onConfirmIngest, onCancel }) {
  const [currentMappings, setCurrentMappings] = useState(message.mapping_results || []);
  const isPending = message.requires_mapping_confirm;

  const validTargets = useMemo(() => {
    const list = (targetColumns || []).map(c => c.column_name || c).filter(c => c !== "id" && c !== "created_at");
    return Array.from(new Set(["customer_name", "email", "phone_number", "city", "signup_date", ...list]));
  }, [targetColumns]);

  const updateMapping = (inputCol, newTarget) => {
    setCurrentMappings(prev => prev.map(m => {
      if (m.input_column === inputCol) {
        return {
          ...m,
          standardized_column: newTarget,
          requires_confirmation: false,
          method: newTarget === "skip" ? "Skipped by user" : "User confirmed"
        };
      }
      return m;
    }));
  };

  return (
    <div className="mapping-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid #e2e8f0', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '13px', color: '#1e293b' }}>
          <Icon name="file" size={16} /> {message.file_info?.filename}
          <span style={{ fontSize: '11px', background: '#e0e7ff', color: '#3730a3', padding: '2px 8px', borderRadius: '10px', fontWeight: 600 }}>
            {message.file_info?.format?.toUpperCase()}
          </span>
        </div>
        <div style={{ fontSize: '12px', color: '#64748b' }}>
          {message.file_info?.total_rows} records detected
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="mapping-table">
          <thead>
            <tr>
              <th>INPUT COLUMN</th>
              <th>STANDARDIZED TARGET COLUMN</th>
              <th>CONFIDENCE</th>
              <th>METHOD</th>
              <th>STATUS</th>
            </tr>
          </thead>
          <tbody>
            {currentMappings.map((item, idx) => (
              <tr key={idx} style={{ background: item.requires_confirmation ? '#fffbeb' : '#ffffff' }}>
                <td>
                  <strong>{item.input_column}</strong>
                  {item.sample_values && item.sample_values.length > 0 && (
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                      Sample: {item.sample_values.slice(0, 2).join(", ")}
                    </div>
                  )}
                </td>
                <td>
                  {isPending ? (
                    <select 
                      className="mapping-select"
                      value={item.standardized_column}
                      onChange={(e) => updateMapping(item.input_column, e.target.value)}
                    >
                      <option value="skip">— Skip Column —</option>
                      {validTargets.map((t, ti) => (
                        <option key={ti} value={t}>{t}</option>
                      ))}
                    </select>
                  ) : (
                    <span style={{ fontWeight: 600, color: item.standardized_column === "skip" ? '#94a3b8' : '#2563eb' }}>
                      {item.standardized_column === "skip" ? "Skipped" : item.standardized_column}
                    </span>
                  )}
                </td>
                <td>
                  <span className={`conf-badge ${item.confidence >= 0.90 ? 'conf-high' : 'conf-low'}`}>
                    {item.confidence_pct || Math.round((item.confidence || 0) * 100)}%
                  </span>
                </td>
                <td style={{ fontSize: '11.5px', color: '#475569' }}>
                  {item.method}
                </td>
                <td style={{ fontSize: '11.5px' }}>
                  {item.requires_confirmation ? (
                    <span style={{ color: '#b45309', fontWeight: 600 }}>⚠️ Needs Review</span>
                  ) : (
                    <span style={{ color: '#047857', fontWeight: 600 }}>✅ Confirmed</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isPending ? (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '14px' }}>
          <button 
            type="button"
            className="btn btn-outline" 
            style={{ fontSize: '12px', padding: '6px 14px' }}
            onClick={() => onCancel && onCancel(message.id)}
          >
            Cancel
          </button>
          <button 
            type="button"
            className="btn btn-primary" 
            style={{ fontSize: '12px', padding: '6px 16px' }}
            onClick={() => onConfirmIngest && onConfirmIngest(message.id, message.file_info, currentMappings)}
          >
            <Icon name="check" size={14} /> Confirm &amp; Ingest into Database
          </button>
        </div>
      ) : (
        <div style={{ marginTop: '10px', fontSize: '12px', color: '#047857', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Icon name="check" size={14} /> Mappings confirmed and processed
        </div>
      )}
    </div>
  );
}

function ChatInterface({ 
  messages, 
  onSendMessage, 
  onSendFile, 
  isThinking, 
  isDrawer = false, 
  onConfirmAction, 
  onCancelAction,
  onConfirmMappingIngest,
  onCancelMapping,
  targetColumns = [],
  onToast
}) {
  const [inputText, setInputText] = useState("");
  const [attachedFile, setAttachedFile] = useState(null);
  const fileInputRef = React.useRef(null);
  const messagesEndRef = React.useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";

    const lowerName = file.name.toLowerCase();
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const isValid = validExtensions.some(ext => lowerName.endsWith(ext));

    if (!isValid) {
      if (onToast) onToast("Unsupported file type. Please upload a CSV or Excel file.", "error");
      return;
    }

    setAttachedFile(file);
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if ((!inputText.trim() && !attachedFile) || isThinking) return;

    if (attachedFile) {
      const file = attachedFile;
      const prompt = inputText.trim();
      setAttachedFile(null);
      setInputText("");
      if (onSendFile) {
        onSendFile(file, prompt);
      }
      return;
    }

    const txt = inputText.trim();
    setInputText("");
    onSendMessage(txt);
  };

  const handleChipClick = (chipText) => {
    if (isThinking) return;
    onSendMessage(chipText);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Scrollable chat history */}
      <div className="chat-history-scroll">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-bubble-row ${msg.role}`}>
            {msg.role === "assistant" && (
              <div className="assistant-avatar" style={{ width: '30px', height: '30px', fontSize: '14px', flexShrink: 0 }}>
                🤖
              </div>
            )}

            <div className={`chat-bubble ${msg.role}`}>
              <div className="chat-bubble-header">
                <span style={{ color: msg.role === "user" ? '#bfdbfe' : '#64748b' }}>
                  {msg.role === "user" ? "You" : "AI Assistant"} &bull; {msg.timestamp}
                </span>

                {msg.tool_called && (
                  <span className={`tool-indicator-pill ${msg.executed ? 'success' : msg.requires_confirmation ? 'write' : ''}`}>
                    ⚡ MCP Tool: {msg.tool_called}
                  </span>
                )}
              </div>

              {/* User Attachment Tag */}
              {msg.attachment && (
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(255, 255, 255, 0.2)', padding: '3px 10px', borderRadius: '12px', fontSize: '11.5px', marginBottom: '8px', fontWeight: 500 }}>
                  <Icon name="file" size={13} />
                  <span>{msg.attachment.name}</span>
                  <span style={{ opacity: 0.85, fontSize: '11px' }}>({msg.attachment.size})</span>
                </div>
              )}

              {/* Text content */}
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.55 }}>
                {msg.content}
              </div>

              {/* Interactive Column Mapping Results Card */}
              {msg.data_type === "column_mapping" && (
                <InteractiveMappingCard 
                  message={msg}
                  targetColumns={targetColumns}
                  onConfirmIngest={onConfirmMappingIngest}
                  onCancel={onCancelMapping}
                />
              )}

              {/* Ingestion & Standardization Result Card */}
              {msg.data_type === "ingestion_result" && (
                <div style={{ marginTop: '12px', padding: '14px', background: '#ecfdf5', borderRadius: '10px', border: '1px solid #a7f3d0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#065f46', fontWeight: 700, fontSize: '13.5px', marginBottom: '8px' }}>
                    <Icon name="check" size={16} /> Successfully Ingested {msg.inserted_count} Records
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px', marginTop: '10px' }}>
                    <div style={{ background: '#ffffff', padding: '8px', borderRadius: '6px', border: '1px solid #d1fae5', textAlign: 'center' }}>
                      <div style={{ fontSize: '11px', color: '#047857' }}>Stored Records</div>
                      <strong style={{ fontSize: '15px', color: '#065f46' }}>{msg.inserted_count}</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '8px', borderRadius: '6px', border: '1px solid #d1fae5', textAlign: 'center' }}>
                      <div style={{ fontSize: '11px', color: '#047857' }}>Invalid Formats</div>
                      <strong style={{ fontSize: '15px', color: ((msg.validation_report?.invalid_emails || 0) + (msg.validation_report?.invalid_phones || 0)) > 0 ? '#b45309' : '#065f46' }}>
                        {(msg.validation_report?.invalid_emails || 0) + (msg.validation_report?.invalid_phones || 0) + (msg.validation_report?.invalid_dates || 0)}
                      </strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '8px', borderRadius: '6px', border: '1px solid #d1fae5', textAlign: 'center' }}>
                      <div style={{ fontSize: '11px', color: '#047857' }}>Target Table</div>
                      <strong style={{ fontSize: '13px', color: '#065f46' }}>customers (SQLite)</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Table Data View for extract_data */}
              {msg.data?.records && Array.isArray(msg.data.records) && msg.data.records.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                    Database Records ({msg.data.records.length}{msg.data.total_count && msg.data.total_count !== msg.data.records.length ? ` of ${msg.data.total_count}` : ''}):
                  </div>
                  <div className="chat-table-container" style={{ maxHeight: '360px', overflowY: 'auto' }}>
                    <table className="chat-table">
                      <thead>
                        <tr>
                          {(msg.data.columns || Object.keys(msg.data.records[0])).map((c, ci) => (
                            <th key={ci}>{c.replace(/_/g, " ").toUpperCase()}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.data.records.map((r, ri) => (
                          <tr key={ri}>
                            {(msg.data.columns || Object.keys(msg.data.records[0])).map((c, ci) => (
                              <td key={ci}>{r[c] !== null && r[c] !== undefined ? String(r[c]) : "—"}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Schema Data View for get_column */}
              {msg.data_type === "schema" && msg.data?.columns && Array.isArray(msg.data.columns) && (
                <div style={{ marginTop: '12px' }}>
                  <div className="chat-table-container">
                    <table className="chat-table">
                      <thead>
                        <tr>
                          <th>COLUMN</th>
                          <th>DATA TYPE</th>
                          <th>DESCRIPTION</th>
                        </tr>
                      </thead>
                      <tbody>
                        {msg.data.columns.map((c, ci) => (
                          <tr key={ci}>
                            <td><strong>{c.column_name || c}</strong></td>
                            <td><code>{c.data_type || "TEXT"}</code></td>
                            <td>{c.description || (Array.isArray(c.aliases) ? c.aliases.slice(0, 2).join(", ") : "—")}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Data Quality Report Card for check_data */}
              {msg.data_type === "quality_report" && msg.data && (
                <div style={{ marginTop: '12px', padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 600, fontSize: '13px', color: '#334155' }}>Quality Health Score</span>
                    <span style={{ fontWeight: 700, fontSize: '15px', color: (msg.data.data_quality_score || 0) >= 80 ? '#10b981' : '#f59e0b' }}>
                      {msg.data.data_quality_score || 0}%
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', fontSize: '12px', textAlign: 'center' }}>
                    <div style={{ background: '#ffffff', padding: '6px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <div style={{ color: '#64748b', fontSize: '11px' }}>Total Records</div>
                      <strong>{msg.data.total_records || 0}</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '6px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <div style={{ color: '#64748b', fontSize: '11px' }}>Duplicates</div>
                      <strong style={{ color: (msg.data.duplicate_records || 0) > 0 ? '#ef4444' : '#10b981' }}>{msg.data.duplicate_records || 0}</strong>
                    </div>
                    <div style={{ background: '#ffffff', padding: '6px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                      <div style={{ color: '#64748b', fontSize: '11px' }}>Invalid Values</div>
                      <strong style={{ color: ((msg.data.invalid_emails || 0) + (msg.data.invalid_phones || 0)) > 0 ? '#ef4444' : '#10b981' }}>
                        {(msg.data.invalid_emails || 0) + (msg.data.invalid_phones || 0) + (msg.data.invalid_dates || 0)}
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Confirmation Prompt Card */}
              {msg.requires_confirmation && (
                <div className="chat-confirm-box">
                  <div className="chat-confirm-title">
                    ⚠️ Confirmation Required Before Execution
                  </div>
                  <div style={{ fontSize: '12.5px', color: '#92400e', marginBottom: '6px' }}>
                    Review the intended changes below. The database will only be modified once you confirm:
                  </div>

                  {msg.preview && (
                    <pre className="chat-confirm-preview">
                      {JSON.stringify(msg.preview, null, 2)}
                    </pre>
                  )}

                  <div className="chat-confirm-actions">
                    <button 
                      className="btn btn-outline" 
                      style={{ fontSize: '12px', padding: '5px 12px' }}
                      onClick={() => onCancelAction && onCancelAction(msg.id)}
                    >
                      Cancel
                    </button>
                    <button 
                      className="btn btn-primary" 
                      style={{ fontSize: '12px', padding: '5px 14px' }}
                      onClick={() => onConfirmAction && onConfirmAction(msg.tool_called, msg.tool_args, msg.id)}
                    >
                      Confirm &amp; Execute
                    </button>
                  </div>
                </div>
              )}

              {/* Executed Badge */}
              {msg.executed && (
                <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px', color: '#047857', fontSize: '12px', fontWeight: 600 }}>
                  <Icon name="check" size={14} /> Database updated via MCP server
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading / Thinking Indicator */}
        {isThinking && (
          <div className="chat-bubble-row assistant">
            <div className="assistant-avatar" style={{ width: '30px', height: '30px', fontSize: '14px', flexShrink: 0 }}>
              🤖
            </div>
            <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '16px', height: '16px', border: '2px solid #e2e8f0', borderTop: '2px solid #2563eb', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }}></div>
              <span style={{ fontSize: '13px', color: '#64748b' }}>
                AI Assistant is analyzing query with OpenRouter &amp; MCP tools...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips */}
      <div className="chat-chips-bar">
        {[
          "Show me all records.",
          "Find customers from Hyderabad.",
          "How many records are in the database?",
          "Check for missing email addresses.",
          "Show me available columns.",
          "Add a new customer named Rahul from Mumbai.",
          "Delete the row with ID 20."
        ].map((chip, idx) => (
          <button 
            key={idx} 
            className="chat-chip"
            onClick={() => handleChipClick(chip)}
            disabled={isThinking}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Message Input Container with File Attachment Bar */}
      <div className="chat-input-container">
        {attachedFile && (
          <div className="chat-attachment-bar">
            <div className="chat-attachment-pill">
              <Icon name="file" size={14} />
              <span style={{ fontWeight: 600 }}>{attachedFile.name}</span>
              <span style={{ color: '#64748b', fontSize: '11px' }}>
                ({(attachedFile.size / 1024).toFixed(1)} KB)
              </span>
              <button 
                type="button" 
                className="chat-attachment-remove" 
                onClick={() => setAttachedFile(null)} 
                title="Remove attachment"
              >
                &times;
              </button>
            </div>
            <span style={{ fontSize: '11.5px', color: '#64748b' }}>
              Ready to process with AI Assistant
            </span>
          </div>
        )}

        <form className="chat-input-bar" onSubmit={handleSubmit}>
          {/* Hidden File Input */}
          <input 
            type="file" 
            ref={fileInputRef} 
            accept=".csv,.xlsx,.xls" 
            onChange={handleFileSelect} 
            style={{ display: 'none' }} 
          />

          {/* Paperclip / File Upload Icon Button */}
          <button 
            type="button" 
            className="chat-upload-btn" 
            onClick={() => fileInputRef.current?.click()} 
            title="Attach CSV or Excel file (.csv, .xlsx, .xls)"
            disabled={isThinking}
          >
            <Icon name="paperclip" size={18} />
          </button>

          <input 
            type="text" 
            className="form-input" 
            placeholder={attachedFile ? "Include an instruction (e.g. Upload and standardize, Check columns) or press Send..." : "Ask AI Assistant or attach a CSV/Excel file..."}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isThinking}
          />
          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={isThinking || (!inputText.trim() && !attachedFile)}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="send" size={15} /> Send
          </button>
        </form>
      </div>
    </div>
  );
}

// Full-Page AI Assistant View Component
function AIAssistantView({ 
  messages, 
  onSendMessage, 
  onSendFile, 
  isThinking, 
  onConfirmAction, 
  onCancelAction,
  onConfirmMappingIngest,
  onCancelMapping,
  targetColumns,
  onToast
}) {
  return (
    <div className="animate-fade">
      <div className="assistant-page-container">
        <div className="assistant-header">
          <div className="assistant-header-left">
            <div className="assistant-avatar">🤖</div>
            <div>
              <div className="assistant-title">
                AI Assistant &bull; MCP Database Controller
              </div>
              <div className="assistant-subtitle">
                Natural-language database operations &amp; file standardization powered by OpenRouter LLM &bull; Communicates with local MCP Client &amp; Server
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="server-status-pill" style={{ background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0' }}>
              <span className="status-dot"></span> OpenRouter Connected
            </span>
          </div>
        </div>

        <ChatInterface 
          messages={messages}
          onSendMessage={onSendMessage}
          onSendFile={onSendFile}
          isThinking={isThinking}
          onConfirmAction={onConfirmAction}
          onCancelAction={onCancelAction}
          onConfirmMappingIngest={onConfirmMappingIngest}
          onCancelMapping={onCancelMapping}
          targetColumns={targetColumns}
          onToast={onToast}
        />
      </div>
    </div>
  );
}

// Side-by-Side Toggleable Drawer Panel Component
function AIAssistantDrawer({ 
  isOpen, 
  onClose, 
  messages, 
  onSendMessage, 
  onSendFile, 
  isThinking, 
  onConfirmAction, 
  onCancelAction,
  onConfirmMappingIngest,
  onCancelMapping,
  targetColumns,
  onToast
}) {
  if (!isOpen) return null;

  return (
    <div className="assistant-panel-drawer">
      <div className="drawer-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="assistant-avatar" style={{ width: '30px', height: '30px', fontSize: '15px' }}>🤖</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-main)' }}>AI Assistant Column</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Side-by-side MCP controller</div>
          </div>
        </div>
        <button className="drawer-close-btn" onClick={onClose} title="Close Panel">
          <Icon name="close" size={18} />
        </button>
      </div>

      <ChatInterface 
        messages={messages}
        onSendMessage={onSendMessage}
        onSendFile={onSendFile}
        isThinking={isThinking}
        isDrawer={true}
        onConfirmAction={onConfirmAction}
        onCancelAction={onCancelAction}
        onConfirmMappingIngest={onConfirmMappingIngest}
        onCancelMapping={onCancelMapping}
        targetColumns={targetColumns}
        onToast={onToast}
      />
    </div>
  );
}

// Render React App
const rootElement = document.getElementById("root");
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);

