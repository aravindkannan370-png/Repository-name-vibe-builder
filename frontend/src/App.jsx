import { useState } from "react";

function App() {
  const [prompt, setPrompt] = useState("");
  const [website, setWebsite] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [editPrompt, setEditPrompt] = useState("");
  const [editing, setEditing] = useState(false);

  // Undo / Redo
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Preview
  const [previewMode, setPreviewMode] = useState("desktop");
  const [viewMode, setViewMode] = useState("preview");

  // Copy code
  const [copied, setCopied] = useState(false);

  // Publishing
  const [publishing, setPublishing] = useState(false);
  const [publishedUrl, setPublishedUrl] = useState("");
  const [publishCopied, setPublishCopied] = useState(false);

  // --------------------------------------------------
  // Save website version
  // --------------------------------------------------

  const saveVersion = (newWebsite) => {
    if (!newWebsite) return;

    const newHistory = history.slice(
      0,
      historyIndex + 1
    );

    newHistory.push(newWebsite);

    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
    setWebsite(newWebsite);
  };

  // --------------------------------------------------
  // Generate website
  // --------------------------------------------------

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError(
        "Please describe the website you want to create."
      );
      return;
    }

    setLoading(true);
    setError("");
    setPublishedUrl("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/generate"
        ,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prompt: prompt,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Generation failed"
        );
      }

      if (!data.html) {
        throw new Error(
          "AI did not return website HTML."
        );
      }

      saveVersion(data.html);

      setViewMode("preview");

    } catch (err) {
      console.error(err);

      setError(
        err.message || "Something went wrong."
      );

    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------
  // Edit website with AI
  // --------------------------------------------------

  const handleEdit = async () => {
    if (!website) {
      setError("Generate a website first.");
      return;
    }

    if (!editPrompt.trim()) {
      setError(
        "Tell the AI what you want to change."
      );
      return;
    }

    setEditing(true);
    setError("");
    setPublishedUrl("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/edit",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            html: website,
            instruction: editPrompt,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Editing failed"
        );
      }

      if (!data.html) {
        throw new Error(
          "AI did not return updated HTML."
        );
      }

      saveVersion(data.html);

      setEditPrompt("");
      setViewMode("preview");

    } catch (err) {
      console.error(err);

      setError(
        err.message || "Something went wrong."
      );

    } finally {
      setEditing(false);
    }
  };

  // --------------------------------------------------
  // Undo
  // --------------------------------------------------

  const handleUndo = () => {
    if (historyIndex <= 0) {
      return;
    }

    const previousIndex = historyIndex - 1;

    setHistoryIndex(previousIndex);
    setWebsite(history[previousIndex]);

    setPublishedUrl("");
    setError("");
    setViewMode("preview");
  };

  // --------------------------------------------------
  // Redo
  // --------------------------------------------------

  const handleRedo = () => {
    if (historyIndex >= history.length - 1) {
      return;
    }

    const nextIndex = historyIndex + 1;

    setHistoryIndex(nextIndex);
    setWebsite(history[nextIndex]);

    setPublishedUrl("");
    setError("");
    setViewMode("preview");
  };

  // --------------------------------------------------
  // New Project
  // --------------------------------------------------

  const handleNewProject = () => {
    setPrompt("");
    setWebsite("");
    setEditPrompt("");

    setHistory([]);
    setHistoryIndex(-1);

    setError("");
    setViewMode("preview");

    setCopied(false);
    setPublishedUrl("");
    setPublishCopied(false);
  };

  // --------------------------------------------------
  // Copy HTML
  // --------------------------------------------------

  const handleCopyCode = async () => {
    if (!website) {
      setError("Generate a website first.");
      return;
    }

    try {
      await navigator.clipboard.writeText(
        website
      );

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);

    } catch (err) {
      console.error(err);

      setError(
        "Unable to copy the code."
      );
    }
  };

  // --------------------------------------------------
  // Download HTML
  // --------------------------------------------------

  const handleDownload = () => {
    if (!website) {
      setError("Generate a website first.");
      return;
    }

    const blob = new Blob(
      [website],
      {
        type: "text/html",
      }
    );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;
    link.download = "index.html";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  // --------------------------------------------------
  // Publish website
  // --------------------------------------------------

  const handlePublish = async () => {
    if (!website) {
      setError(
        "Generate a website before publishing."
      );
      return;
    }

    setPublishing(true);
    setError("");
    setPublishedUrl("");

    try {
      const response = await fetch(
      "http://127.0.0.1:8000/publish",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            html: website,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Publishing failed."
        );
      }

      if (!data.url) {
        throw new Error(
          "Publishing succeeded but no URL was returned."
        );
      }

      setPublishedUrl(data.url);

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
        "Unable to publish website."
      );

    } finally {
      setPublishing(false);
    }
  };

  // --------------------------------------------------
  // Copy published URL
  // --------------------------------------------------

  const handleCopyPublishedUrl = async () => {
    if (!publishedUrl) return;

    try {
      await navigator.clipboard.writeText(
        publishedUrl
      );

      setPublishCopied(true);

      setTimeout(() => {
        setPublishCopied(false);
      }, 2000);

    } catch (err) {
      console.error(err);

      setError(
        "Unable to copy the published URL."
      );
    }
  };

  // --------------------------------------------------
  // Preview width
  // --------------------------------------------------

  const getPreviewClass = () => {
    if (previewMode === "mobile") {
      return "w-[390px] max-w-full h-full";
    }

    if (previewMode === "tablet") {
      return "w-[768px] max-w-full h-full";
    }

    return "w-full h-full";
  };

  // --------------------------------------------------
  // Prepare generated HTML
  // --------------------------------------------------

  const preparePreviewHtml = (html) => {
    if (!html) {
      return "";
    }

    const previewScript = `
<script>
(function () {

  document.addEventListener("click", function (event) {

    const link = event.target.closest("a");

    if (!link) {
      return;
    }

    const href = link.getAttribute("href");

    if (!href) {
      event.preventDefault();
      return;
    }

    if (href.startsWith("#")) {

      event.preventDefault();

      const id = href.substring(1);

      if (!id) {

        window.scrollTo({
          top: 0,
          behavior: "smooth"
        });

        return;
      }

      const target =
        document.getElementById(id);

      if (target) {

        target.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });

      }

      return;
    }

    if (
      href === "/" ||
      href.startsWith("/") ||
      href.startsWith("./") ||
      href.startsWith("../")
    ) {

      event.preventDefault();
      return;
    }

    if (
      href.startsWith("http://") ||
      href.startsWith("https://")
    ) {

      event.preventDefault();

      window.open(
        href,
        "_blank",
        "noopener,noreferrer"
      );

      return;
    }

    if (href.startsWith("mailto:")) {

      event.preventDefault();

      window.open(
        href,
        "_blank"
      );

      return;
    }

    if (href.startsWith("tel:")) {

      event.preventDefault();

      window.open(
        href,
        "_blank"
      );

      return;
    }

    event.preventDefault();

  });

  document.addEventListener(
    "submit",
    function (event) {
      event.preventDefault();
    }
  );

})();
</script>
`;

    if (html.includes("</body>")) {
      return html.replace(
        "</body>",
        previewScript + "</body>"
      );
    }

    return html + previewScript;
  };

  // --------------------------------------------------
  // Render
  // --------------------------------------------------

  return (
    <div className="min-h-screen bg-zinc-950 text-white">

      {/* ==================================================
          NAVBAR
      ================================================== */}

      <header className="flex h-16 items-center justify-between border-b border-zinc-800 bg-zinc-950 px-6">

        <div className="flex items-center gap-3">

          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-bold text-black">
            V
          </div>

          <span className="text-lg font-semibold">
            VibeBuilder
          </span>

        </div>

        <div className="flex items-center gap-2">

          <button
            onClick={handleUndo}
            disabled={historyIndex <= 0}
            className="rounded-lg px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-30"
          >
            ↶ Undo
          </button>

          <button
            onClick={handleRedo}
            disabled={
              historyIndex >=
              history.length - 1
            }
            className="rounded-lg px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-30"
          >
            ↷ Redo
          </button>

          <button
            onClick={handleNewProject}
            className="rounded-lg px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800"
          >
            New Project
          </button>

        </div>

      </header>

      {/* ==================================================
          MAIN
      ================================================== */}

      <main className="flex h-[calc(100vh-4rem)]">

        {/* ==================================================
            LEFT PANEL
        ================================================== */}

        <section className="flex w-[40%] flex-col border-r border-zinc-800">

          <div className="flex-1 overflow-y-auto p-6">

            <div className="mb-8">

              <h1 className="text-3xl font-bold">
                Build with AI
              </h1>

              <p className="mt-2 text-zinc-400">
                Describe the website you want to create.
              </p>

            </div>

            {/* AI INFO */}

            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">

              <div className="mb-3 flex items-center gap-2">

                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white text-xs font-bold text-black">
                  AI
                </div>

                <span className="text-sm font-medium">
                  VibeBuilder AI
                </span>

              </div>

              <p className="text-sm leading-6 text-zinc-300">
                Tell me what kind of website you
                want and I'll create it for you.
              </p>

              <div className="mt-4 space-y-2 text-sm text-zinc-500">

                <p>
                  • Create a modern portfolio website
                </p>

                <p>
                  • Build a restaurant landing page
                </p>

                <p>
                  • Create an e-commerce homepage
                </p>

              </div>

            </div>

            {/* ==================================================
                EDIT WITH AI
            ================================================== */}

            {website && (

              <div className="mt-5 rounded-2xl border border-zinc-800 bg-zinc-900 p-5">

                <div className="mb-3 flex items-center gap-2">

                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500 text-xs font-bold">
                    AI
                  </div>

                  <span className="text-sm font-medium">
                    Edit with AI
                  </span>

                </div>

                <p className="mb-3 text-sm text-zinc-400">
                  Tell the AI what you want to change.
                </p>

                <textarea
                  value={editPrompt}
                  onChange={(e) =>
                    setEditPrompt(
                      e.target.value
                    )
                  }
                  placeholder="Example: Add a testimonials section..."
                  className="h-24 w-full resize-none rounded-xl border border-zinc-700 bg-zinc-950 p-3 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-zinc-500"
                />

                <button
                  onClick={handleEdit}
                  disabled={
                    editing || loading
                  }
                  className="mt-3 w-full rounded-xl bg-purple-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-purple-600 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {editing
                    ? "AI is editing..."
                    : "Apply AI Changes"}
                </button>

              </div>

            )}

          </div>

          {/* ==================================================
              GENERATE AREA
          ================================================== */}

          <div className="border-t border-zinc-800 p-5">

            <div className="rounded-2xl border border-zinc-700 bg-zinc-900 p-3">

              <textarea
                value={prompt}
                onChange={(e) =>
                  setPrompt(e.target.value)
                }
                placeholder="Describe the website you want..."
                className="h-24 w-full resize-none bg-transparent p-2 text-sm text-white outline-none placeholder:text-zinc-500"
              />

              {error && (

                <p className="px-2 py-2 text-sm text-red-400">
                  {error}
                </p>

              )}

              <div className="flex items-center justify-between pt-2">

                <span className="text-xs text-zinc-500">

                  {loading
                    ? "AI is building your website..."
                    : editing
                    ? "AI is editing your website..."
                    : publishing
                    ? "Publishing website..."
                    : "AI website generation"}

                </span>

                <button
                  onClick={handleGenerate}
                  disabled={
                    loading ||
                    editing ||
                    publishing
                  }
                  className="rounded-xl bg-white px-5 py-2 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading
                    ? "Generating..."
                    : "Generate"}
                </button>

              </div>

            </div>

          </div>

        </section>

        {/* ==================================================
            RIGHT PANEL
        ================================================== */}

        <section className="flex flex-1 flex-col bg-zinc-900">

          {/* ==================================================
              TOOLBAR
          ================================================== */}

          <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-5">

            <div className="flex items-center gap-2">

              <span className="h-2.5 w-2.5 rounded-full bg-green-500" />

              <span className="text-sm text-zinc-300">
                {viewMode === "preview"
                  ? "Live Preview"
                  : "Code Editor"}
              </span>

            </div>

            <div className="flex items-center gap-2">

              <span className="mr-2 text-xs text-zinc-500">

                {history.length > 0
                  ? `Version ${
                      historyIndex + 1
                    } / ${history.length}`
                  : "No website"}

              </span>

              {/* Preview */}

              <button
                onClick={() =>
                  setViewMode("preview")
                }
                disabled={!website}
                className={`rounded-lg px-3 py-1.5 text-xs transition ${
                  viewMode === "preview"
                    ? "bg-white text-black"
                    : "text-zinc-400 hover:bg-zinc-800"
                } disabled:cursor-not-allowed disabled:opacity-30`}
              >
                👁 Preview
              </button>

              {/* Code */}

              <button
                onClick={() =>
                  setViewMode("code")
                }
                disabled={!website}
                className={`rounded-lg px-3 py-1.5 text-xs transition ${
                  viewMode === "code"
                    ? "bg-white text-black"
                    : "text-zinc-400 hover:bg-zinc-800"
                } disabled:cursor-not-allowed disabled:opacity-30`}
              >
                {"</>"} Code
              </button>

              {/* Copy */}

              {viewMode === "code" && (

                <button
                  onClick={handleCopyCode}
                  disabled={!website}
                  className="rounded-lg bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 transition hover:bg-zinc-700 disabled:opacity-30"
                >
                  {copied
                    ? "✓ Copied"
                    : "Copy Code"}
                </button>

              )}

              {/* Download */}

              {viewMode === "code" && (

                <button
                  onClick={handleDownload}
                  disabled={!website}
                  className="rounded-lg bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 transition hover:bg-zinc-700 disabled:opacity-30"
                >
                  ↓ Download
                </button>

              )}

              {/* Publish */}

              <button
                onClick={handlePublish}
                disabled={
                  !website ||
                  publishing ||
                  loading ||
                  editing
                }
                className="rounded-lg bg-green-500 px-4 py-1.5 text-xs font-semibold text-black transition hover:bg-green-400 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {publishing
                  ? "Publishing..."
                  : "🚀 Publish"}
              </button>

            </div>

          </div>

          {/* ==================================================
              PUBLISHED WEBSITE MESSAGE
          ================================================== */}

          {publishedUrl && (

            <div className="border-b border-green-900 bg-green-950/40 px-5 py-4">

              <div className="flex items-center justify-between gap-4">

                <div className="min-w-0">

                  <div className="flex items-center gap-2">

                    <span className="text-green-400">
                      ✓
                    </span>

                    <span className="text-sm font-semibold text-green-300">
                      Website Published
                    </span>

                  </div>

                  <p className="mt-1 truncate text-xs text-zinc-400">
                    {publishedUrl}
                  </p>

                </div>

                <div className="flex shrink-0 gap-2">

                  <button
                    onClick={() =>
                      window.open(
                        publishedUrl,
                        "_blank",
                        "noopener,noreferrer"
                      )
                    }
                    className="rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-black hover:bg-zinc-200"
                  >
                    Open Website
                  </button>

                  <button
                    onClick={
                      handleCopyPublishedUrl
                    }
                    className="rounded-lg bg-zinc-800 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-700"
                  >
                    {publishCopied
                      ? "✓ Copied"
                      : "Copy URL"}
                  </button>

                </div>

              </div>

            </div>

          )}

          {/* ==================================================
              PREVIEW MODE
          ================================================== */}

          {viewMode === "preview" && (

            <>

              <div className="flex h-12 items-center justify-center gap-2 border-b border-zinc-800 bg-zinc-900">

                {/* Desktop */}

                <button
                  onClick={() =>
                    setPreviewMode("desktop")
                  }
                  className={`rounded-lg px-3 py-1.5 text-xs transition ${
                    previewMode === "desktop"
                      ? "bg-white text-black"
                      : "text-zinc-400 hover:bg-zinc-800"
                  }`}
                >
                  🖥 Desktop
                </button>

                {/* Tablet */}

                <button
                  onClick={() =>
                    setPreviewMode("tablet")
                  }
                  className={`rounded-lg px-3 py-1.5 text-xs transition ${
                    previewMode === "tablet"
                      ? "bg-white text-black"
                      : "text-zinc-400 hover:bg-zinc-800"
                  }`}
                >
                  📱 Tablet
                </button>

                {/* Mobile */}

                <button
                  onClick={() =>
                    setPreviewMode("mobile")
                  }
                  className={`rounded-lg px-3 py-1.5 text-xs transition ${
                    previewMode === "mobile"
                      ? "bg-white text-black"
                      : "text-zinc-400 hover:bg-zinc-800"
                  }`}
                >
                  📱 Mobile
                </button>

              </div>

              {/* Preview */}

              <div className="flex flex-1 justify-center overflow-auto bg-zinc-950 p-4">

                {website ? (

                  <div
                    className={`h-full overflow-hidden rounded-lg bg-white shadow-2xl transition-all duration-300 ${getPreviewClass()}`}
                  >

                    <iframe
                      key={previewMode}
                      title="Generated Website"
                      srcDoc={preparePreviewHtml(
                        website
                      )}
                      className="h-full w-full border-0"
                      sandbox="allow-scripts allow-forms allow-popups"
                    />

                  </div>

                ) : (

                  <div className="flex h-full w-full items-center justify-center">

                    <div className="text-center">

                      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-zinc-700 bg-zinc-900 text-2xl">
                        ✨
                      </div>

                      <h2 className="text-xl font-semibold">
                        Your website will appear here
                      </h2>

                      <p className="mt-2 text-sm text-zinc-500">
                        Describe your idea and click Generate.
                      </p>

                    </div>

                  </div>

                )}

              </div>

            </>

          )}

          {/* ==================================================
              CODE MODE
          ================================================== */}

          {viewMode === "code" && (

            <div className="flex flex-1 flex-col overflow-hidden bg-zinc-950">

              {!website ? (

                <div className="flex flex-1 items-center justify-center">

                  <div className="text-center">

                    <div className="mb-4 text-4xl">
                      {"</>"}
                    </div>

                    <h2 className="text-xl font-semibold">
                      No code yet
                    </h2>

                    <p className="mt-2 text-sm text-zinc-500">
                      Generate a website first.
                    </p>

                  </div>

                </div>

              ) : (

                <div className="flex flex-1 overflow-auto">

                  <pre className="min-h-full w-full overflow-auto p-6 text-sm leading-6 text-zinc-300">

                    <code>
                      {website}
                    </code>

                  </pre>

                </div>

              )}

            </div>

          )}

        </section>

      </main>

    </div>
  );
}

export default App;