# 🚍 Busly – Bus Booking System  

A full-stack bus booking application built with **FastAPI (Python)**, **MongoDB**, and **React.js**, implementing **concurrent seat reservation with multithreading, locks, and synchronization** to ensure **atomic bookings and cancellations**.  

This project demonstrates **real-world system design concepts** such as **concurrency control, authentication, role-based access, and revenue tracking**.  

---

## ✨ Features  

### 🔑 User Module  
- **Sign Up Bonus**: New users get `₹1000` credited automatically.  
- **Wallet Management**: Users can request additional balance from Admin.  
- **Search & Book**:  
  - Search buses by **source and destination cities**.  
  - View available seats and prices.  
  - Book multiple seats with **thread-safe seat locking**.  
- **Seat Cancellation**:  
  - Users can cancel upcoming bookings.  
  - Cancelled amount is credited back to user’s wallet.  
- **User Profile**:  
  - View past bookings.  
  - Update password.  
  - Track wallet transactions.  

### 🛠️ Admin Module  
- **Route Management**: Create routes with source and destination cities.  
- **Bus Management**:  
  - Add buses under routes.  
  - Define seat count, pricing, and schedule.  
  - Open bookings **one week before departure**.  
- **Revenue Dashboard**:  
  - Track revenue **daily, monthly, yearly**.  
- **User Requests**: Approve balance requests from users.  
- **Automated Cleanup**:  
  - Buses and bookings are closed **30 minutes before departure**.  
  - Amount from bookings is transferred to **Admin account**.  

---

## 🧵 Concurrency & Threading – The Core Innovation  

The **heart of the system** lies in **seat reservation handling**. Multiple users may attempt to book the same seat **simultaneously**. To avoid **double booking**, we implemented a **thread-safe locking mechanism**:  

- **Shared Resource**: Each seat of a bus is treated as a **shared resource**.  
- **Lock Acquisition**:  
  - When a user selects a seat, the system attempts to **acquire a lock** on that seat.  
  - If the seat is already locked by another transaction, booking fails with a **conflict**.  
- **Atomic Reservation**:  
  - Either all selected seats are locked successfully → booking confirmed.  
  - Or if any conflict arises → rollback & release previously locked seats.  
- **Lock Release**:  
  - Once a booking is confirmed or cancelled, the lock is released back into the pool.  

👉 **Why is this important?**  
Without locks, two users could **simultaneously book the same seat**, leading to **data inconsistency** and financial disputes. By using **threading + locking**, we guarantee **100% atomicity** and **isolation** of seat booking operations.  

---

### 🔒 Pseudo Workflow of Locking  

```plaintext
User selects seats → Try to acquire locks
    If all locks acquired:
        Reserve seats
        Deduct wallet balance
    Else:
        Release acquired locks
        Return "Seats already booked"
