// src/pages/admin/Requests.jsx
import React, { useEffect, useState } from "react";
import api from "../../api";
import { useNavigate } from "react-router-dom";

export default function AdminRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null); // request id being acted on
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchRequests();
  }, []);

  async function fetchRequests() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/admin/topup-requests");
      setRequests(res.data.requests || []);
    } catch (err) {
      console.error("fetchRequests", err?.response?.status, err?.response?.data);
      setError(err.response?.data?.detail || "Failed to fetch requests");
    } finally {
      setLoading(false);
    }
  }

  async function approve(reqId) {
    if (!window.confirm("Approve this top-up request?")) return;
    setActionLoading(reqId);
    try {
      const res = await api.post(`/admin/topup-requests/${reqId}/approve`);
      alert(`Approved: credited ₹${res.data.amount}. New balance: ₹${res.data.new_balance}`);
      await fetchRequests();
    } catch (err) {
      console.error("approve", err?.response?.status, err?.response?.data);
      alert(err.response?.data?.detail || "Failed to approve");
    } finally {
      setActionLoading(null);
    }
  }

  async function reject(reqId) {
    const reason = window.prompt("Reason for rejection (optional):", "Insufficient details");
    if (reason === null) return; // cancelled
    setActionLoading(reqId);
    try {
      await api.post(`/admin/topup-requests/${reqId}/reject`, { reason });
      alert("Rejected");
      await fetchRequests();
    } catch (err) {
      console.error("reject", err?.response?.status, err?.response?.data);
      alert(err.response?.data?.detail || "Failed to reject");
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) return <div className="card">Loading requests...</div>;
  if (error) return <div className="card">Error: {error}</div>;

  return (
    <div className="card">
      <h3>Top-up requests</h3>
      {requests.length === 0 ? (
        <div>No requests</div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th>User</th>
              <th>Amount</th>
              <th>Note</th>
              <th>Status</th>
              <th>Requested at</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id} style={{ borderTop: "1px solid #eee" }}>
                <td>
                  {r.user ? (
                    <>
                      <div><strong>{r.user.name || r.user.email}</strong></div>
                      <div style={{ fontSize: 12 }}>{r.user.email}</div>
                    </>
                  ) : (
                    <div>Unknown user</div>
                  )}
                </td>
                <td>₹{(r.amount || 0).toFixed(2)}</td>
                <td>{r.note || "—"}</td>
                <td>{r.status}</td>
                <td>{r.created_at || "—"}</td>
                <td>
                  {r.status === "pending" ? (
                    <>
                      <button className="btn" disabled={actionLoading === r.id} onClick={() => approve(r.id)}>
                        {actionLoading === r.id ? "Processing..." : "Approve"}
                      </button>
                      <button style={{ marginLeft: 8 }} disabled={actionLoading === r.id} onClick={() => reject(r.id)}>
                        Reject
                      </button>
                    </>
                  ) : (
                    <div>
                      {r.status} {r.approved_by ? <div style={{ fontSize: 12 }}>By: {r.approved_by}</div> : null}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
