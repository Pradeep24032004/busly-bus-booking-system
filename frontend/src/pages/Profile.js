
// // src/pages/Profile.jsx
// import React, { useEffect, useState, useContext } from "react";
// import api from "../api";
// import { AuthContext } from "../contexts/AuthContext";

// function formatDateIso(iso) {
//   if (!iso) return "unknown";
//   try {
//     const d = new Date(iso);
//     if (isNaN(d.getTime())) return iso;
//     return d.toLocaleString(); // uses user's locale; change if you want fixed format
//   } catch {
//     return iso;
//   }
// }

// export default function Profile() {
//   const { user: authUser, loadingMe } = useContext(AuthContext);

//   const [profile, setProfile] = useState(authUser ?? null);
//   const [bookings, setBookings] = useState([]);
//   const [amount, setAmount] = useState("");
//   const [note, setNote] = useState("");
//   const [loading, setLoading] = useState(false);
//   const [reqMsg, setReqMsg] = useState(null);
//   const [pwMsg, setPwMsg] = useState(null);
//   const [oldPw, setOldPw] = useState("");
//   const [newPw, setNewPw] = useState("");

//   // keep profile in sync if authUser later hydrates
//   useEffect(() => {
//     if (authUser) setProfile(authUser);
//   }, [authUser]);

//   useEffect(() => {
//     // fetch bookings once (bookings endpoint requires valid token)
//     fetchBookings();
//   }, []);

//   async function fetchBookings() {
//     try {
//       const res = await api.get("/users/me/bookings");
//       setBookings(res.data.bookings || []);
//     } catch (e) {
//       console.error("fetchBookings", e?.response?.status, e?.response?.data);
//       setBookings([]);
//     }
//   }

//   async function submitRequest(e) {
//     e.preventDefault();
//     setReqMsg(null);
//     const amt = parseFloat(amount);
//     if (Number.isNaN(amt) || amt <= 0) {
//       setReqMsg("Enter a valid amount");
//       return;
//     }
//     setLoading(true);
//     try {
//       const res = await api.post("/users/request-topup", { amount: amt, note });
//       setReqMsg(`Request submitted (id ${res.data.id}). Waiting for admin approval.`);
//       setAmount("");
//       setNote("");
//     } catch (err) {
//       console.error("request-topup", err?.response?.status, err?.response?.data);
//       setReqMsg(err.response?.data?.detail || "Failed to submit request");
//     } finally {
//       setLoading(false);
//     }
//   }

//   async function submitChangePassword(e) {
//     e.preventDefault();
//     setPwMsg(null);
//     if (!oldPw || !newPw || newPw.length < 6) {
//       setPwMsg("Provide valid old and new password (min 6 chars)");
//       return;
//     }
//     setLoading(true);
//     try {
//       const res = await api.post("/users/change-password", { old_password: oldPw, new_password: newPw });
//       setPwMsg(res.data?.message || "Password changed");
//       setOldPw("");
//       setNewPw("");
//     } catch (err) {
//       console.error("change-password", err?.response?.status, err?.response?.data);
//       setPwMsg(err.response?.data?.detail || "Failed to change password");
//     } finally {
//       setLoading(false);
//     }
//   }

//   if (loadingMe && !profile) return <div className="card">Loading profile...</div>;
//   if (!profile) return <div className="card"><h3>Profile</h3><div>Please sign in to view your profile.</div></div>;

//   return (
//     <div className="card">
//       <h3>Profile</h3>
//       <div><strong>Name:</strong> {profile.name || profile.email}</div>
//       <div><strong>Email:</strong> {profile.email}</div>
//       <div><strong>Mobile:</strong> {profile.mobile || "—"}</div>
//       <div><strong>Role:</strong> {profile.role || "user"}</div>
//       <div><strong>Balance:</strong> ₹{(profile.balance ?? 0).toFixed(2)}</div>

//       <hr />

//       <h4>Request Top-up</h4>
//       <form onSubmit={submitRequest} style={{ display: "flex", gap: 8, alignItems: "center" }}>
//         <input placeholder="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" style={{ width: 120 }} />
//         <input placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
//         <button className="btn" type="submit" disabled={loading}>{loading ? "Submitting..." : "Request"}</button>
//       </form>
//       {reqMsg && <div style={{ marginTop: 8 }}>{reqMsg}</div>}

//       <hr />

//       <h4>Change password</h4>
//       <form onSubmit={submitChangePassword} style={{ display: "flex", gap: 8, alignItems: "center" }}>
//         <input type="password" placeholder="Old password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} />
//         <input type="password" placeholder="New password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
//         <button className="btn" type="submit" disabled={loading}>Change</button>
//       </form>
//       {pwMsg && <div style={{ marginTop: 8 }}>{pwMsg}</div>}

//       <hr />

//       <h4>Past Bookings</h4>
//       {bookings.length === 0 ? (
//         <div>No bookings</div>
//       ) : (
//         <div style={{ display: "grid", gap: 12 }}>
//           {bookings.map((b) => {
//             const routeStr = b.route ? `${b.route.src || ""} → ${b.route.dst || ""}` : null;
//             const startStr = b.bus_start_time ? formatDateIso(b.bus_start_time) : "TBD";
//             const createdStr = b.created_at ? formatDateIso(b.created_at) : "unknown";
//             const seatsStr = Array.isArray(b.seats) && b.seats.length ? b.seats.join(", ") : (b.seats || "—");

//             return (
//               <div key={b.id} style={{ border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
//                 <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
//                   <div><strong>Booking:</strong> {b.id}</div>
//                   <div style={{ fontSize: 14, color: "#666" }}>{createdStr}</div>
//                 </div>

//                 <div style={{ marginBottom: 6 }}>
//                   <strong>Route:</strong> {routeStr || "Unknown route"} &nbsp; {b.bus_id ? <span style={{ color: "#666" }}>({b.bus_id})</span> : null}
//                 </div>

//                 <div style={{ marginBottom: 6 }}>
//                   <strong>Start time:</strong> {startStr}
//                 </div>

//                 <div style={{ marginBottom: 6 }}>
//                   <strong>Seat no:</strong> {seatsStr}
//                 </div>

//                 <div style={{ marginBottom: 6 }}>
//                   <strong>Passengers:</strong>
//                   {b.passengers && b.passengers.length ? (
//                     <ul style={{ marginTop: 6 }}>
//                       {b.passengers.map((p, idx) => (
//                         <li key={idx} style={{ fontSize: 14 }}>
//                           <strong>{p.name || "Passenger"}</strong>
//                           {p.seat_number ? ` — seat ${p.seat_number}` : ""}
//                           {p.email ? ` • ${p.email}` : ""}
//                           {p.mobile ? ` • ${p.mobile}` : ""}
//                         </li>
//                       ))}
//                     </ul>
//                   ) : (
//                     <div style={{ marginTop: 6 }}>No passenger details</div>
//                   )}
//                 </div>

//                 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
//                   <div><strong>Total:</strong> ₹{(b.total_price ?? 0).toFixed(2)}</div>
//                   <div style={{ fontSize: 13, color: "#333" }}><strong>Status:</strong> {b.status || "—"}</div>
//                 </div>
//               </div>
//             );
//           })}
//         </div>
//       )}
//     </div>
//   );
// }
// src/pages/Profile.jsx
import React, { useEffect, useState, useContext } from "react";
import api from "../api";
import { AuthContext } from "../contexts/AuthContext";

function formatDateIso(iso) {
  if (!iso) return "unknown";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

export default function Profile() {
  const { user: authUser, loadingMe } = useContext(AuthContext);

  const [profile, setProfile] = useState(authUser ?? null);
  const [bookings, setBookings] = useState([]);
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [reqMsg, setReqMsg] = useState(null);
  const [pwMsg, setPwMsg] = useState(null);
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    if (authUser) setProfile(authUser);
  }, [authUser]);

  useEffect(() => {
    fetchBookings();
  }, []);

  async function fetchBookings() {
    try {
      const res = await api.get("/users/me/bookings");
      setBookings(res.data.bookings || []);
    } catch (e) {
      console.error("fetchBookings", e?.response?.status, e?.response?.data);
      setBookings([]);
    }
  }

  async function submitRequest(e) {
    e.preventDefault();
    setReqMsg(null);
    const amt = parseFloat(amount);
    if (Number.isNaN(amt) || amt <= 0) {
      setReqMsg("Enter a valid amount");
      return;
    }
    setLoading(true);
    try {
      const res = await api.post("/users/request-topup", { amount: amt, note });
      setReqMsg(`Request submitted (id ${res.data.id}). Waiting for admin approval.`);
      setAmount("");
      setNote("");
    } catch (err) {
      console.error("request-topup", err?.response?.status, err?.response?.data);
      setReqMsg(err.response?.data?.detail || "Failed to submit request");
    } finally {
      setLoading(false);
    }
  }

  async function submitChangePassword(e) {
    e.preventDefault();
    setPwMsg(null);
    if (!oldPw || !newPw || newPw.length < 6) {
      setPwMsg("Provide valid old and new password (min 6 chars)");
      return;
    }
    setLoading(true);
    try {
      const res = await api.post("/users/change-password", { old_password: oldPw, new_password: newPw });
      setPwMsg(res.data?.message || "Password changed");
      setOldPw("");
      setNewPw("");
    } catch (err) {
      console.error("change-password", err?.response?.status, err?.response?.data);
      setPwMsg(err.response?.data?.detail || "Failed to change password");
    } finally {
      setLoading(false);
    }
  }

  async function cancelBooking(bookingId) {
    if (!window.confirm("Cancel this booking and get a refund?")) return;
    setActionLoading(bookingId);
    try {
      const res = await api.post(`/users/bookings/${bookingId}/cancel`);
      alert(`Booking cancelled. Refunded ₹${res.data.refunded}. New balance: ₹${res.data.new_balance.toFixed(2)}`);
      const me = await api.get("/users/me");
      setProfile(me.data);
      await fetchBookings();
    } catch (err) {
      console.error("cancelBooking", err?.response?.status, err?.response?.data);
      alert(err?.response?.data?.detail || "Failed to cancel booking");
    } finally {
      setActionLoading(null);
    }
  }

  if (loadingMe && !profile) return <div className="card">Loading profile...</div>;
  if (!profile) return <div className="card"><h3>Profile</h3><div>Please sign in to view your profile.</div></div>;

  return (
    <div className="card">
      <h3>Profile</h3>
      <div><strong>Name:</strong> {profile.name || profile.email}</div>
      <div><strong>Email:</strong> {profile.email}</div>
      <div><strong>Mobile:</strong> {profile.mobile || "—"}</div>
      <div><strong>Role:</strong> {profile.role || "user"}</div>
      <div><strong>Balance:</strong> ₹{(profile.balance ?? 0).toFixed(2)}</div>

      <hr />

      <h4>Request Top-up</h4>
      <form onSubmit={submitRequest} style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input placeholder="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" style={{ width: 120 }} />
        <input placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
        <button className="btn" type="submit" disabled={loading}>{loading ? "Submitting..." : "Request"}</button>
      </form>
      {reqMsg && <div style={{ marginTop: 8 }}>{reqMsg}</div>}

      <hr />

      <h4>Change password</h4>
      <form onSubmit={submitChangePassword} style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input type="password" placeholder="Old password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} />
        <input type="password" placeholder="New password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
        <button className="btn" type="submit" disabled={loading}>Change</button>
      </form>
      {pwMsg && <div style={{ marginTop: 8 }}>{pwMsg}</div>}

      <hr />

      <h4>Past Bookings</h4>
      {bookings.length === 0 ? (
        <div>No bookings</div>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {bookings.map((b) => {
            const routeStr = b.route ? `${b.route.src || ""} → ${b.route.dst || ""}` : null;
            const startStr = b.bus_start_time ? formatDateIso(b.bus_start_time) : "TBD";
            const createdStr = b.created_at ? formatDateIso(b.created_at) : "unknown";
            const seatsStr = Array.isArray(b.seats) && b.seats.length ? b.seats.join(", ") : (b.seats || "—");
            const isCancellable = b.status && b.status !== "cancelled";

            return (
              <div key={b.id} style={{ border: "1px solid #eee", padding: 12, borderRadius: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <div><strong>Booking:</strong> {b.id}</div>
                  <div style={{ fontSize: 14, color: "#666" }}>{createdStr}</div>
                </div>

                <div style={{ marginBottom: 6 }}>
                  <strong>Route:</strong> {routeStr || "Unknown route"} &nbsp; {b.bus_id ? <span style={{ color: "#666" }}>({b.bus_id})</span> : null}
                </div>

                <div style={{ marginBottom: 6 }}>
                  <strong>Start time:</strong> {startStr}
                </div>

                <div style={{ marginBottom: 6 }}>
                  <strong>Seat Number:</strong> {seatsStr}
                </div>

                <div style={{ marginBottom: 6 }}>
                  <strong>Passengers:</strong>
                  {b.passengers && b.passengers.length ? (
                    <ul style={{ marginTop: 6 }}>
                      {b.passengers.map((p, idx) => (
                        <li key={idx} style={{ fontSize: 14 }}>
                          <strong>{p.name || "Passenger"}</strong>
                          {p.seat_number ? ` — seat ${p.seat_number}` : ""}
                          {p.email ? ` • ${p.email}` : ""}
                          {p.mobile ? ` • ${p.mobile}` : ""}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div style={{ marginTop: 6 }}>No passenger details</div>
                  )}
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div><strong>Total:</strong> ₹{(b.total_price ?? 0).toFixed(2)}</div>
                  <div style={{ fontSize: 13, color: "#333" }}><strong>Status:</strong> {b.status || "—"}</div>
                </div>

                {isCancellable && (
                  <div style={{ marginTop: 8 }}>
                    <button className="btn" disabled={actionLoading === b.id} onClick={() => cancelBooking(b.id)}>
                      {actionLoading === b.id ? "Cancelling..." : "Cancel booking"}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
