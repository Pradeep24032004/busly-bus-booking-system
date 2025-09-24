
// SeatMap.js
import React from "react";
import "./seatmap.css";

/**
 * SeatMap Component
 * 
 * Props:
 * - seats: array of { _id?, seat_number: string, status: "available"|"reserved"|"booked", side?: "left"|"right", row?: number, col?: number }
 * - selected: Set of seat_number strings
 * - onToggle(seat_number): function called when user clicks a seat
 *
 * This component is purely presentational — it does NOT fetch data.
 */
export default function SeatMap({ seats = [], selected = new Set(), onToggle = () => {} }) {
  console.log("SeatMap props:", { 
    seatsCount: seats.length, 
    selectedCount: selected?.size || 0, 
    onToggleDefined: typeof onToggle === 'function'
  });

  if (!Array.isArray(seats)) {
    console.warn("SeatMap: seats prop is not an array:", seats);
    return (
      <div className="seatmap-wrapper">
        <div className="seatmap-error">
          <p>Invalid seat data provided</p>
        </div>
      </div>
    );
  }

  const selectedSet = selected && typeof selected.has === 'function' 
    ? selected 
    : new Set();

  if (seats.length === 0) {
    return (
      <div className="seatmap-wrapper">
        <div className="seatmap-empty">
          <p>No seats available</p>
        </div>
      </div>
    );
  }

  // If seats include side/row/col metadata, render grid by rows for realistic bus layout
  const hasLayoutMeta = seats.every(s => s && (s.row !== undefined) && (s.side !== undefined) && (s.col !== undefined));

  if (hasLayoutMeta) {
    // Build a map: row -> { left: {1,2}, right: {1,2} }
    const rowsMap = new Map();
    seats.forEach(seat => {
      const row = Number(seat.row) || 0;
      if (!rowsMap.has(row)) rowsMap.set(row, { left: {1: null, 2: null}, right: {1: null, 2: null} });
      rowsMap.get(row)[seat.side][seat.col] = seat;
    });

    const sortedRows = Array.from(rowsMap.keys()).sort((a,b) => a - b);

    const renderSeat = (seat) => {
      if (!seat || !seat.seat_number) return (
        <div className="seat seat-empty" key={`empty-${Math.random()}`}></div>
      );

      const seatNumber = String(seat.seat_number);
      const seatStatus = seat.status || "available";
      const isSelected = selectedSet.has(seatNumber);

      const classes = [
        "seat",
        seatStatus,
        isSelected ? "selected" : ""
      ].filter(Boolean).join(" ");

      const isEnabled = seatStatus === "available";

      const handleClick = () => {
        if (typeof onToggle === 'function' && isEnabled) {
          onToggle(seatNumber);
        }
      };

      const title = `Seat ${seatNumber} - ${seatStatus}${isSelected ? ' (selected)' : ''}`;

      return (
        <button
          key={`seat-${seatNumber}`}
          className={classes}
          disabled={!isEnabled}
          onClick={handleClick}
          title={title}
          aria-pressed={isSelected}
          aria-label={title}
          data-seat={seatNumber}
          data-status={seatStatus}
        >
          <span className="seat-number">{seatNumber}</span>
        </button>
      );
    };

    return (
      <div className="seatmap-wrapper">
        <div className="seatmap-legend">
          <div className="legend-item">
            <div className="seat-demo available"></div><span>Available</span>
          </div>
          <div className="legend-item">
            <div className="seat-demo selected"></div><span>Selected</span>
          </div>
          <div className="legend-item">
            <div className="seat-demo reserved"></div><span>Reserved</span>
          </div>
          <div className="legend-item">
            <div className="seat-demo booked"></div><span>Booked</span>
          </div>
        </div>

        <div className="bus-front">
          <div className="driver-section">
            <span>🚌 Driver</span>
          </div>
        </div>

        <div className="seatmap">
          <div className="seat-rows">
            {sortedRows.map(rowNum => {
              const row = rowsMap.get(rowNum);
              return (
                <div className="seat-row" key={`row-${rowNum}`}>
                  <div className="seat-row-left">
                    {renderSeat(row.left[1])}
                    {renderSeat(row.left[2])}
                  </div>

                  <div className="aisle" aria-hidden="true">
                    <div className="aisle-line"></div>
                  </div>

                  <div className="seat-row-right">
                    {renderSeat(row.right[1])}
                    {renderSeat(row.right[2])}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="seatmap-summary">
          <div className="summary-item"><strong>Total Seats:</strong> {seats.length}</div>
          <div className="summary-item"><strong>Available:</strong> {seats.filter(s => s.status === 'available').length}</div>
          <div className="summary-item"><strong>Selected:</strong> {selectedSet.size}</div>
        </div>
      </div>
    );
  }

  // Fallback: old behavior (numeric sort, left/right split by index)
  const seatList = seats.filter(seat => seat && seat.seat_number);
  const seatsSorted = [...seatList].sort((a, b) => {
    const na = parseInt(String(a.seat_number), 10);
    const nb = parseInt(String(b.seat_number), 10);
    if (!isNaN(na) && !isNaN(nb)) return na - nb;
    return String(a.seat_number).localeCompare(String(b.seat_number));
  });

  const totalSeats = seatsSorted.length;
  const seatsPerRow = 4;
  const leftSeats = [];
  const rightSeats = [];

  seatsSorted.forEach((seat, index) => {
    const seatInRow = index % seatsPerRow;
    if (seatInRow < seatsPerRow / 2) leftSeats.push(seat);
    else rightSeats.push(seat);
  });

  const renderSeatFallback = (seat) => {
    if (!seat || !seat.seat_number) return null;
    const seatNumber = String(seat.seat_number);
    const seatStatus = seat.status || "available";
    const isSelected = selectedSet.has(seatNumber);
    const classes = ["seat", seatStatus, isSelected ? "selected" : ""].filter(Boolean).join(" ");
    const isEnabled = seatStatus === "available";
    const handleClick = () => {
      if (typeof onToggle === 'function' && isEnabled) onToggle(seatNumber);
    };
    const title = `Seat ${seatNumber} - ${seatStatus}${isSelected ? ' (selected)' : ''}`;
    return (
      <button
        key={`seat-${seatNumber}`}
        className={classes}
        disabled={!isEnabled}
        onClick={handleClick}
        title={title}
        aria-pressed={isSelected}
        aria-label={title}
        data-seat={seatNumber}
        data-status={seatStatus}
      >
        <span className="seat-number">{seatNumber}</span>
      </button>
    );
  };

  return (
    <div className="seatmap-wrapper">
      <div className="seatmap-legend">
        <div className="legend-item"><div className="seat-demo available"></div><span>Available</span></div>
        <div className="legend-item"><div className="seat-demo selected"></div><span>Selected</span></div>
        <div className="legend-item"><div className="seat-demo reserved"></div><span>Reserved</span></div>
        <div className="legend-item"><div className="seat-demo booked"></div><span>Booked</span></div>
      </div>

      <div className="bus-front"><div className="driver-section"><span>🚌 Driver</span></div></div>

      <div className="seatmap">
        <div className="side side-left">{leftSeats.map(renderSeatFallback)}</div>
        <div className="aisle" aria-hidden="true"><div className="aisle-line"></div></div>
        <div className="side side-right">{rightSeats.map(renderSeatFallback)}</div>
      </div>

      <div className="seatmap-summary">
        <div className="summary-item"><strong>Total Seats:</strong> {totalSeats}</div>
        <div className="summary-item"><strong>Available:</strong> {seats.filter(s => s.status === 'available').length}</div>
        <div className="summary-item"><strong>Selected:</strong> {selectedSet.size}</div>
      </div>
    </div>
  );
}
