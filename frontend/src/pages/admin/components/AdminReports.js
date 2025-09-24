
// AdminReports.js
import React, { useState } from "react";
import api from "../../../api";

export default function AdminReports() {
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [data, setData] = useState([]);
  const [busId, setBusId] = useState("");
  const [by, setBy] = useState("day");

  const fetchReports = async () => {
    if (!fromDate || !toDate) return alert("Select from and to dates");
    try {
      const res = await api.get("/admin/reports", {
        params: {
          from_date: fromDate,
          to_date: toDate,
          by,
          bus_id: busId || undefined
        }
      });
      setData(res.data.data || []);
    } catch (e) {
      console.error("Fetch reports error:", e.response?.data || e.message);
      alert("Failed to fetch reports");
    }
  };

  // helper to read label from doc._id which now has day/week/month/year
  const getLabel = (idObj) => {
    if (!idObj) return "";
    if (idObj.day) return idObj.day;
    if (idObj.week) return idObj.week;
    if (idObj.month) return idObj.month;
    if (idObj.year) return idObj.year;
    // fallback: stringify
    return JSON.stringify(idObj);
  };

  return (
    <div className="card">
      <h4>Revenue Reports</h4>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} />
        <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} />

        <select value={by} onChange={e => setBy(e.target.value)}>
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
          <option value="year">Year</option>
        </select>

        <input
          type="text"
          placeholder="Optional bus id"
          value={busId}
          onChange={(e) => setBusId(e.target.value)}
          style={{ minWidth: 180 }}
        />

        <button className="btn" onClick={fetchReports}>Fetch</button>
      </div>

      <div style={{ marginTop: 12 }}>
        {data.length === 0 && <div>No data</div>}
        <ul>
          {data.map((d, i) => (
            <li key={i} style={{ marginBottom: 6 }}>
              <strong>{getLabel(d._id)}</strong> — Revenue: ₹{(d.revenue || 0).toFixed(2)} — Bookings: {d.bookings || 0}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
