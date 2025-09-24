
// src/App.js
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Signup from "./pages/Signup";
import Signin from "./pages/Signin";
import Home from "./pages/Home";
import BusDetails from "./pages/BusDetails";
import ConfirmReservation from "./pages/ConfirmReservation";
import Profile from "./pages/Profile"; // <-- add this import
import Header from "./components/Header";
import { AuthContext } from "./contexts/AuthContext";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminRequests from "./pages/admin/Requests";

function PrivateRoute({ children }) {
  const { user, loadingMe } = React.useContext(AuthContext);
  // while auth is hydrating, don't show redirect — prevents flicker
  if (loadingMe) return null;
  if (!user) return <Navigate to="/signin" replace />;
  return children;
}

function AdminRoute({ children }) {
  const { user, loadingMe } = React.useContext(AuthContext);
  if (loadingMe) return null;
  if (!user) return <Navigate to="/signin" replace />;
  if (user.role !== "admin") return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <div className="app">
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/signin" element={<Signin />} />

          {/* Profile route (protected) */}
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            }
          />

          <Route
            path="/buses/:busId"
            element={
              <PrivateRoute>
                <BusDetails />
              </PrivateRoute>
            }
          />
          <Route
            path="/confirm/:reservationId"
            element={
              <PrivateRoute>
                <ConfirmReservation />
              </PrivateRoute>
            }
          />

          {/* Admin */}
          <Route
            path="/admin/dashboard"
            element={
              <AdminRoute>
                <AdminDashboard />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/requests"
            element={
              <AdminRoute>
                <AdminRequests />
              </AdminRoute>
            }
          />
          <Route path="*" element={<div>Page not found</div>} />
        </Routes>
      </main>
    </div>
  );
}
