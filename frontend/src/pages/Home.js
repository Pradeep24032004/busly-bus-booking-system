// import React, { useState } from "react";
// import api from "../api";
// import { Link } from "react-router-dom";

// export default function Home() {
//   const [src, setSrc] = useState("");
//   const [dst, setDst] = useState("");
//   const [buses, setBuses] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const [err, setErr] = useState(null);

//   const search = async (e) => {
//     e && e.preventDefault();
//     setErr(null);
//     setLoading(true);
//     try {
//       const res = await api.get("/buses/search", { params: { src, dst } });
//       setBuses(res.data.buses || []);
//     } catch (error) {
//       setErr(error.response?.data?.detail || error.message);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div>
//       <div className="card">
//         <h3>Search buses</h3>
//         <form className="row" onSubmit={search}>
//           <input placeholder="Source city" value={src} onChange={(e) => setSrc(e.target.value)} required />
//           <input placeholder="Destination city" value={dst} onChange={(e) => setDst(e.target.value)} required />
//           <button className="btn" type="submit" disabled={loading}>
//             {loading ? "Searching..." : "Search"}
//           </button>
//         </form>
//         {err && <div className="error">{JSON.stringify(err)}</div>}
//       </div>

//       <div className="card">
//         <h3>Available buses</h3>
//         {buses.length === 0 && <div>No buses found for this route.</div>}
//         <ul className="bus-list">
//           {buses.map((b) => (
//             <li key={b._id} className="bus-item">
//               <div>
//                 <strong>{b.name}</strong> — Starts: {new Date(b.start_time).toLocaleString()}
//               </div>
//               <div>Price per seat: ₹{b.price_per_seat}</div>
//               <div>
//                 <Link to={`/buses/${b._id}`} className="btn-small">View & Book</Link>
//               </div>
//             </li>
//           ))}
//         </ul>
//       </div>
//     </div>
//   );
// }
// src/pages/Home.jsx
import React, { useState, useEffect, useRef } from "react";
import api from "../api";
import { Link } from "react-router-dom";

/**
 * Simple Carousel component
 * Props:
 *   images: array of image URLs (strings)
 *   interval: ms between auto slides (default 4000)
 *   height: CSS height for carousel container (default '320px')
 */
function Carousel({ images = [], interval = 4000, height = "320px" }) {
  const [index, setIndex] = useState(0);
  const timeoutRef = useRef(null);
  const imagesToUse = images.length ? images : [
    // default placeholders (you can replace /public/images/ files)
   `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_8hzcnv8hzcnv8hzc.png`,
  `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_em5qhoem5qhoem5q.png`,
  `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_urd61murd61murd6.png`,
  `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_g7obbxg7obbxg7ob.png`,
    //  slide1,
    //   slide2,
    //   slide3,
  ];

  const resetAuto = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      goNext();
    }, interval);
  };

  useEffect(() => {
    resetAuto();
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, imagesToUse.length]);

  const goPrev = () => {
    setIndex((i) => (i - 1 + imagesToUse.length) % imagesToUse.length);
  };
  const goNext = () => {
    setIndex((i) => (i + 1) % imagesToUse.length);
  };
  const goTo = (i) => {
    setIndex(i % imagesToUse.length);
  };

  return (
    <div style={{ width: "100%", overflow: "hidden", borderRadius: 8, position: "relative" }}>
      <div
        className="carousel-viewport"
        style={{
          display: "flex",
          transition: "transform 600ms ease",
          transform: `translateX(-${index * 100}%)`,
          height,
        }}
      >
        {imagesToUse.map((src, i) => (
          <div key={i} style={{ minWidth: "100%", height, position: "relative" }}>
            <img
              src={src}
              alt={`slide-${i}`}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                display: "block",
              }}
              onError={(e) => {
                // if image missing, replace with data URI placeholder
                e.target.onerror = null;
                e.target.src =
                  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='600'%3E%3Crect width='100%25' height='100%25' fill='%23ECEFF1'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='28' fill='%23949AA0'%3EImage not found%3C/text%3E%3C/svg%3E";
              }}
            />
          </div>
        ))}
      </div>

      {/* Prev/Next controls */}
      <button
        aria-label="Previous slide"
        onClick={() => { goPrev(); resetAuto(); }}
        style={{
          position: "absolute",
          left: 8,
          top: "50%",
          transform: "translateY(-50%)",
          background: "rgba(0,0,0,0.4)",
          border: "none",
          color: "#fff",
          padding: "8px 10px",
          borderRadius: 6,
          cursor: "pointer",
        }}
      >
        ‹
      </button>
      <button
        aria-label="Next slide"
        onClick={() => { goNext(); resetAuto(); }}
        style={{
          position: "absolute",
          right: 8,
          top: "50%",
          transform: "translateY(-50%)",
          background: "rgba(0,0,0,0.4)",
          border: "none",
          color: "#fff",
          padding: "8px 10px",
          borderRadius: 6,
          cursor: "pointer",
        }}
      >
        ›
      </button>

      {/* Dots */}
      <div
        style={{
          position: "absolute",
          bottom: 8,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 8,
        }}
      >
        {imagesToUse.map((_, i) => (
          <button
            key={i}
            aria-label={`Go to slide ${i + 1}`}
            onClick={() => { goTo(i); resetAuto(); }}
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              border: "none",
              background: i === index ? "rgba(255,255,255,0.94)" : "rgba(255,255,255,0.5)",
              cursor: "pointer",
              padding: 0,
            }}
          />
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const [src, setSrc] = useState("");
  const [dst, setDst] = useState("");
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  // Optional: provide carousel images here (you can also use default public images)
  const carouselImages = [
    `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_8hzcnv8hzcnv8hzc.png`,
  `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_em5qhoem5qhoem5q.png`,
  `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_urd61murd61murd6.png`,
  `${process.env.PUBLIC_URL}/images/Gemini_Generated_Image_g7obbxg7obbxg7ob.png`,
  ];

  const search = async (e) => {
    e && e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await api.get("/buses/search", { params: { src, dst } });
      setBuses(res.data.buses || []);
    } catch (error) {
      setErr(error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Carousel - full width card */}
      <div className="card" style={{ padding: 0 }}>
        <Carousel images={carouselImages} interval={4000} height="360px" />
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3>Search buses</h3>
        <form className="row" onSubmit={search} style={{ gap: 8, alignItems: "center" }}>
          <input placeholder="Source city" value={src} onChange={(e) => setSrc(e.target.value)} required />
          <input placeholder="Destination city" value={dst} onChange={(e) => setDst(e.target.value)} required />
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
        {err && <div className="error" style={{ marginTop: 8 }}>{JSON.stringify(err)}</div>}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3>Available buses</h3>
        {buses.length === 0 && <div>No buses found for this route.</div>}
        <ul className="bus-list" style={{ listStyle: "none", padding: 0 }}>
          {buses.map((b) => (
            <li key={b._id} className="bus-item" style={{ padding: 12, borderBottom: "1px solid #eee", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 600 }}>{b.name}</div>
                <div style={{ fontSize: 13, color: "#666" }}>Starts: {b.start_time ? new Date(b.start_time).toLocaleString() : "TBD"}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div>Price per seat: <strong>₹{b.price_per_seat}</strong></div>
                <div style={{ marginTop: 8 }}>
                  <Link to={`/buses/${b._id}`} className="btn-small">View & Book</Link>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
