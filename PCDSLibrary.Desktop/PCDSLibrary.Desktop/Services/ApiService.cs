using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using PCDSLibrary.Desktop.Models;

namespace PCDSLibrary.Desktop.Services
{
    public class ApiService
    {
        private readonly HttpClient _httpClient;

        public string AccessToken { get; private set; } = "";

        public ApiService(string accessToken = "")
        {
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(
                    "http://127.0.0.1:5000/api/"
                )
            };

            if (!string.IsNullOrWhiteSpace(accessToken))
            {
                AccessToken = accessToken;
                _httpClient.DefaultRequestHeaders.Authorization =
                    new AuthenticationHeaderValue("Bearer", AccessToken);
            }
        }

        public async Task<bool> CheckHealthAsync()
        {
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(4));
            try
            {
                using var response = await _httpClient.GetAsync("health", timeout.Token);
                return response.IsSuccessStatusCode;
            }
            catch (HttpRequestException)
            {
                return false;
            }
            catch (OperationCanceledException)
            {
                return false;
            }
        }

        public async Task<LoginResponse> LoginAsync(
            string email,
            string password)
        {
            var requestData = new LoginRequest
            {
                Email = email,
                Password = password
            };

            try
            {
                var response =
                    await _httpClient.PostAsJsonAsync(
                        "auth/login",
                        requestData
                    );

                var result =
                    await response.Content
                        .ReadFromJsonAsync<LoginResponse>();

                if (result == null)
                {
                    return new LoginResponse
                    {
                        Success = false,
                        Message =
                            "Invalid response from the server."
                    };
                }

                if (response.IsSuccessStatusCode)
                {
                    AccessToken = result.AccessToken;

                    _httpClient
                        .DefaultRequestHeaders
                        .Authorization =
                        new AuthenticationHeaderValue(
                            "Bearer",
                            AccessToken
                        );
                }

                return result;
            }
            catch (HttpRequestException)
            {
                return new LoginResponse
                {
                    Success = false,
                    Message =
                        "Cannot connect to the Flask server."
                };
            }
            catch (Exception error)
            {
                return new LoginResponse
                {
                    Success = false,
                    Message = error.Message
                };
            }
        }

        public async Task<LoginResponse> RegisterStaffAsync(StaffRegistrationRequest request)
        {
            try
            {
                var response = await _httpClient.PostAsJsonAsync("auth/staff-register", request);
                return await response.Content.ReadFromJsonAsync<LoginResponse>() ?? new LoginResponse
                {
                    Success = false,
                    Message = "Invalid response from the server."
                };
            }
            catch (HttpRequestException)
            {
                return new LoginResponse
                {
                    Success = false,
                    Message = "Cannot connect to the Flask server."
                };
            }
            catch (Exception error)
            {
                return new LoginResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<BookResponse> CreateBookAsync(CreateBookRequest request)
        {
            try
            {
                var response = await _httpClient.PostAsJsonAsync("books", request);
                var result = await response.Content.ReadFromJsonAsync<BookResponse>();

                return result ?? new BookResponse
                {
                    Success = false,
                    Message = "Invalid response from the server."
                };
            }
            catch (HttpRequestException)
            {
                return new BookResponse
                {
                    Success = false,
                    Message = "Cannot connect to the Flask server."
                };
            }
            catch (Exception error)
            {
                return new BookResponse
                {
                    Success = false,
                    Message = error.Message
                };
            }
        }

        public async Task<LibraryListResponse> GetBooksAsync()
        {
            try
            {
                return await _httpClient.GetFromJsonAsync<LibraryListResponse>("books") ?? new LibraryListResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new LibraryListResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<byte[]?> GetBookCoverImageAsync(int bookId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"books/{bookId}/cover-image");
                return response.IsSuccessStatusCode ? await response.Content.ReadAsByteArrayAsync() : null;
            }
            catch
            {
                return null;
            }
        }

        public async Task<BorrowRequestsResponse> GetBorrowRequestsAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("borrow-requests?status=PENDING");
                var result = await response.Content.ReadFromJsonAsync<BorrowRequestsResponse>();
                return result ?? new BorrowRequestsResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new BorrowRequestsResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<BorrowRequestResponse> UpdateBorrowRequestAsync(int requestId, string status)
        {
            try
            {
                var response = await _httpClient.PatchAsJsonAsync($"borrow-requests/{requestId}", new { status });
                var result = await response.Content.ReadFromJsonAsync<BorrowRequestResponse>();
                return result ?? new BorrowRequestResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new BorrowRequestResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<(byte[]? Image, string Error)> GetBorrowRequestBookImageAsync(int requestId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"borrow-requests/{requestId}/book-image");
                if (!response.IsSuccessStatusCode)
                {
                    var error = await response.Content.ReadFromJsonAsync<BorrowRequestResponse>();
                    return (null, error?.Message ?? "Unable to load the book photo.");
                }
                return (await response.Content.ReadAsByteArrayAsync(), "");
            }
            catch (Exception error)
            {
                return (null, error.Message);
            }
        }

        public async Task<VerificationProfilesResponse> GetVerificationProfilesAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("verification/profiles");
                return await response.Content.ReadFromJsonAsync<VerificationProfilesResponse>() ?? new VerificationProfilesResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new VerificationProfilesResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<VerificationResponse> UpdateVerificationProfileAsync(int profileId, string status)
        {
            try
            {
                var response = await _httpClient.PatchAsJsonAsync($"verification/profiles/{profileId}", new { status });
                return await response.Content.ReadFromJsonAsync<VerificationResponse>() ?? new VerificationResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new VerificationResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<(byte[]? Image, string Error)> GetSchoolIdImageAsync(int profileId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"verification/profiles/{profileId}/school-id");
                if (!response.IsSuccessStatusCode)
                {
                    var error = await response.Content.ReadFromJsonAsync<VerificationResponse>();
                    return (null, error?.Message ?? "Unable to load the School ID image.");
                }
                return (await response.Content.ReadAsByteArrayAsync(), "");
            }
            catch (Exception error)
            {
                return (null, error.Message);
            }
        }

        public async Task<VerificationResponse> DeleteBorrowerAsync(int userId)
        {
            try
            {
                var response = await _httpClient.DeleteAsync($"verification/users/{userId}");
                return await response.Content.ReadFromJsonAsync<VerificationResponse>() ?? new VerificationResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new VerificationResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<AuditLogsResponse> GetAuditLogsAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("audit-logs?limit=300");
                return await response.Content.ReadFromJsonAsync<AuditLogsResponse>() ?? new AuditLogsResponse
                {
                    Success = false,
                    Message = "Invalid response from the server."
                };
            }
            catch (Exception error)
            {
                return new AuditLogsResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<LibraryListResponse> GetLoansAsync(bool overdueOnly = false)
        {
            try
            {
                var path = overdueOnly ? "library/overdue" : "library/loans";
                return await _httpClient.GetFromJsonAsync<LibraryListResponse>(path) ?? new LibraryListResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new LibraryListResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<OperationResponse> ProcessReturnAsync(int loanId, string condition)
        {
            try
            {
                var response = await _httpClient.PostAsJsonAsync($"library/loans/{loanId}/return", new { condition });
                return await response.Content.ReadFromJsonAsync<OperationResponse>() ?? new OperationResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new OperationResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<LibraryListResponse> GetPenaltiesAsync()
        {
            try
            {
                return await _httpClient.GetFromJsonAsync<LibraryListResponse>("library/penalties") ?? new LibraryListResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new LibraryListResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<OperationResponse> MarkPenaltyPaidAsync(int penaltyId)
        {
            try
            {
                var response = await _httpClient.PatchAsJsonAsync($"library/penalties/{penaltyId}/pay", new { });
                return await response.Content.ReadFromJsonAsync<OperationResponse>() ?? new OperationResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new OperationResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<LibraryListResponse> GetBorrowersAsync()
        {
            try
            {
                return await _httpClient.GetFromJsonAsync<LibraryListResponse>("library/borrowers") ?? new LibraryListResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new LibraryListResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<OperationResponse> SendLibraryNotificationAsync(string title, string message, string audience)
        {
            try
            {
                var response = await _httpClient.PostAsJsonAsync("library/notifications", new { title, message, audience });
                return await response.Content.ReadFromJsonAsync<OperationResponse>() ?? new OperationResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new OperationResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<ReportsSummary> GetReportsSummaryAsync()
        {
            try
            {
                return await _httpClient.GetFromJsonAsync<ReportsSummary>("library/reports/summary") ?? new ReportsSummary { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new ReportsSummary { Success = false, Message = error.Message };
            }
        }

        public async Task<LibrarySettingsResponse> GetLibrarySettingsAsync()
        {
            try
            {
                return await _httpClient.GetFromJsonAsync<LibrarySettingsResponse>("library/settings") ?? new LibrarySettingsResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new LibrarySettingsResponse { Success = false, Message = error.Message };
            }
        }

        public async Task<OperationResponse> SaveLibrarySettingsAsync(LibrarySettingsData settings)
        {
            try
            {
                var response = await _httpClient.PutAsJsonAsync("library/settings", settings);
                return await response.Content.ReadFromJsonAsync<OperationResponse>() ?? new OperationResponse { Success = false, Message = "Invalid response from the server." };
            }
            catch (Exception error)
            {
                return new OperationResponse { Success = false, Message = error.Message };
            }
        }
    }
}
