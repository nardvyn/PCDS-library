using System.Text.Json.Serialization;

namespace PCDSLibrary.Desktop.Models
{
    public class CreateBookRequest
    {
        [JsonPropertyName("title")]
        public string Title { get; set; } = "";

        [JsonPropertyName("author")]
        public string Author { get; set; } = "";

        [JsonPropertyName("call_number")]
        public string CallNumber { get; set; } = "";

        [JsonPropertyName("isbn")]
        public string Isbn { get; set; } = "";

        [JsonPropertyName("accession_number")]
        public string AccessionNumber { get; set; } = "";

        [JsonPropertyName("category")]
        public string Category { get; set; } = "";

        [JsonPropertyName("publication_year")]
        public int? PublicationYear { get; set; }

        [JsonPropertyName("total_copies")]
        public int TotalCopies { get; set; } = 1;

        [JsonPropertyName("description")]
        public string Description { get; set; } = "";
    }

    public class BookResponse
    {
        [JsonPropertyName("success")]
        public bool Success { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; } = "";

        [JsonPropertyName("book")]
        public BookData? Book { get; set; }
    }

    public class BookData
    {
        [JsonPropertyName("book_id")]
        public int BookId { get; set; }

        [JsonPropertyName("title")]
        public string Title { get; set; } = "";

        [JsonPropertyName("author")]
        public string Author { get; set; } = "";

        [JsonPropertyName("category")]
        public string? Category { get; set; }

        [JsonPropertyName("call_number")]
        public string? CallNumber { get; set; }

        [JsonPropertyName("isbn")]
        public string? Isbn { get; set; }

        [JsonPropertyName("publication_year")]
        public int? PublicationYear { get; set; }

        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("cover_image")]
        public string? CoverImage { get; set; }

        [JsonPropertyName("total_copies")]
        public int TotalCopies { get; set; }

        [JsonPropertyName("accession_number")]
        public string AccessionNumber { get; set; } = "";

        [JsonPropertyName("available_copies")]
        public int AvailableCopies { get; set; }
    }
}
