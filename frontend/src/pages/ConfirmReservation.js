
// ConfirmReservation.jsx
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api";

export default function ConfirmReservation() {
  const { reservationId } = useParams();
  const navigate = useNavigate();
  const [reservation, setReservation] = useState(null);
  const [passengers, setPassengers] = useState([]);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    const raw = localStorage.getItem(`reservation_${reservationId}`);
    if (!raw) {
      setErr("Reservation not found in local storage. Return to bus page and reserve again.");
      return;
    }
    const r = JSON.parse(raw);
    setReservation(r);
    const initial = (r.seat_numbers || []).map((s) => ({ seat_number: s, name: "", email: "", mobile: "" }));
    setPassengers(initial);
  }, [reservationId]);

  const onChange = (idx, field, value) => {
    setPassengers((prev) => {
      const c = [...prev];
      c[idx] = { ...c[idx], [field]: value };
      return c;
    });
  };

  const confirmBooking = async () => {
    setErr(null);
    if (!reservation) return;
    // basic validation
    for (let p of passengers) {
      if (!p.name || !p.mobile || !p.email) {
        setErr("Fill name, email and mobile for every passenger.");
        return;
      }
    }
    setConfirmLoading(true);
    try {
      const res = await api.post(`/reservations/confirm/${reservationId}`, {
        passengers
      });
      setSuccess(res.data.booking_id);
      localStorage.removeItem(`reservation_${reservationId}`);
      setTimeout(() => navigate("/"), 2500);
    } catch (error) {
      const status = error.response?.status;
      const data = error.response?.data;
      // 402 structured
      if (status === 402 && data?.detail) {
        const detail = data.detail;
        // expected { required: X, available: Y }
        setErr(`Insufficient balance: required ₹${detail.required.toFixed(2)}, available ₹${detail.available.toFixed(2)}. Please add funds.`);
      } else if (status === 409) {
        // conflict - seat issues
        const detail = data?.detail;
        setErr(typeof detail === "object" ? JSON.stringify(detail) : (detail || "Seat conflict"));
        // remove local reservation copy to force user to re-reserve
        localStorage.removeItem(`reservation_${reservationId}`);
      } else if (status === 400) {
        setErr(data?.detail || "Bad request - reservation invalid or expired");
        localStorage.removeItem(`reservation_${reservationId}`);
      } else {
        setErr(data?.detail || error.message || "Failed to confirm reservation");
      }
    } finally {
      setConfirmLoading(false);
    }
  };

  if (!reservation) return <div className="card">{err ? <div className="error">{err}</div> : "Loading..."}</div>;

  return (
    <div className="card">
      <h3>Confirm reservation</h3>
      <div>
        <strong>Reservation:</strong> {reservation.id || reservation._id}
      </div>
      <div>
        <strong>Bus:</strong> {reservation.bus_id}
      </div>
      <div>
        <strong>Seats:</strong> {(reservation.seat_numbers || []).join(", ")}
      </div>
      <div>
        <strong>Total:</strong> ₹{(reservation.total_price || 0).toFixed(2)}
      </div>

      <hr />

      <h4>Passenger details</h4>
      {passengers.map((p, idx) => (
        <div key={p.seat_number} className="passenger-row" style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <div style={{ width: 48, fontWeight: "bold" }}>{p.seat_number}</div>
          <input placeholder="Name" value={p.name} onChange={(e) => onChange(idx, "name", e.target.value)} />
          <input placeholder="Email" value={p.email} onChange={(e) => onChange(idx, "email", e.target.value)} />
          <input placeholder="Mobile" value={p.mobile} onChange={(e) => onChange(idx, "mobile", e.target.value)} />
        </div>
      ))}

      {err && <div className="error" style={{ marginTop: 8 }}>{err}</div>}
      {success && <div className="success" style={{ marginTop: 8 }}>Booking confirmed! Booking id: {success}</div>}

      <div className="actions" style={{ marginTop: 12 }}>
        <button className="btn" onClick={confirmBooking} disabled={confirmLoading || success}>
          {confirmLoading ? "Confirming..." : "Confirm & Pay"}
        </button>
        <button
          className="btn-secondary"
          onClick={() => {
            fetchCancel();
          }}
          style={{ marginLeft: 8 }}
        >
          Cancel reservation
        </button>
      </div>
    </div>
  );

  async function fetchCancel() {
    try {
      setLoading(true);
      await api.post(`/reservations/cancel/${reservationId}`);
      localStorage.removeItem(`reservation_${reservationId}`);
      navigate("/");
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }
}
