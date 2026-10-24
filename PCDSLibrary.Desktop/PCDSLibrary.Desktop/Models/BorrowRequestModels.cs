using System.Text.Json.Serialization;

namespace PCDSLibrary.Desktop.Models
{
    public class BorrowRequestsResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";

        [JsonPropertyName("requests")]
        public List<BorrowRequestData> Requests { get; set; } = new();
    }

    public class BorrowRequestResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";
    }

    public class BorrowRequestData
    {
        [JsonPropertyName("request_id")]
        public int RequestId { get; set; }

        [JsonPropertyName("borrower_name")]
        public string BorrowerName { get; set; } = "";

        [JsonPropertyName("school_id")]
        public string SchoolId { get; set; } = "";

        [JsonPropertyName("borrower_role")]
        public string BorrowerRole { get; set; } = "";

        [JsonPropertyName("borrower_email")] public string BorrowerEmail { get; set; } = "";
        [JsonPropertyName("borrower_contact")] public string BorrowerContact { get; set; } = "";
        [JsonPropertyName("borrower_course")] public string BorrowerCourse { get; set; } = "";
        [JsonPropertyName("borrower_year_level")] public string BorrowerYearLevel { get; set; } = "";
        [JsonPropertyName("borrower_section")] public string BorrowerSection { get; set; } = "";
        [JsonPropertyName("borrower_department")] public string BorrowerDepartment { get; set; } = "";
        [JsonPropertyName("borrower_address")] public string BorrowerAddress { get; set; } = "";
        [JsonPropertyName("borrower_account_status")] public string BorrowerAccountStatus { get; set; } = "";
        [JsonPropertyName("borrower_verification_status")] public string BorrowerVerificationStatus { get; set; } = "";
        [JsonPropertyName("borrower_eligibility_status")] public string BorrowerEligibilityStatus { get; set; } = "";
        [JsonPropertyName("borrower_verification_expires_at")] public string? BorrowerVerificationExpiresAt { get; set; }

        [JsonPropertyName("book_title")]
        public string BookTitle { get; set; } = "";

        [JsonPropertyName("author")]
        public string Author { get; set; } = "";

        [JsonPropertyName("call_number")]
        public string CallNumber { get; set; } = "";

        [JsonPropertyName("accession_number")]
        public string AccessionNumber { get; set; } = "";

        [JsonPropertyName("has_book_image")]
        public bool HasBookImage { get; set; }

        [JsonPropertyName("status")]
        public string Status { get; set; } = "";

        [JsonPropertyName("requested_at")]
        public string RequestedAt { get; set; } = "";
    }
}
