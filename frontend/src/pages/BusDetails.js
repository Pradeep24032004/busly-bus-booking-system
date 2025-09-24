
// BusDetails.js
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api";
import SeatMap from "../components/SeatMap";

export default function BusDetails() {
  const { busId } = useParams();
  const navigate = useNavigate();
  const [bus, setBus] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (busId) {
      fetchBus();
    }
    // eslint-disable-next-line
  }, [busId]);

  const fetchBus = async () => {
    if (!busId) {
      setErr("Bus ID is required");
      return;
    }

    setLoading(true);
    setErr(null);
    
    try {
      console.log("Fetching bus details for ID:", busId);
      const res = await api.get(`/buses/${busId}`);
      
      console.log("API Response:", res.data);
      if (!res.data || !res.data.bus) {
        throw new Error("Invalid response format - missing bus data");
      }
      
      setBus(res.data.bus);
      
      const seatsArray = res.data.seats || [];
      if (!Array.isArray(seatsArray)) {
        console.warn("Seats data is not an array:", seatsArray);
        setSeats([]);
        return;
      }
      
      // Map seats to the format expected by SeatMap component, keep side/row/col if present
      const mappedSeats = seatsArray.map((seat) => ({
        _id: seat._id,
        seat_number: String(seat.seat_number || ""),
        status: seat.status || "available",
        side: seat.side || undefined,
        row: seat.row !== undefined ? Number(seat.row) : undefined,
        col: seat.col !== undefined ? Number(seat.col) : undefined
      }));
      
      console.log("Mapped seats:", mappedSeats.slice(0, 6));
      setSeats(mappedSeats);
      
      // Clear any previously selected seats when fetching fresh data
      setSelected(new Set());
      
    } catch (error) {
      console.error("Error fetching bus details:", error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          "Failed to fetch bus details";
      setErr(errorMessage);
      
      // If bus not found, redirect after a short delay (2s)
      if (error.response?.status === 404) {
        setTimeout(() => {
          navigate("/search");
        }, 2000);
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleSeat = (seatNumber) => {
    console.log("Toggling seat:", seatNumber);
    setErr(null);
    
    if (!seatNumber) {
      console.warn("Invalid seat number provided to toggleSeat");
      return;
    }
    
    setSelected((prevSelected) => {
      const newSelected = new Set(prevSelected);
      
      if (newSelected.has(seatNumber)) {
        // Deselect the seat
        newSelected.delete(seatNumber);
      } else {
        // Check if seat is available before selecting
        const seatObj = seats.find((s) => s.seat_number === seatNumber);
        
        if (!seatObj) {
          console.warn("Seat not found:", seatNumber);
          setErr(`Seat ${seatNumber} not found`);
          return prevSelected;
        }
        
        if (seatObj.status !== "available") {
          setErr(`Seat ${seatNumber} is not available (status: ${seatObj.status})`);
          return prevSelected;
        }
        
        // Select the seat
        newSelected.add(seatNumber);
      }
      
      console.log("Selected seats:", Array.from(newSelected));
      return newSelected;
    });
  };

  const reserveSeats = async () => {
    if (selected.size === 0) {
      setErr("Please select at least one seat");
      return;
    }

    if (!busId) {
      setErr("Bus ID is missing");
      return;
    }

    setActionLoading(true);
    setErr(null);
    
    try {
      console.log("Reserving seats:", Array.from(selected), "for bus:", busId);
      
      const res = await api.post(`/reservations/select/${busId}`, {
        seat_numbers: Array.from(selected)
      });
      
      console.log("Reservation response:", res.data);
      
      if (!res.data || !res.data._id) {
        throw new Error("Invalid reservation response");
      }
      
      const reservation = {
        id: res.data._id,
        bus_id: res.data.bus_id || busId,
        seat_numbers: res.data.seat_numbers || Array.from(selected),
        total_price: res.data.total_price || 0,
        expires_at: res.data.expires_at
      };
      
      localStorage.setItem(`reservation_${reservation.id}`, JSON.stringify(reservation));
      
      navigate(`/confirm/${reservation.id}`);
      
    } catch (error) {
      console.error("Error reserving seats:", error);
      
      const errorData = error.response?.data;
      let errorMessage = "Failed to reserve seats";
      
      if (errorData) {
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
        
        // Handle seat conflicts - refresh seat data
        if (errorData.conflicting_seats && Array.isArray(errorData.conflicting_seats)) {
          errorMessage += ` Conflicting seats: ${errorData.conflicting_seats.join(', ')}`;
          await fetchBus();
        }
      }
      
      setErr(errorMessage);
    } finally {
      setActionLoading(false);
    }
  };

  const clearSelection = () => {
    setSelected(new Set());
    setErr(null);
  };

  // Debug info for development
  const debugInfo = {
    busId,
    loading,
    busExists: !!bus,
    seatsCount: seats.length,
    selectedCount: selected.size,
    selectedSeats: Array.from(selected)
  };
  
  console.log("BusDetails render state:", debugInfo);

  if (loading) {
    return (
      <div className="card">
        <div>Loading bus details...</div>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <div>Please wait...</div>
        </div>
      </div>
    );
  }

  if (err && !bus) {
    return (
      <div className="card">
        <div className="error">
          <h3>Error</h3>
          <p>{err}</p>
          <button 
            className="btn-secondary" 
            onClick={() => navigate("/search")}
            style={{ marginTop: '10px' }}
          >
            Back to Search
          </button>
        </div>
      </div>
    );
  }

  if (!bus) {
    return (
      <div className="card">
        <div>Bus not found</div>
        <button 
          className="btn-secondary" 
          onClick={() => navigate("/search")}
          style={{ marginTop: '10px' }}
        >
          Back to Search
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h3>{bus.name || "Bus Details"}</h3>
        <div>
          <strong>Route:</strong> {bus.route_id ? `Route ${bus.route_id}` : "N/A"}
        </div>
        {bus.start_time && (
          <div>
            <strong>Departure:</strong> {new Date(bus.start_time).toLocaleString()}
          </div>
        )}
        {bus.price_per_seat && (
          <div>
            <strong>Price per seat:</strong> ₹{bus.price_per_seat}
          </div>
        )}
        {bus.status && (
          <div>
            <strong>Status:</strong> {bus.status}
          </div>
        )}
      </div>

      <div className="card">
        <h4>Select Seats</h4>
        
        {process.env.NODE_ENV === 'development' && (
          <div style={{ 
            background: '#f0f0f0', 
            padding: '10px', 
            margin: '10px 0', 
            fontSize: '12px',
            borderRadius: '4px'
          }}>
            <strong>Debug Info:</strong>
            <div>Bus ID: {busId}</div>
            <div>Seats found: {seats.length}</div>
            <div>Selected: {selected.size}</div>
            {seats.length > 0 && (
              <div>Sample seat: {JSON.stringify(seats[0])}</div>
            )}
          </div>
        )}
        
        {seats.length > 0 ? (
          <SeatMap 
            seats={seats} 
            selected={selected} 
            onToggle={toggleSeat} 
          />
        ) : (
          <div style={{ 
            textAlign: 'center', 
            padding: '20px',
            color: '#666'
          }}>
            <p>No seats available for this bus</p>
            <small>This might be a configuration issue. Please contact support.</small>
          </div>
        )}
        
        <div className="mt" style={{ marginTop: '15px' }}>
          <strong>Selected Seats:</strong> {
            selected.size > 0 
              ? Array.from(selected).sort((a, b) => {
                  const na = parseInt(a, 10);
                  const nb = parseInt(b, 10);
                  return !isNaN(na) && !isNaN(nb) ? na - nb : a.localeCompare(b);
                }).join(", ")
              : "None"
          }
        </div>
        
        {selected.size > 0 && bus.price_per_seat && (
          <div style={{ marginTop: '10px' }}>
            <strong>Total Price:</strong> ₹{selected.size * bus.price_per_seat}
          </div>
        )}
        
        {err && (
          <div className="error" style={{ marginTop: '10px' }}>
            {typeof err === 'string' ? err : JSON.stringify(err)}
          </div>
        )}
        
        <div className="actions" style={{ marginTop: '15px' }}>
          <button 
            className="btn" 
            onClick={reserveSeats} 
            disabled={actionLoading || selected.size === 0}
            style={{ marginRight: '10px' }}
          >
            {actionLoading 
              ? "Reserving..." 
              : `Reserve ${selected.size} Seat${selected.size === 1 ? '' : 's'}`
            }
          </button>
          
          <button 
            className="btn-secondary" 
            onClick={clearSelection}
            disabled={actionLoading || selected.size === 0}
            style={{ marginRight: '10px' }}
          >
            Clear Selection
          </button>
          
          <button 
            className="btn-secondary" 
            onClick={() => navigate("/search")}
            disabled={actionLoading}
          >
            Back to Search
          </button>
        </div>
      </div>
    </div>
  );
}
