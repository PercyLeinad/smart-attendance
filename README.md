# 📌 Attendance Management System

A sleek, high-performance attendance tracking system built with
**FastAPI**, **SQLAlchemy**, and **Tailwind CSS**.

AdminPro features **QR-based check-ins**, **real-time analytics**, and
**automated reporting**, making it ideal for modern institutional or
corporate environments.

------------------------------------------------------------------------

## ✨ Key Features

### 🔐 Dual-ID Support

Staff can check in and check out using:

-   **ID Number**
-   **ANY ID**

This provides flexible identification without compromising validation
integrity.

------------------------------------------------------------------------

### 🧠 Intelligent Attendance Logic

The system ensures accurate and consistent attendance tracking by:

-   Preventing **double check-ins**
-   Strictly validating daily attendance state
-   Automatically handling:
    -   Missing check-outs
    -   Invalid state transitions

------------------------------------------------------------------------

### 📊 Modern Admin Dashboard

A premium, responsive interface designed for efficiency and clarity.

**Features include:**

-   Real-time attendance statistics
-   Dynamic date-range reporting
-   CSV export functionality
-   Fully responsive design (desktop & tablet optimized)

------------------------------------------------------------------------

### 🔒 Enhanced Security

QR codes are secured using **TOTP (Time-based One-Time Password)**
technology.

This prevents:

-   QR spoofing\
-   Screenshot/photo reuse\
-   Code sharing between users

------------------------------------------------------------------------

## 🛠️ Tech Stack
---

| **Layer**      | **Technology**               |
|----------------|------------------------------|
| Backend        | FastAPI                      |
| Database       | MariaDB                      |
| ORM            | SQLAlchemy (Textual Queries) |
| Frontend       | FontAwesome 7                |
| Frontend Logic | Vanilla JS (ES6+)            |


