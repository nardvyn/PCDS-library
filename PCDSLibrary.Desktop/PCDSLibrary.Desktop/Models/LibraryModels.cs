using System.Text.Json.Serialization;

namespace PCDSLibrary.Desktop.Models
{
    public class LibrarySettingsResponse
    {
        [JsonPropertyName("success")] public bool Success { get; set; }
        [JsonPropertyName("message")] public string Message { get; set; } = "";
        [JsonPropertyName("settings")] public LibrarySettingsData Settings { get; set; } = new();
    }

    public class LibrarySettingsData
    {
        [JsonPropertyName("student_loan_days")] public int StudentLoanDays { get; set; } = 7;
        [JsonPropertyName("teacher_loan_days")] public int TeacherLoanDays { get; set; } = 14;
        [JsonPropertyName("student_max_books")] public int StudentMaxBooks { get; set; } = 3;
        [JsonPropertyName("teacher_max_books")] public int TeacherMaxBooks { get; set; } = 3;
        [JsonPropertyName("daily_penalty")] public decimal DailyPenalty { get; set; } = 10;
        [JsonPropertyName("notifications_enabled")] public bool NotificationsEnabled { get; set; } = true;
    }

    public class LibraryListResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";

        [JsonPropertyName("loans")]
        public List<LoanData> Loans { get; set; } = new();

        [JsonPropertyName("penalties")]
        public List<PenaltyData> Penalties { get; set; } = new();

        [JsonPropertyName("total_penalties")] public decimal TotalPenalties { get; set; }
        [JsonPropertyName("unpaid_penalties")] public decimal UnpaidPenalties { get; set; }
        [JsonPropertyName("paid_penalties")] public decimal PaidPenalties { get; set; }

        [JsonPropertyName("borrowers")]
        public List<BorrowerData> Borrowers { get; set; } = new();

        [JsonPropertyName("books")]
        public List<BookData> Books { get; set; } = new();
    }

    public class LoanData
    {
        [JsonPropertyName("loan_id")] public int LoanId { get; set; }
        [JsonPropertyName("borrower_name")] public string BorrowerName { get; set; } = "";
        [JsonPropertyName("school_id")] public string SchoolId { get; set; } = "";
        [JsonPropertyName("role")] public string Role { get; set; } = "";
        [JsonPropertyName("book_title")] public string BookTitle { get; set; } = "";
        [JsonPropertyName("accession_number")] public string AccessionNumber { get; set; } = "";
        [JsonPropertyName("borrowed_at")] public string BorrowedAt { get; set; } = "";
        [JsonPropertyName("due_date")] public string DueDate { get; set; } = "";
        [JsonPropertyName("returned_at")] public string ReturnedAt { get; set; } = "";
        [JsonPropertyName("late_days")] public int LateDays { get; set; }
        [JsonPropertyName("penalty_amount")] public decimal PenaltyAmount { get; set; }
        [JsonPropertyName("penalty_status")] public string PenaltyStatus { get; set; } = "NONE";
        [JsonPropertyName("status")] public string Status { get; set; } = "";
    }

    public class PenaltyData
    {
        [JsonPropertyName("penalty_id")] public int PenaltyId { get; set; }
        [JsonPropertyName("borrower_name")] public string BorrowerName { get; set; } = "";
        [JsonPropertyName("school_id")] public string SchoolId { get; set; } = "";
        [JsonPropertyName("book_title")] public string BookTitle { get; set; } = "";
        [JsonPropertyName("amount")] public decimal Amount { get; set; }
        [JsonPropertyName("late_days")] public int LateDays { get; set; }
        [JsonPropertyName("status")] public string Status { get; set; } = "";
        [JsonPropertyName("created_at")] public string CreatedAt { get; set; } = "";
    }

    public class BorrowerData
    {
        [JsonPropertyName("user_id")] public int UserId { get; set; }
        [JsonPropertyName("full_name")] public string FullName { get; set; } = "";
        [JsonPropertyName("email")] public string Email { get; set; } = "";
        [JsonPropertyName("contact_number")] public string? ContactNumber { get; set; }
        [JsonPropertyName("address")] public string? Address { get; set; }
        [JsonPropertyName("role")] public string Role { get; set; } = "";
        [JsonPropertyName("account_status")] public string AccountStatus { get; set; } = "";
        [JsonPropertyName("school_id_number")] public string SchoolId { get; set; } = "";
        [JsonPropertyName("course")] public string? Course { get; set; }
        [JsonPropertyName("year_level")] public string? YearLevel { get; set; }
        [JsonPropertyName("section")] public string? Section { get; set; }
        [JsonPropertyName("department")] public string? Department { get; set; }
        [JsonPropertyName("verification_status")] public string VerificationStatus { get; set; } = "";
        [JsonPropertyName("eligibility_status")] public string EligibilityStatus { get; set; } = "";
        [JsonPropertyName("verification_expires_at")] public string? VerificationExpiresAt { get; set; }
        [JsonPropertyName("created_at")] public string? CreatedAt { get; set; }
        public string CourseOrDepartment => Role == "TEACHER" ? (Department ?? "") : (Course ?? "");
        public string VerificationValidUntil => DateTimeOffset.TryParse(VerificationExpiresAt, out var expiry)
            ? expiry.ToLocalTime().ToString("MMM dd, yyyy")
            : "Not set";
        public string RegisteredOn => DateTimeOffset.TryParse(CreatedAt, out var created)
            ? created.ToLocalTime().ToString("MMM dd, yyyy")
            : "Not available";
    }

    public class ReportsSummary
    {
        [JsonPropertyName("success")] public bool Success { get; set; }
        [JsonPropertyName("message")] public string Message { get; set; } = "";
        [JsonPropertyName("total_books")] public int TotalBooks { get; set; }
        [JsonPropertyName("available_books")] public int AvailableBooks { get; set; }
        [JsonPropertyName("borrowed_books")] public int BorrowedBooks { get; set; }
        [JsonPropertyName("pending_requests")] public int PendingRequests { get; set; }
        [JsonPropertyName("approved_requests")] public int ApprovedRequests { get; set; }
        [JsonPropertyName("overdue_books")] public int OverdueBooks { get; set; }
        [JsonPropertyName("borrowers")] public int Borrowers { get; set; }
        [JsonPropertyName("unpaid_penalties")] public decimal UnpaidPenalties { get; set; }
    }

    public class OperationResponse
    {
        [JsonPropertyName("success")] public bool Success { get; set; }
        [JsonPropertyName("message")] public string Message { get; set; } = "";
        [JsonPropertyName("recipient_count")] public int RecipientCount { get; set; }
    }
}
