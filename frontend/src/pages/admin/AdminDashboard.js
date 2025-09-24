import React, { useEffect, useState } from "react";
import AdminCreateRoute from "./components/AdminCreateRoute";
import AdminRouteList from "./components/AdminRouteList";
import AdminCreateBus from "./components/AdminCreateBus";
import AdminBusList from "./components/AdminBusList";
import AdminReports from "./components/AdminReports";
import api from "../../api";

export default function AdminDashboard() {
  const [tab, setTab] = useState("routes");
  const [routes, setRoutes] = useState([]);
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/routes"); // implemented in backend changes below
      const b = await api.get("/admin/buses");
      setRoutes(r.data.routes || []);
      setBuses(b.data.buses || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div>
      <div className="card">
        <h2>Admin Dashboard</h2>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button className={`btn ${tab === "routes" ? "active" : ""}`} onClick={() => setTab("routes")}>Routes</button>
          <button className={`btn ${tab === "buses" ? "active" : ""}`} onClick={() => setTab("buses")}>Buses</button>
          <button className={`btn ${tab === "reports" ? "active" : ""}`} onClick={() => setTab("reports")}>Reports</button>
        </div>

        {loading && <div>Loading...</div>}

        {tab === "routes" && (
          <>
            <AdminCreateRoute onCreated={loadData} />
            <AdminRouteList routes={routes} onDeleted={loadData} />
          </>
        )}

        {tab === "buses" && (
          <>
            <AdminCreateBus routes={routes} onCreated={loadData} />
            <AdminBusList buses={buses} onDeleted={loadData} onUpdated={loadData} />
          </>
        )}

        {tab === "reports" && <AdminReports />}
      </div>
    </div>
  );
}
