// src/pages/History.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import { Icon } from "@iconify/react";

export default function History() {
  const [history, setHistory] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch("http://localhost:5000/history", {
        credentials: "include", // <-- penting untuk kirim cookie session
      });

      if (!response.ok) {
        if (response.status === 401) {
          window.location.href = "/login";
        }
        return;
      }

      const data = await response.json();
      setHistory(data); 
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };


  // Pagination
  const totalPages = Math.ceil(history.length / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentData = history.slice(startIndex, startIndex + itemsPerPage);

  const handleNext = () => {
    if (currentPage < totalPages) setCurrentPage((p) => p + 1);
  };

// --- tampilkan hanya 5 angka pagination ---
const getPageNumbers = () => {
  let pages = [];

  if (totalPages <= 5) {
    pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  } else {
    if (currentPage <= 3) {
      pages = [1, 2, 3, 4, 5];
    } else if (currentPage >= totalPages - 2) {
      pages = [
        totalPages - 4,
        totalPages - 3,
        totalPages - 2,
        totalPages - 1,
        totalPages,
      ];
    } else {
      pages = [
        currentPage - 2,
        currentPage - 1,
        currentPage,
        currentPage + 1,
        currentPage + 2,
      ];
    }
  }

  return pages;
};

  return (
    <>
      <Navbar />

      <main className="pt-32 pb-16 bg-slate-50 min-h-screen">
        <div className="max-w-6xl mx-auto px-4">

          <div className="flex gap-6 items-start">
            {/* Navigasi kiri */}
            <div className="flex flex-col gap-3 min-w-[150px]">
              <Link
                to="/detection"
                className="px-6 py-2 rounded-full text-sm font-medium  
                border border-blue-400 text-blue-500 hover:bg-blue-50 text-center transition"
              >
                Detection
              </Link>

              <button
                disabled
                className="px-6 py-2 rounded-full text-sm font-medium
                bg-gradient-to-r from-blue-500 to-sky-400 text-white shadow-md"
              >
                History
              </button>
            </div>

            {/* Card Tabel */}
            <div className="flex-1">
            <h1 className="text-3xl md:text-[32px] font-semibold text-slate-900 mb-6">
                Detection <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-sky-400">History</span>
            </h1>
              <div className="bg-white shadow-lg rounded-2xl overflow-hidden">
                {/* Header tabel: Grid diubah menjadi 6 kolom agar muat untuk Recommendation */}
                <div className="grid grid-cols-6 bg-[#2B80FF] text-white font-medium text-sm py-4 px-6 gap-4">
                  <div>Date</div>
                  <div>Total Acne</div>
                  <div>Severity Level</div>
                  <div>AI Summary</div>
                  <div>AI Recommendations</div>
                  <div className="text-center">Action</div>
                </div>

                {/* Isi tabel */}
                {currentData.length > 0 ? (
                  currentData.map((row) => (
                    <div
                      key={row.id}
                      // Grid body juga diubah ke cols-6 agar sejajar dengan header
                      className="grid grid-cols-6 border-b border-slate-200 py-4 px-6 text-sm items-center bg-white hover:bg-slate-50 transition gap-4"
                    >
                      {/* 1. Waktu */}
                      <div className="text-slate-700 font-medium">{row.waktu}</div>

                      {/* 2. Jumlah Jerawat */}
                      <div className="text-slate-700 pl-2">{row.jumlah_jerawat}</div>

                      {/* 3. Tingkat Keparahan */}
                      <div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            row.tingkat_keparahan === 'High' || row.tingkat_keparahan === 'Severe' ? 'bg-red-100 text-red-600' :
                            row.tingkat_keparahan === 'Medium' || row.tingkat_keparahan === 'Moderate' ? 'bg-yellow-100 text-yellow-600' :
                            'bg-green-100 text-green-600'
                        }`}>
                            {row.tingkat_keparahan}
                        </span>
                      </div>

                      {/* 4. AI Summary (Menggunakan kunci analisa_summary dari backend) */}
                      <div className="truncate max-w-[200px] text-slate-500" title={row.analisa_summary}>
                        {row.analisa_summary || "-"}
                      </div>

                      {/* 5. AI Recommendations (Menggunakan kunci analisa_recommendation dari backend) */}
                      <div className="truncate max-w-[200px] text-slate-500" title={row.analisa_recommendation}>
                        {row.analisa_recommendation || "-"}
                      </div>

                      {/* 6. Action: Download PDF */}
                      <div className="text-center flex justify-center">
                        {row.pdf_url ? (
                            <a
                            href={row.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center justify-center w-9 h-9 rounded-full border border-blue-400 text-blue-500 hover:bg-blue-50 transition shadow-sm"
                            title="Download PDF"
                            >
                             {/* Pastikan Icon sudah diimport, atau ganti dengan text jika belum */}
                             <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"><path fill="currentColor" d="M12 16L7 11l1.41-1.41L11 12.17V4h2v8.17l2.59-2.58L17 11l-5 5zm0 2h-4v2h8v-2h-4z"/></svg>
                            </a>
                        ) : (
                            <span className="text-slate-400 text-xs">No PDF</span>
                        )}
                        </div>
                    </div>
                  ))
                ) : (
                  <div className="py-10 text-center text-slate-500 text-sm flex flex-col items-center justify-center">
                    <p>Belum ada riwayat deteksi.</p>
                  </div>
                )}

                {/* Footer: info + pagination */}
                <div className="p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-3 text-sm">
                  <span className="text-slate-600">
                    Menampilkan {currentData.length} dari {history.length}
                  </span>

                  <div className="flex gap-2">
                    {getPageNumbers().map((page) => (
                        <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`px-3 py-1 rounded-md border text-sm ${
                            currentPage === page
                            ? "bg-blue-500 text-white border-blue-500"
                            : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
                        }`}
                        >
                        {page}
                        </button>
                    ))}

                    {currentPage < totalPages && (
                        <button
                        onClick={handleNext}
                        className="px-4 py-1 rounded-md bg-white text-slate-700 border border-slate-300 hover:bg-slate-100"
                        >
                        Selanjutnya
                        </button>
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