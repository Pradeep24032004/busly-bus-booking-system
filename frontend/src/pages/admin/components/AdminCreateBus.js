import React, { useState } from "react";
import api from "../../../api";

export default function AdminCreateBus({ routes = [], onCreated }) {
  const [form, setForm] = useState({
    route_id: routes[0]?._id || "",
    name: "",
    start_time: "",
    seats_count: 20,
    price_per_seat: 200,
    sales_open_time: ""
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  // when routes change, ensure route_id updated
  React.useEffect(() => {
    if (routes.length && !form.route_id) setForm(s => ({ ...s, route_id: routes[0]._id }));
  }, [routes]);

  const submit = async (e) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const payload = {
        route_id: form.route_id,
        name: form.name,
        start_time: new Date(form.start_time).toISOString(),
        seats_count: Number(form.seats_count),
        price_per_seat: Number(form.price_per_seat),
        sales_open_time: form.sales_open_time ? new Date(form.sales_open_time).toISOString() : undefined,
        status: "published"
      };
      await api.post("/admin/buses", payload);
      setForm({ route_id: routes[0]?._id || "", name: "", start_time: "", seats_count: 20, price_per_seat: 200, sales_open_time: "" });
      onCreated && onCreated();
    } catch (e) {
      setErr(e.response?.data || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <h4>Add Bus</h4>
      <form onSubmit={submit}>
        <select value={form.route_id} onChange={e => setForm({ ...form, route_id: e.target.value })} required>
          <option value="">Select route</option>
          {routes.map(r => <option key={r._id} value={r._id}>{r.src_city} → {r.dst_city}</option>)}
        </select>
        <input placeholder="Bus name/code" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
        <label>Start time (UTC)</label>
        <input type="datetime-local" value={form.start_time} onChange={e => setForm({ ...form, start_time: e.target.value })} required />
        <input placeholder="Seats count" type="number" value={form.seats_count} onChange={e => setForm({ ...form, seats_count: e.target.value })} required />
        <input placeholder="Price per seat" type="number" value={form.price_per_seat} onChange={e => setForm({ ...form, price_per_seat: e.target.value })} required />
        <label>Optional: sales open time (datetime-local)</label>
        <input type="datetime-local" value={form.sales_open_time} onChange={e => setForm({ ...form, sales_open_time: e.target.value })} />
        {err && <div className="error">{JSON.stringify(err)}</div>}
        <button className="btn" type="submit" disabled={loading}>{loading ? "Creating..." : "Create Bus"}</button>
      </form>
    </div>
  );
}
