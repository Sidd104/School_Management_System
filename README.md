# School_Management_System

This code is a **complete School Management System** developed using **Python’s Tkinter** for the graphical user interface and **SQLite** as the local database. It is designed to help schools or small educational institutions efficiently manage their daily administrative tasks.

The system provides a **login interface** for authentication, with user roles like *admin*, *teacher*, and *accountant*. A default admin account (`admin/admin`) is automatically created when the database initializes.

Once logged in, users can access multiple modules through a sidebar menu:

* **Dashboard:** Displays important school statistics such as the total number of students, average attendance in the last 30 days, and total paid fee records. It also shows a simple bar graph representing attendance trends for the last six months.
* **Student Management:** Allows adding, editing, searching, and deleting student records. Each record includes personal details (name, DOB), academic details (class, section, admission number), and guardian contact information.
* **Attendance Module:** Enables marking daily attendance as *Present* or *Absent*. Attendance records are stored by date and linked to each student. Users can filter students by class, view attendance from the past week, and update attendance statuses.
* **Fees and Payments:** Handles financial management by creating fee invoices, recording payments, updating payment statuses, and viewing recent transactions. Each payment entry includes amount, method (cash, card, online), and optional transaction references.
* **Exam Schedule:** Lets users create, view, and delete exam schedules. Each exam entry includes details such as exam title, class, subject, date, time, and room/hall.
* **Settings:** Allows password changes and adding new user accounts.

The system automatically creates and manages multiple database tables (`users`, `students`, `attendance`, `fees`, `payments`, `exam_schedule`). All records are saved in a local SQLite file called `school.db`.

Overall, this application provides a clean, organized, and user-friendly interface for handling student data, tracking attendance, managing finances, and scheduling exams — making it a practical school administration solution built entirely in Python.
