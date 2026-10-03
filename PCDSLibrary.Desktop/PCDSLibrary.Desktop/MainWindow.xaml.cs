using System.Windows;
using System.Windows.Input;
using PCDSLibrary.Desktop.Models;
using PCDSLibrary.Desktop.Services;
using PCDSLibrary.Desktop.Views;

namespace PCDSLibrary.Desktop
{
    public partial class MainWindow : Window
    {
        private readonly ApiService _apiService = new();

        public MainWindow()
        {
            InitializeComponent();
        }

        private void StaffEmailInput_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key != Key.Enter)
                return;

            e.Handled = true;
            PasswordInput.Focus();
        }

        private void PasswordInput_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key != Key.Enter)
                return;

            e.Handled = true;
            LoginButton_Click(LoginButton, new RoutedEventArgs());
        }

        private async void LoginButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            string email =
                StaffEmailInput.Text.Trim();

            string password =
                PasswordInput.Password;

            ErrorText.Text = "";

            if (string.IsNullOrWhiteSpace(email))
            {
                ErrorText.Text =
                    "Please enter your staff email.";

                StaffEmailInput.Focus();
                return;
            }

            if (string.IsNullOrWhiteSpace(password))
            {
                ErrorText.Text =
                    "Please enter your password.";

                PasswordInput.Focus();
                return;
            }

            LoginButton.IsEnabled = false;
            var result = await _apiService.LoginAsync(email, password);
            LoginButton.IsEnabled = true;

            if (!result.Success)
            {
                ErrorText.Text = result.Message;
                return;
            }

            var role = result.User?.Role?.Trim().ToUpperInvariant() ?? "";
            if (role != "ADMIN" && role != "LIBRARIAN")
            {
                ErrorText.Text = "Desktop access is limited to administrators and librarians.";
                return;
            }

            var dashboardWindow = new LibrarianDashboardWindow(role, result.AccessToken);
            dashboardWindow.Show();
            Close();
        }

        private void ShowRegistration_Click(object sender, RoutedEventArgs e)
        {
            ErrorText.Text = "";
            LoginPanel.Visibility = Visibility.Collapsed;
            RegistrationPanel.Visibility = Visibility.Visible;
        }

        private void ShowLogin_Click(object sender, RoutedEventArgs e)
        {
            RegistrationErrorText.Text = "";
            RegistrationPanel.Visibility = Visibility.Collapsed;
            LoginPanel.Visibility = Visibility.Visible;
        }

        private async void RegisterButton_Click(object sender, RoutedEventArgs e)
        {
            RegistrationErrorText.Text = "";
            var fullName = RegisterNameInput.Text.Trim();
            var staffId = RegisterStaffIdInput.Text.Trim();
            var email = RegisterEmailInput.Text.Trim();
            var password = RegisterPasswordInput.Password;

            if (string.IsNullOrWhiteSpace(fullName) || string.IsNullOrWhiteSpace(staffId) ||
                string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(password) ||
                string.IsNullOrWhiteSpace(StaffInviteCodeInput.Password))
            {
                RegistrationErrorText.Text = "Complete all fields to register.";
                return;
            }

            if (!email.Contains('@'))
            {
                RegistrationErrorText.Text = "Enter a valid work email address.";
                return;
            }

            if (password.Length < 8)
            {
                RegistrationErrorText.Text = "Password must contain at least 8 characters.";
                return;
            }

            if (password != ConfirmPasswordInput.Password)
            {
                RegistrationErrorText.Text = "Passwords do not match.";
                return;
            }

            RegisterButton.IsEnabled = false;
            var result = await _apiService.RegisterStaffAsync(new StaffRegistrationRequest
            {
                FullName = fullName,
                StaffId = staffId,
                Email = email,
                Password = password,
                InviteCode = StaffInviteCodeInput.Password
            });
            RegisterButton.IsEnabled = true;

            if (!result.Success)
            {
                RegistrationErrorText.Text = result.Message;
                return;
            }

            StaffEmailInput.Text = email;
            RegisterNameInput.Clear();
            RegisterStaffIdInput.Clear();
            RegisterEmailInput.Clear();
            RegisterPasswordInput.Clear();
            ConfirmPasswordInput.Clear();
            StaffInviteCodeInput.Clear();
            MessageBox.Show(result.Message, "Registration complete", MessageBoxButton.OK, MessageBoxImage.Information);
            ShowLogin_Click(sender, e);
        }
    }
}
