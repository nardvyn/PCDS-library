using System.Globalization;
using System.Text.Json.Serialization;

namespace PCDSLibrary.Desktop.Models
{
    public class AuditLogsResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";

        [JsonPropertyName("logs")]
        public List<AuditLogData> Logs { get; set; } = new();
    }

    public class AuditLogData
    {
        [JsonPropertyName("audit_log_id")]
        public int AuditLogId { get; set; }

        [JsonPropertyName("actor_name")]
        public string ActorName { get; set; } = "";

        [JsonPropertyName("actor_role")]
        public string ActorRole { get; set; } = "";

        [JsonPropertyName("action")]
        public string Action { get; set; } = "";

        [JsonPropertyName("entity_type")]
        public string EntityType { get; set; } = "";

        [JsonPropertyName("entity_id")]
        public string EntityId { get; set; } = "";

        [JsonPropertyName("details")]
        public string Details { get; set; } = "";

        [JsonPropertyName("created_at")]
        public string CreatedAt { get; set; } = "";

        public string TimestampDisplay => DateTime.TryParse(CreatedAt, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out var timestamp)
            ? timestamp.ToLocalTime().ToString("MMM d, yyyy h:mm tt")
            : CreatedAt;

        public string RecordDisplay => string.IsNullOrWhiteSpace(EntityId) ? EntityType : $"{EntityType} #{EntityId}";
    }
}
