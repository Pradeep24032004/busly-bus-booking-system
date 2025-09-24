
// src/components/Header.js
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../contexts/AuthContext";

export default function Header() {
  const { user, signout, loadingMe } = React.useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    signout();
    navigate("/signin");
  };

  return (
    <header className="header">
      <div className="header-left">
        <Link to="/" className="brand">BusBooking</Link>
      </div>
      <div className="header-right">
        {loadingMe ? (
          <span>Loading...</span>
        ) : user ? (
          <>
            <button className="btn-link" onClick={() => navigate("/")}>Home</button>
            <button className="btn-link" onClick={() => navigate("/profile")}>Profile</button>
            {user.role === "admin" && (
              <>
                <button className="btn-link" onClick={() => navigate("/admin/dashboard")}>Admin Dashboard</button>
                <button className="btn-link" onClick={() => navigate("/admin/requests")}>Requests</button>
              </>
            )}
            <button className="btn-link" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/signin" className="btn-link">Sign in</Link>
            <Link to="/signup" className="btn-link">Sign up</Link>
          </>
        )}
      </div>
    </header>
  );
}
