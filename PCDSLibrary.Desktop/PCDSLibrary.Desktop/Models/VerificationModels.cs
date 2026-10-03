using System.Text.Json.Serialization;

namespace PCDSLibrary.Desktop.Models
{
    public class VerificationProfilesResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";

        [JsonPropertyName("profiles")]
        public List<VerificationProfileData> Profiles { get; set; } = new();
    }

    public class VerificationResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";
    }

    public class VerificationProfileData
    {
        [JsonPropertyName("profile_id")]
        public int? ProfileId { get; set; }

        [JsonPropertyName("user_id")]
        public int UserId { get; set; }

        [JsonPropertyName("full_name")]
        public string FullName { get; set; } = "";

        [JsonPropertyName("email")]
        public string Email { get; set; } = "";

        [JsonPropertyName("school_id_number")]
        public string SchoolIdNumber { get; set; } = "";

        [JsonPropertyName("verification_status")]
        public string VerificationStatus { get; set; } = "";

        [JsonPropertyName("role")]
        public string Role { get; set; } = "";

        [JsonPropertyName("account_status")]
        public string AccountStatus { get; set; } = "";

        [JsonPropertyName("course")]
        public string? Course { get; set; }

        [JsonPropertyName("year_level")]
        public string? YearLevel { get; set; }

        [JsonPropertyName("section")]
        public string? Section { get; set; }

        [JsonPropertyName("department")]
        public string? Department { get; set; }

        [JsonPropertyName("contact_number")]
        public string? ContactNumber { get; set; }

        [JsonPropertyName("address")]
        public string? Address { get; set; }

        [JsonPropertyName("school_id_image")]
        public string? SchoolIdImage { get; set; }

        [JsonPropertyName("created_at")]
        public string? CreatedAt { get; set; }
    }
}
