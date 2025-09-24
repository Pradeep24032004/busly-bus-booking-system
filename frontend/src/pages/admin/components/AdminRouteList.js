import React from "react";
import api from "../../../api";

export default function AdminRouteList({ routes = [], onDeleted }) {
  const remove = async (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) return;
    try {
      await api.delete(`/admin/routes/${id}`);
      onDeleted && onDeleted();
    } catch (e) {
      alert("Failed to delete route");
    }
  };

  return (
    <div className="card">
      <h4>Existing Routes</h4>
      {routes.length === 0 && <div>No routes yet</div>}
      <ul>
        {routes.map(r => (
          <li key={r._id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
            <div>{r.src_city} → {r.dst_city}</div>
            <div>
              <button className="btn-secondary" onClick={() => remove(r._id)}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
