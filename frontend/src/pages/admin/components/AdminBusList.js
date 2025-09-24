import React from "react";
import api from "../../../api";

export default function AdminBusList({ buses = [], onDeleted, onUpdated }) {
  const remove = async (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) return;
    try {
      await api.delete(`/admin/buses/${id}`);
      onDeleted && onDeleted();
    } catch (e) {
      alert("Failed to delete bus");
    }
  };

  const openSales = async (bus) => {
    const weeks = prompt("Open sales how many weeks before start? (1 or 2)");
    if (!weeks) return;
    try {
      await api.post(`/admin/buses/${bus._id}/open-sales`, null, { params: { weeks_before: Number(weeks) } });
      alert("Sales open time updated");
      onUpdated && onUpdated();
    } catch (e) {
      alert("Failed to open sales");
    }
  };

  return (
    <div className="card">
      <h4>Existing Buses</h4>
      {buses.length === 0 && <div>No buses yet</div>}
      <ul>
        {buses.map(b => (
          <li key={b._id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
            <div>
              <div><strong>{b.name}</strong></div>
              <div>Route: {b.route_id}</div>
              <div>Start: {new Date(b.start_time).toLocaleString()}</div>
              <div>Price: ₹{b.price_per_seat}</div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button className="btn-secondary" onClick={() => openSales(b)}>Open Sales</button>
              <button className="btn-secondary" onClick={() => remove(b._id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
