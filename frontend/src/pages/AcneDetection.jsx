import React, {
    useState,
    useEffect,
    useCallback,
    useRef,
    useContext,   
  } from "react";
  import Webcam from "react-webcam";
  import { Link } from "react-router-dom";
  import Navbar from "../components/Navbar";
  import ReactMarkdown from "react-markdown";
  import remarkGfm from "remark-gfm";
  import { AuthContext } from "../context/AuthContext";
  
  function AcneDetection() {
    const { user } = useContext(AuthContext); 
    const webcamRef = useRef(null);
    const [imgSrc, setImgSrc] = useState(null);
    const [processedImg, setProcessedImg] = useState(null);
    const [loading, setLoading] = useState(false);
    const [devices, setDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState(null);
    const [jerawatAnalysis, setJerawatAnalysis] = useState(null);
    const [activeTab, setActiveTab] = useState("recommendation");
    

  
    // ambil daftar kamera
    const handleDevices = useCallback(
      (mediaDevices) => {
        const videoDevices = mediaDevices.filter(
          ({ kind }) => kind === "videoinput"
        );
        setDevices(videoDevices);
        if (!selectedDeviceId && videoDevices.length > 0) {
          setSelectedDeviceId(videoDevices[0].deviceId);
        }
      },
      [selectedDeviceId]
    );
  
    useEffect(() => {
      navigator.mediaDevices
        .enumerateDevices()
        .then(handleDevices)
        .catch((err) => console.error(err));
    }, [handleDevices]);
  
    // ambil gambar dari webcam
    const capture = useCallback(() => {
      if (!webcamRef.current) return;
      const imageSrc = webcamRef.current.getScreenshot();
      if (!imageSrc) return;
      setImgSrc(imageSrc);
      sendToBackend(imageSrc, false);
    }, []);
  
    // upload gambar dari file
    const handleUpload = (e) => {
      const file = e.target.files[0];
      if (file) {
        setImgSrc(URL.createObjectURL(file));
        sendToBackend(file, true);
      }
    };


  
    // kirim gambar ke backend
    const sendToBackend = async (imageInput, fromUpload = false) => {
      setLoading(true);
      const formData = new FormData();
  
      if (fromUpload) {
        formData.append("image", imageInput);
      } else {
        const blob = await fetch(imageInput).then((res) => res.blob());
        formData.append("image", blob, "capture.jpg");
      }
  
      try {
        const response = await fetch("http://localhost:5000/predict", {
          method: "POST",
          body: formData,
          credentials: "include",
        });
  
        const data = await response.json();
        setProcessedImg(data.image_url);
        setJerawatAnalysis(data);
      } catch (error) {
        console.error("Error sending image to backend:", error);
      } finally {
        setLoading(false);
      }
    };
  

    const normalizePhone = (phone) => {
      if (!phone) return null;
      const digits = phone.replace(/\D/g, "");

      if (digits.startsWith("0")) {
        return "62" + digits.slice(1);
      }
      if (digits.startsWith("62")) {
        return digits;
      }
      if (digits.startsWith("8")) {
        return "62" + digits;
      }
      return digits;
    };


    const handleSendToWA = async () => {
      if (!jerawatAnalysis) return;

      if (!user || !user.phone) {
        alert("Nomor WhatsApp belum diisi di profil. Silakan lengkapi dulu.");
        return;
      }

      const phoneNumber = normalizePhone(user.phone);

      if (!phoneNumber) {
        alert("Format nomor HP tidak valid.");
        return;
      }

      try {
        const res = await fetch("http://localhost:5000/send-to-wa", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            phone: phoneNumber,
            result: jerawatAnalysis,
          }),
          credentials: "include",
        });

        const data = await res.json();
        console.log("Send-to-WA response:", data);

        if (data.success) {
          alert("Berhasil mengirim hasil ke WhatsApp ✅");
        } else {
          console.error("Gagal kirim WA:", data.detail || data.error);
          alert("Gagal mengirim WhatsApp. Cek log backend.");
        }
      } catch (error) {
        console.error("Error sending to WA:", error);
        alert("Terjadi error saat mengirim WhatsApp.");
      }
    };


  
    return (
      <>
        <Navbar />
  
        <main className="pt-32 pb-12 bg-slate-50 min-h-screen">
          <div className="max-w-6xl mx-auto px-4">
  
            {/* Layout: kiri tabs, kanan cards */}
            <div className="flex gap-6 items-start">
  
              {/* Kiri: tombol Detection & History */}
              <div className="flex flex-col gap-3 min-w-[150px]">
                <button
                  className="px-6 py-2 rounded-full text-sm font-medium 
                  bg-gradient-to-r from-blue-500 to-sky-400 text-white shadow-md hover:opacity-90"
                  disabled
                >
                  Detection
                </button>
  
                <Link
                  to="/history"
                  className="px-6 py-2 rounded-full text-sm font-medium 
                  border border-blue-400 text-blue-500 hover:bg-blue-50 text-center"
                >
                  History
                </Link>
              </div>
  
              
              {/* Kanan: camera card + result card */}
              <div className="flex flex-col gap-6">
                <h1 className="text-3xl md:text-[32px] font-semibold text-slate-900">
                    Acne <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-sky-400">Detection</span>
                </h1>
              <div className="flex-1 grid gap-6 lg:grid-cols-3 items-start">
                
                {/* Card Kamera (span 2 kolom) */}
                <div className="lg:col-span-2">
                  <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
                    {/* Area camera / preview */}
                    <div className="rounded-2xl overflow-hidden border border-slate-200 bg-slate-100 aspect-video flex items-center justify-center mb-6">
                      {imgSrc ? (
                        <img
                          src={imgSrc}
                          alt="Captured"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Webcam
                          audio={false}
                          ref={webcamRef}
                          screenshotFormat="image/jpeg"
                          mirrored={true}
                          videoConstraints={{
                            deviceId: selectedDeviceId
                              ? { exact: selectedDeviceId }
                              : undefined,
                          }}
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
    
                    {/* Select Camera */}
                    <div className="mb-4">
                      <label className="block text-xs md:text-sm font-medium text-slate-700 mb-1">
                        Select Camera
                      </label>
                      <select
                        className="border border-slate-300 rounded-xl px-3 py-2 bg-white text-sm w-full"
                        onChange={(e) => setSelectedDeviceId(e.target.value)}
                        value={selectedDeviceId || ""}
                      >
                        {devices.map((device, index) => (
                          <option key={device.deviceId} value={device.deviceId}>
                            {device.label || `Camera ${index + 1}`}
                          </option>
                        ))}
                      </select>
                    </div>
    
                    {/* Tombol Take Picture & Choose File */}
                    <div className="flex flex-wrap gap-4 mt-4">
                      <button
                        onClick={capture}
                        className="flex-1 min-w-[150px] px-4 py-3 rounded-full bg-gradient-to-r from-blue-500 to-sky-400 text-white text-sm font-medium shadow-md hover:opacity-90 transition"
                      >
                        Take Picture
                      </button>
    
                      <label className="flex-1 min-w-[150px]">
                        <span className="w-full inline-flex justify-center px-4 py-3 rounded-full border border-blue-400 text-blue-500 text-sm font-medium bg-white hover:bg-blue-50 cursor-pointer transition">
                          Choose File
                        </span>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleUpload}
                          className="hidden"
                        />
                      </label>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl shadow-lg border border-slate-200 mt-5 overflow-hidden">
                  
                  {/* HEADER TAB */}
                  <div className="flex border-b border-slate-200">
                    <button
                      className={`flex-1 py-4 text-sm font-semibold text-center transition-all duration-200 focus:outline-none ${
                        activeTab === "recommendation"
                          ? "text-blue-600 border-b-2 border-blue-500 bg-blue-50"
                          : "text-slate-500 hover:text-blue-500 hover:bg-slate-50"
                      }`}
                      onClick={() => setActiveTab("recommendation")}
                    >
                      AI Recommendation
                    </button>

                    <button
                      className={`flex-1 py-4 text-sm font-semibold text-center transition-all duration-200 focus:outline-none ${
                        activeTab === "summary"
                          ? "text-blue-600 border-b-2 border-blue-500 bg-blue-50"
                          : "text-slate-500 hover:text-blue-500 hover:bg-slate-50"
                      }`}
                      onClick={() => setActiveTab("summary")}
                    >
                      AI Summary
                    </button>
                  </div>

                  {/* ISI KONTEN TAB */}
                  <div className="p-6">
                    {jerawatAnalysis ? (
                      <>
                        {/* KONTEN TAB 1: RECOMMENDATION */}
                        {activeTab === "recommendation" && (
                          <div className="animate-fade-in text-sm text-slate-700 leading-relaxed prose max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {jerawatAnalysis.analisa_recommendation || "No recommendation available."}
                            </ReactMarkdown>
                          </div>
                        )}

                        {/* KONTEN TAB 2: SUMMARY */}
                        {activeTab === "summary" && (
                          <div className="animate-fade-in text-sm text-slate-700 leading-relaxed prose max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {jerawatAnalysis.analisa_summary || "No summary available."}
                            </ReactMarkdown>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="text-sm text-slate-400 text-center py-4">
                        AI recommendations & summary will appear here after detection.
                      </p>
                    )}
                  </div>

                </div>
              </div>
  
                {/* Card Hasil Deteksi */}
                <div className="bg-white rounded-2xl shadow-lg p-6 flex flex-col lg:col-span-1 border border-slate-200">
                  <h2 className="text-lg font-semibold text-blue-500 mb-4">
                    Detection Result
                  </h2> 
  
                  <div className="rounded-2xl overflow-hidden border border-slate-200 bg-slate-100 aspect-video flex items-center justify-center mb-6">
                    {loading ? (
                      <p className="text-blue-500 text-sm">
                        Processing image...
                      </p>
                    ) : processedImg ? (
                      <img
                        src={processedImg}
                        alt="Detection result"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <p className="text-slate-400 text-sm px-4 text-center">
                        No result yet. Capture or upload a photo first.
                      </p>
                    )}
                  </div>
  
                  <div className="border-t border-slate-200 pt-4">
                    <h3 className="text-lg font-semibold text-blue-500 mb-3">
                      Acne Analysis
                    </h3>
  
                    {jerawatAnalysis ? (
                      <>
                        <p className="text-sm text-slate-700">
                          <span className="font-semibold">Total Acne:</span>{" "}
                          {jerawatAnalysis.jumlah_jerawat}
                        </p>
                        <p className="text-sm text-slate-700 mt-1">
                          <span className="font-semibold">Severity Level:</span>{" "}
                          {jerawatAnalysis.tingkat_keparahan}
                        </p>

                        {/* Tambahan: Tipe Kulit */}
                        <p className="text-sm text-slate-700 mt-1">
                          <span className="font-semibold">Skin Type:</span>{" "}
                          {jerawatAnalysis.tipe_kulit || "Not detected"}
                        </p>

                        {/* Opsional: tampilkan confidence */}
                        {jerawatAnalysis.skin_confidence !== undefined && (
                          <p className="text-sm text-slate-700 mt-1">
                            <span className="font-semibold">Skin Confidence:</span>{" "}
                            {jerawatAnalysis.skin_confidence.toFixed(1)}%
                          </p>
                        )}

                        {/* <p className="text-sm text-slate-700 mt-1">
                          <span className="font-semibold">AI Recommendations:</span>{" "}
                          {jerawatAnalysis.analisa}
                        </p> */}

                        <div className="flex flex-wrap gap-3 mt-6">
                          {jerawatAnalysis.pdf_url && (
                            <a
                              href={jerawatAnalysis.pdf_url}
                              download
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex-1 min-w-[140px] inline-flex justify-center px-4 py-3 rounded-full bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition"
                            >
                              Download PDF
                            </a>
                          )}

                         <button
                          type="button"
                          onClick={handleSendToWA}
                          className="flex-1 min-w-[140px] px-4 py-3 rounded-full bg-green-500 text-white text-sm font-medium hover:bg-green-600 transition"
                        >
                          Send to WA
                        </button>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-slate-400">
                        Acne analysis will appear here after detection.
                      </p>
                    )}

                  </div>
                </div>
              </div>
              </div>
            </div>
          </div>
        </main>
      </>
    );
  }
  
  export default AcneDetection;