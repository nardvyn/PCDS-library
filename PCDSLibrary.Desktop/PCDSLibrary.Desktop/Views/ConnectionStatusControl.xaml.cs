using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using PCDSLibrary.Desktop.Services;

namespace PCDSLibrary.Desktop.Views
{
    public partial class ConnectionStatusControl : UserControl
    {
        private readonly ApiService _apiService = new();
        private readonly DispatcherTimer _retryTimer;
        private bool _isChecking;

        public ConnectionStatusControl()
        {
            InitializeComponent();
            _retryTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(10) };
            _retryTimer.Tick += async (_, _) => await CheckConnectionAsync();
            Loaded += async (_, _) =>
            {
                _retryTimer.Start();
                await CheckConnectionAsync();
            };
            Unloaded += (_, _) => _retryTimer.Stop();
        }

        private async Task CheckConnectionAsync()
        {
            if (_isChecking)
                return;

            _isChecking = true;
            ConnectionText.Text = "Checking library server...";
            ConnectionIndicator.Fill = new SolidColorBrush(Color.FromRgb(217, 152, 34));
            ConnectionProgress.Visibility = Visibility.Visible;
            RetryButton.Visibility = Visibility.Collapsed;

            bool isConnected = await _apiService.CheckHealthAsync();
            if (isConnected)
            {
                ConnectionText.Text = "Library server connected";
                ConnectionIndicator.Fill = new SolidColorBrush(Color.FromRgb(35, 132, 82));
                ConnectionProgress.Visibility = Visibility.Collapsed;
                RetryButton.Visibility = Visibility.Collapsed;
            }
            else
            {
                ConnectionText.Text = "No connection. Reconnecting...";
                ConnectionIndicator.Fill = new SolidColorBrush(Color.FromRgb(180, 50, 50));
                ConnectionProgress.Visibility = Visibility.Visible;
                RetryButton.Visibility = Visibility.Visible;
            }

            _isChecking = false;
        }

        private async void RetryButton_Click(object sender, RoutedEventArgs e)
        {
            await CheckConnectionAsync();
        }
    }
}