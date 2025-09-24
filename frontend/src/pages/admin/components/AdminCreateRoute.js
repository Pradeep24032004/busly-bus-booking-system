import React, { useState } from "react";
import api from "../../../api";

export default function AdminCreateRoute({ onCreated }) {
  const [form, setForm] = useState({ src_city: "", dst_city: "" });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      await api.post("/admin/routes", { src_city: form.src_city, dst_city: form.dst_city });
      setForm({ src_city: "", dst_city: "" });
      onCreated && onCreated();
    } catch (e) {
      setErr(e.response?.data || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <h4>Add Route</h4>
      <form onSubmit={submit}>
        <input placeholder="Source city" value={form.src_city} onChange={e => setForm({ ...form, src_city: e.target.value })} required />
        <input placeholder="Destination city" value={form.dst_city} onChange={e => setForm({ ...form, dst_city: e.target.value })} required />
        {err && <div className="error">{JSON.stringify(err)}</div>}
        <button className="btn" type="submit" disabled={loading}>{loading ? "Adding..." : "Add Route"}</button>
      </form>
    </div>
  );
}
