using System.Text.Json.Serialization;

namespace PCDSLibrary.Desktop.Models
{
    public class StaffRegistrationRequest
    {
        [JsonPropertyName("full_name")]
        public string FullName { get; set; } = "";

        [JsonPropertyName("staff_id")]
        public string StaffId { get; set; } = "";

        [JsonPropertyName("email")]
        public string Email { get; set; } = "";

        [JsonPropertyName("password")]
        public string Password { get; set; } = "";

        [JsonPropertyName("invite_code")]
        public string InviteCode { get; set; } = "";
    }

    public class LoginRequest
    {
        [JsonPropertyName("email")]
        public string Email { get; set; } = "";

        [JsonPropertyName("password")]
        public string Password { get; set; } = "";
    }

    public class LoginResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";

        [JsonPropertyName("access_token")]
        public string AccessToken { get; set; } = "";

        [JsonPropertyName("user")]
        public UserData? User { get; set; }
    }

    public class UserData
    {
        [JsonPropertyName("user_id")]
        public int UserId { get; set; }

        [JsonPropertyName("school_id")]
        public string SchoolId { get; set; } = "";

        [JsonPropertyName("full_name")]
        public string FullName { get; set; } = "";

        [JsonPropertyName("role")]
        public string Role { get; set; } = "";

        [JsonPropertyName("account_status")]
        public string AccountStatus { get; set; } = "";
    }
}
