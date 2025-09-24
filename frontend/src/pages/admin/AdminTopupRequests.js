// src/pages/admin/AdminTopupRequests.jsx
import React, { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";

export default function AdminTopupRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRequests();
  }, []);

  async function fetchRequests() {
    setLoading(true);
    try {
      const res = await api.get("/admin/topup-requests", { params: { status: "pending" } });
      setRequests(res.data.requests || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function approve(id) {
    try {
      await api.post(`/admin/topup-requests/${id}/approve`);
      fetchRequests();
    } catch (e) {
      alert("Failed to approve: " + (e.response?.data?.detail || e.message));
    }
  }

  async function reject(id) {
    const reason = prompt("Reason for rejection (optional):", "");
    try {
      await api.post(`/admin/topup-requests/${id}/reject`, { reason });
      fetchRequests();
    } catch (e) {
      alert("Failed to reject: " + (e.response?.data?.detail || e.message));
    }
  }

  return (
    <div className="card">
      <h3>Top-up Requests</h3>
      <button className="btn-secondary" onClick={() => navigate("/admin/dashboard")}>Back to Dashboard</button>
      <div style={{ marginTop: 12 }}>
        {loading ? <div>Loading...</div> : null}
        {requests.length === 0 ? <div>No pending requests</div> : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th>User</th>
                <th>Amount</th>
                <th>Note</th>
                <th>Requested At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.map(r => (
                <tr key={r.id}>
                  <td>{r.user ? `${r.user.name || r.user.email} (${r.user.email})` : "User not found"}</td>
                  <td>₹{r.amount.toFixed(2)}</td>
                  <td>{r.note}</td>
                  <td>{r.created_at}</td>
                  <td>
                    <button className="btn" onClick={() => approve(r.id)} style={{ marginRight: 8 }}>Approve</button>
                    <button className="btn-secondary" onClick={() => reject(r.id)}>Reject</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
