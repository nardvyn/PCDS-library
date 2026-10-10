using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using PCDSLibrary.Desktop.Models;
using PCDSLibrary.Desktop.Services;

namespace PCDSLibrary.Desktop.Views
{
    public partial class LibrarianDashboardWindow : Window
    {
        private readonly string _currentRole;
        private readonly ApiService _apiService;
        private DataGrid _booksCatalogGrid = null!;
        private TextBlock _booksCatalogStatus = null!;
        private Border _bookDetailsPanel = null!;
        private Image _bookCoverImage = null!;
        private TextBlock _bookCoverStatus = null!;
        private TextBlock _bookDetailsContent = null!;
        private TextBox _studentLoanDaysInput = null!;
        private TextBox _teacherLoanDaysInput = null!;
        private TextBox _dailyPenaltyInput = null!;
        private CheckBox _notificationsInput = null!;
        private DispatcherTimer? _pendingUsersTimer;
        private DispatcherTimer? _pendingRequestsTimer;
        private TextBlock _dashboardRefreshStatus = null!;
        private TextBlock _totalBooksValue = null!;
        private TextBlock _availableBooksValue = null!;
        private TextBlock _borrowedBooksValue = null!;
        private TextBlock _pendingRequestsValue = null!;
        private TextBlock _approvedRequestsValue = null!;
        private TextBlock _overdueBooksValue = null!;
        private TextBlock _borrowersValue = null!;
        private TextBlock _unpaidPenaltiesValue = null!;

        public LibrarianDashboardWindow()
        {
            InitializeComponent();

            _currentRole = "ADMIN";
            _apiService = new ApiService();

            ConfigureRoleAccess();
            LoadDashboard();
        }

        public LibrarianDashboardWindow(string role, string accessToken = "")
        {
            InitializeComponent();

            _currentRole = string.IsNullOrWhiteSpace(role)
                ? "LIBRARIAN"
                : role.Trim().ToUpperInvariant();
            _apiService = new ApiService(accessToken);

            ConfigureRoleAccess();
            LoadDashboard();
        }

        private void ConfigureRoleAccess()
        {
            bool isAdmin = _currentRole == "ADMIN";

            SidebarRoleText.Text = _currentRole;
            HeaderRoleText.Text = _currentRole;
            UserManagementButton.IsEnabled = isAdmin;
            AuditLogsButton.IsEnabled = isAdmin;

            UserManagementButton.Opacity = isAdmin ? 1 : 0.45;
            AuditLogsButton.Opacity = isAdmin ? 1 : 0.45;
            SettingsButton.Opacity = isAdmin ? 1 : 0.45;
            PendingUsersBadge.Visibility = Visibility.Collapsed;
            PendingRequestsBadge.Visibility = Visibility.Collapsed;
            _ = UpdatePendingRequestsBadgeAsync();
            _pendingRequestsTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(30) };
            _pendingRequestsTimer.Tick += async (_, _) => await UpdatePendingRequestsBadgeAsync();
            _pendingRequestsTimer.Start();
            if (isAdmin)
            {
                _ = UpdatePendingUsersBadgeAsync();
                _pendingUsersTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(30) };
                _pendingUsersTimer.Tick += async (_, _) => await UpdatePendingUsersBadgeAsync();
                _pendingUsersTimer.Start();
            }
        }

        private async Task UpdatePendingUsersBadgeAsync()
        {
            var result = await _apiService.GetVerificationProfilesAsync();
            if (!result.Success)
                return;

            var pendingCount = result.Profiles.Count(profile => profile.VerificationStatus == "PENDING_VERIFICATION");
            PendingUsersCountText.Text = pendingCount > 99 ? "99+" : pendingCount.ToString();
            PendingUsersBadge.Visibility = pendingCount > 0 ? Visibility.Visible : Visibility.Collapsed;
            PendingUsersButtonTooltip(pendingCount);
        }

        private async Task UpdatePendingRequestsBadgeAsync()
        {
            var result = await _apiService.GetBorrowRequestsAsync();
            if (!result.Success)
                return;

            var pendingCount = result.Requests.Count;
            PendingRequestsCountText.Text = pendingCount > 99 ? "99+" : pendingCount.ToString();
            PendingRequestsBadge.Visibility = pendingCount > 0 ? Visibility.Visible : Visibility.Collapsed;
            BorrowRequestsButton.ToolTip = pendingCount == 0
                ? "No borrow requests are waiting for review."
                : $"{pendingCount} borrow request(s) waiting for review.";
        }

        private void PendingUsersButtonTooltip(int pendingCount)
        {
            UserManagementButton.ToolTip = pendingCount == 0
                ? "No borrower profiles are waiting for verification."
                : $"{pendingCount} borrower profile(s) waiting for verification.";
        }

        private void LoadDashboard()
        {
            Title = "PCDS Library - Dashboard";
            SetActiveButton(DashboardButton);

            var content = new StackPanel();
            var headingGrid = new Grid();
            headingGrid.ColumnDefinitions.Add(new ColumnDefinition());
            headingGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            headingGrid.Children.Add(CreateHeading("Dashboard", "Overview of library operations and request activities"));
            var refreshPanel = new StackPanel { HorizontalAlignment = HorizontalAlignment.Right };
            var refreshButton = CreateRequestButton("Refresh", "#00899A");
            refreshButton.Margin = new Thickness(0, 4, 0, 0);
            refreshButton.Click += async (_, _) => await LoadDashboardSummaryAsync(refreshButton);
            refreshPanel.Children.Add(refreshButton);
            _dashboardRefreshStatus = new TextBlock { Margin = new Thickness(0, 5, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")), HorizontalAlignment = HorizontalAlignment.Right };
            refreshPanel.Children.Add(_dashboardRefreshStatus);
            Grid.SetColumn(refreshPanel, 1);
            headingGrid.Children.Add(refreshPanel);
            content.Children.Add(new Border
            {
                Padding = new Thickness(21, 18, 21, 18),
                Background = Brushes.White,
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(12),
                Child = headingGrid
            });

            var metrics = new UniformGrid
            {
                Columns = 4,
                Rows = 2,
                Margin = new Thickness(0, 13, 0, 0)
            };

            metrics.Children.Add(CreateMetric("Total Books", "—", "#12363D", value => _totalBooksValue = value));
            metrics.Children.Add(CreateMetric("Available Books", "—", "#12363D", value => _availableBooksValue = value));
            metrics.Children.Add(CreateMetric("Borrowed Books", "—", "#12363D", value => _borrowedBooksValue = value));
            metrics.Children.Add(CreateMetric("Pending Requests", "—", "#12363D", value => _pendingRequestsValue = value));
            metrics.Children.Add(CreateMetric("Approved Requests", "—", "#12363D", value => _approvedRequestsValue = value));
            metrics.Children.Add(CreateMetric("Overdue Books", "—", "#B42318", value => _overdueBooksValue = value));
            metrics.Children.Add(CreateMetric("Students + Teachers", "—", "#12363D", value => _borrowersValue = value));
            metrics.Children.Add(CreateMetric("Unpaid Penalties", "—", "#A11D1D", value => _unpaidPenaltiesValue = value));

            content.Children.Add(metrics);
            MainContent.Content = content;
            _ = LoadDashboardSummaryAsync();
        }

        private async Task LoadDashboardSummaryAsync(Button? refreshButton = null)
        {
            if (refreshButton != null)
                refreshButton.IsEnabled = false;
            _dashboardRefreshStatus.Text = "Updating...";
            var result = await _apiService.GetReportsSummaryAsync();
            if (refreshButton != null)
                refreshButton.IsEnabled = true;
            if (!result.Success)
            {
                _dashboardRefreshStatus.Text = result.Message;
                return;
            }

            _totalBooksValue.Text = result.TotalBooks.ToString("N0");
            _availableBooksValue.Text = result.AvailableBooks.ToString("N0");
            _borrowedBooksValue.Text = result.BorrowedBooks.ToString("N0");
            _pendingRequestsValue.Text = result.PendingRequests.ToString("N0");
            _approvedRequestsValue.Text = result.ApprovedRequests.ToString("N0");
            _overdueBooksValue.Text = result.OverdueBooks.ToString("N0");
            _borrowersValue.Text = result.Borrowers.ToString("N0");
            _unpaidPenaltiesValue.Text = $"₱{result.UnpaidPenalties:N2}";
            _dashboardRefreshStatus.Text = $"Updated {DateTime.Now:hh:mm tt}";
        }

        private void ShowModuleContent(
            string title,
            string description,
            string icon,
            Button selectedButton)
        {
            Title = $"PCDS Library - {title}";
            SetActiveButton(selectedButton);

            var content = new StackPanel();
            content.Children.Add(CreateHeading(title, description));

            if (title == "Manage Books")
            {
                content.Children.Add(CreateManageBooksContent());
                MainContent.Content = content;
                return;
            }

            if (title == "Settings")
            {
                content.Children.Add(CreateSettingsContent());
                MainContent.Content = content;
                return;
            }

            if (title == "Borrow Requests")
            {
                content.Children.Add(CreateBorrowRequestsContent());
                MainContent.Content = content;
                return;
            }

            if (title == "User Management")
            {
                content.Children.Add(CreateVerificationContent());
                MainContent.Content = content;
                return;
            }

            if (title == "Audit Logs")
            {
                content.Children.Add(CreateAuditLogsContent());
                MainContent.Content = content;
                return;
            }

            if (title == "Active Loans")
            {
                content.Children.Add(CreateLoanListContent(false, false));
                MainContent.Content = content;
                return;
            }

            if (title == "Book Returns")
            {
                content.Children.Add(CreateLoanListContent(false, true));
                MainContent.Content = content;
                return;
            }

            if (title == "Overdue Books")
            {
                content.Children.Add(CreateLoanListContent(true, true));
                MainContent.Content = content;
                return;
            }

            if (title == "Penalties")
            {
                content.Children.Add(CreatePenaltiesContent());
                MainContent.Content = content;
                return;
            }

            if (title == "Borrowers")
            {
                content.Children.Add(CreateBorrowersContent());
                MainContent.Content = content;
                return;
            }

            if (title == "Notifications")
            {
                content.Children.Add(CreateNotificationComposer());
                MainContent.Content = content;
                return;
            }

            if (title == "Reports")
            {
                content.Children.Add(CreateReportsContent());
                MainContent.Content = content;
                return;
            }

            var modulePanel = new Border
            {
                Margin = new Thickness(0, 24, 0, 0),
                Padding = new Thickness(30),
                Background = Brushes.White,
                CornerRadius = new CornerRadius(12)
            };

            var moduleContent = new StackPanel
            {
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center
            };
            moduleContent.Children.Add(new TextBlock
            {
                Text = icon,
                FontSize = 44,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            moduleContent.Children.Add(new TextBlock
            {
                Text = $"{title} Module",
                Margin = new Thickness(0, 15, 0, 0),
                FontSize = 20,
                FontWeight = FontWeights.SemiBold,
                HorizontalAlignment = HorizontalAlignment.Center
            });
            moduleContent.Children.Add(new TextBlock
            {
                Text = "This module is ready for its API and database functions.",
                Margin = new Thickness(0, 8, 0, 0),
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")),
                HorizontalAlignment = HorizontalAlignment.Center
            });

            modulePanel.Child = moduleContent;
            content.Children.Add(modulePanel);
            MainContent.Content = content;
        }

        private StackPanel CreateLoanListContent(bool overdueOnly, bool allowReturn)
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0) };
            var status = new TextBlock { MinHeight = 24, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) };
            var list = new StackPanel();
            var scroll = new ScrollViewer { Content = list, MaxHeight = 560, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
            var refresh = CreateRequestButton("Refresh", "#00899A");
            refresh.Click += async (_, _) => await LoadLoanListAsync(list, status, overdueOnly, allowReturn);
            panel.Children.Add(refresh);
            panel.Children.Add(status);
            panel.Children.Add(scroll);
            _ = LoadLoanListAsync(list, status, overdueOnly, allowReturn);
            return panel;
        }

        private async Task LoadLoanListAsync(StackPanel list, TextBlock status, bool overdueOnly, bool allowReturn)
        {
            status.Text = "Loading loan records...";
            list.Children.Clear();
            var result = await _apiService.GetLoansAsync(overdueOnly);
            list.Children.Clear();
            if (!result.Success)
            {
                status.Text = result.Message;
                return;
            }
            status.Text = $"{result.Loans.Count} record(s)";
            if (result.Loans.Count == 0)
            {
                list.Children.Add(CreateRequestMessage(overdueOnly ? "No overdue books." : "No active loans." , "#547177"));
                return;
            }
            foreach (var loan in result.Loans)
            {
                var row = CreateLibraryRow(
                    loan.BookTitle,
                    $"{loan.BorrowerName} ({loan.SchoolId}) • {loan.Role}",
                    $"Due {FormatRequestDate(loan.DueDate)} • Accession {loan.AccessionNumber}{(overdueOnly ? $" • {loan.LateDays} late day(s)" : "")}",
                    allowReturn ? "Process return" : null,
                    async () => await PromptAndProcessReturnAsync(loan.LoanId, list, status, overdueOnly, allowReturn)
                );
                list.Children.Add(row);
            }
        }

        private async Task PromptAndProcessReturnAsync(int loanId, StackPanel list, TextBlock status, bool overdueOnly, bool allowReturn)
        {
            var condition = PromptReturnCondition();
            if (condition == null)
                return;
            var result = await _apiService.ProcessReturnAsync(loanId, condition);
            MessageBox.Show(result.Message, result.Success ? "Return processed" : "Return failed", MessageBoxButton.OK, result.Success ? MessageBoxImage.Information : MessageBoxImage.Error);
            if (result.Success)
                await LoadLoanListAsync(list, status, overdueOnly, allowReturn);
        }

        private string? PromptReturnCondition()
        {
            var dialog = new Window
            {
                Title = "Book return condition",
                Owner = this,
                Width = 360,
                Height = 190,
                WindowStartupLocation = WindowStartupLocation.CenterOwner,
                ResizeMode = ResizeMode.NoResize,
                Background = Brushes.White
            };
            var layout = new StackPanel { Margin = new Thickness(20) };
            layout.Children.Add(new TextBlock { Text = "Select the condition of the returned book:", Margin = new Thickness(0, 0, 0, 10), FontSize = 14, FontWeight = FontWeights.SemiBold });
            var condition = new ComboBox { Height = 34, SelectedIndex = 0, ItemsSource = new[] { "GOOD", "DAMAGED", "LOST" } };
            layout.Children.Add(condition);
            var actions = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 16, 0, 0) };
            string? selection = null;
            var confirm = CreateRequestButton("Continue", "#00899A");
            confirm.Click += (_, _) => { selection = condition.SelectedItem?.ToString(); dialog.DialogResult = true; };
            var cancel = CreateRequestButton("Cancel", "#547177");
            cancel.Click += (_, _) => dialog.DialogResult = false;
            actions.Children.Add(confirm);
            actions.Children.Add(cancel);
            layout.Children.Add(actions);
            dialog.Content = layout;
            dialog.ShowDialog();
            return selection;
        }

        private StackPanel CreatePenaltiesContent()
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0) };
            var status = new TextBlock { MinHeight = 24, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) };
            var list = new StackPanel();
            var refresh = CreateRequestButton("Refresh", "#00899A");
            refresh.Click += async (_, _) => await LoadPenaltiesAsync(list, status);
            panel.Children.Add(refresh);
            panel.Children.Add(status);
            panel.Children.Add(new ScrollViewer { Content = list, MaxHeight = 560, VerticalScrollBarVisibility = ScrollBarVisibility.Auto });
            _ = LoadPenaltiesAsync(list, status);
            return panel;
        }

        private async Task LoadPenaltiesAsync(StackPanel list, TextBlock status)
        {
            list.Children.Clear();
            status.Text = "Loading penalties...";
            var result = await _apiService.GetPenaltiesAsync();
            if (!result.Success) { status.Text = result.Message; return; }
            status.Text = $"{result.Penalties.Count} penalty record(s)";
            if (result.Penalties.Count == 0) { list.Children.Add(CreateRequestMessage("No penalties recorded.", "#547177")); return; }
            foreach (var penalty in result.Penalties)
            {
                var row = CreateLibraryRow(penalty.BookTitle, $"{penalty.BorrowerName} ({penalty.SchoolId}) • {penalty.LateDays} late day(s)", $"PHP {penalty.Amount:0.00} • {penalty.Status} • {FormatRequestDate(penalty.CreatedAt)}", penalty.Status == "UNPAID" ? "Mark paid" : null, async () =>
                {
                    var response = await _apiService.MarkPenaltyPaidAsync(penalty.PenaltyId);
                    MessageBox.Show(response.Message, "Penalty payment", MessageBoxButton.OK, response.Success ? MessageBoxImage.Information : MessageBoxImage.Error);
                    if (response.Success) await LoadPenaltiesAsync(list, status);
                });
                list.Children.Add(row);
            }
        }

        private StackPanel CreateBorrowersContent()
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0) };
            var status = new TextBlock { MinHeight = 24, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) };
            var grid = new DataGrid { AutoGenerateColumns = false, IsReadOnly = true, CanUserAddRows = false, RowHeaderWidth = 0, RowHeight = 30, ColumnHeaderHeight = 32, FontSize = 13, MaxHeight = 560, Background = Brushes.White };
            grid.Columns.Add(new DataGridTextColumn { Header = "Name", Binding = new Binding(nameof(BorrowerData.FullName)), Width = 180 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Type", Binding = new Binding(nameof(BorrowerData.Role)), Width = 90 });
            grid.Columns.Add(new DataGridTextColumn { Header = "School ID", Binding = new Binding(nameof(BorrowerData.SchoolId)), Width = 125 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Course / Dept", Binding = new Binding(nameof(BorrowerData.Course)), Width = 150 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Section", Binding = new Binding(nameof(BorrowerData.Section)), Width = 100 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Verification", Binding = new Binding(nameof(BorrowerData.VerificationStatus)), Width = 170 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Account", Binding = new Binding(nameof(BorrowerData.AccountStatus)), Width = 100 });
            var refresh = CreateRequestButton("Refresh", "#00899A");
            refresh.Click += async (_, _) => await LoadBorrowersAsync(grid, status);
            panel.Children.Add(refresh);
            panel.Children.Add(status);
            panel.Children.Add(grid);
            _ = LoadBorrowersAsync(grid, status);
            return panel;
        }

        private async Task LoadBorrowersAsync(DataGrid grid, TextBlock status)
        {
            status.Text = "Loading borrowers...";
            var result = await _apiService.GetBorrowersAsync();
            grid.ItemsSource = result.Success ? result.Borrowers : null;
            status.Text = result.Success ? $"{result.Borrowers.Count} borrower(s)" : result.Message;
        }

        private StackPanel CreateNotificationComposer()
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0), MaxWidth = 720 };
            panel.Children.Add(new TextBlock { Text = "Send an announcement to student and teacher accounts.", Margin = new Thickness(0, 0, 0, 16), FontSize = 13, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            panel.Children.Add(new TextBlock { Text = "Audience", FontWeight = FontWeights.SemiBold });
            var audience = new ComboBox { Height = 38, Margin = new Thickness(0, 5, 0, 14), ItemsSource = new[] { "ALL", "STUDENT", "TEACHER" }, SelectedIndex = 0 };
            panel.Children.Add(audience);
            panel.Children.Add(new TextBlock { Text = "Title", FontWeight = FontWeights.SemiBold });
            var title = new TextBox { Height = 38, Margin = new Thickness(0, 5, 0, 14), Padding = new Thickness(10, 8, 10, 8) };
            panel.Children.Add(title);
            panel.Children.Add(new TextBlock { Text = "Message", FontWeight = FontWeights.SemiBold });
            var message = new TextBox { Height = 130, AcceptsReturn = true, TextWrapping = TextWrapping.Wrap, VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Margin = new Thickness(0, 5, 0, 14), Padding = new Thickness(10) };
            panel.Children.Add(message);
            var status = new TextBlock { MinHeight = 24, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) };
            var send = CreateRequestButton("Send notification", "#00899A");
            send.Click += async (_, _) =>
            {
                if (string.IsNullOrWhiteSpace(title.Text) || string.IsNullOrWhiteSpace(message.Text)) { status.Text = "Enter both a title and message."; return; }
                send.IsEnabled = false;
                var response = await _apiService.SendLibraryNotificationAsync(title.Text.Trim(), message.Text.Trim(), audience.SelectedItem?.ToString() ?? "ALL");
                send.IsEnabled = true;
                status.Text = response.Message;
                if (response.Success) { title.Clear(); message.Clear(); }
            };
            panel.Children.Add(send);
            panel.Children.Add(status);
            return panel;
        }

        private StackPanel CreateReportsContent()
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0) };
            var status = new TextBlock { MinHeight = 24, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) };
            var grid = new UniformGrid { Columns = 3, Rows = 3, Margin = new Thickness(-8, 8, -8, 0) };
            var refresh = CreateRequestButton("Refresh report", "#00899A");
            refresh.Click += async (_, _) => await LoadReportsAsync(grid, status, refresh);
            panel.Children.Add(refresh);
            panel.Children.Add(status);
            panel.Children.Add(grid);
            _ = LoadReportsAsync(grid, status, refresh);
            return panel;
        }

        private async Task LoadReportsAsync(UniformGrid grid, TextBlock status, Button refresh)
        {
            refresh.IsEnabled = false;
            status.Text = "Generating summary...";
            var report = await _apiService.GetReportsSummaryAsync();
            refresh.IsEnabled = true;
            grid.Children.Clear();
            if (!report.Success) { status.Text = report.Message; return; }
            status.Text = "Current library operations summary";
            grid.Children.Add(CreateMetric("Total book copies", report.TotalBooks.ToString()));
            grid.Children.Add(CreateMetric("Available copies", report.AvailableBooks.ToString()));
            grid.Children.Add(CreateMetric("Active loans", report.BorrowedBooks.ToString()));
            grid.Children.Add(CreateMetric("Pending requests", report.PendingRequests.ToString()));
            grid.Children.Add(CreateMetric("Overdue books", report.OverdueBooks.ToString(), "#B42318"));
            grid.Children.Add(CreateMetric("Borrowers", report.Borrowers.ToString()));
            grid.Children.Add(CreateMetric("Unpaid penalties", $"PHP {report.UnpaidPenalties:0.00}", "#A11D1D"));
        }

        private Border CreateLibraryRow(string title, string subtitle, string metadata, string? actionLabel, Func<Task>? action)
        {
            var card = new Border { Margin = new Thickness(0, 0, 0, 10), Padding = new Thickness(15), Background = Brushes.White, CornerRadius = new CornerRadius(9), BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")), BorderThickness = new Thickness(1) };
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition());
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            var details = new StackPanel();
            details.Children.Add(new TextBlock { Text = title, FontSize = 14, FontWeight = FontWeights.SemiBold, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12363D")) });
            details.Children.Add(new TextBlock { Text = subtitle, Margin = new Thickness(0, 4, 0, 0), FontSize = 12, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            details.Children.Add(new TextBlock { Text = metadata, Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#789094")) });
            grid.Children.Add(details);
            if (actionLabel != null && action != null)
            {
                var button = CreateRequestButton(actionLabel, "#00899A");
                button.VerticalAlignment = VerticalAlignment.Center;
                button.Click += async (_, _) => { button.IsEnabled = false; await action(); button.IsEnabled = true; };
                Grid.SetColumn(button, 1);
                grid.Children.Add(button);
            }
            card.Child = grid;
            return card;
        }

        private StackPanel CreateAuditLogsContent()
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0) };
            panel.Children.Add(new TextBlock
            {
                Text = "Recent administrative and library actions. Entries are read-only and retained for accountability.",
                Margin = new Thickness(0, 0, 0, 14),
                FontSize = 13,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177"))
            });

            var status = new TextBlock { MinHeight = 24, FontSize = 12, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) };
            var refreshButton = CreateRequestButton("Refresh", "#00899A");
            var toolbar = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 10) };
            toolbar.Children.Add(refreshButton);
            toolbar.Children.Add(status);
            panel.Children.Add(toolbar);

            var grid = new DataGrid
            {
                AutoGenerateColumns = false,
                IsReadOnly = true,
                CanUserAddRows = false,
                CanUserDeleteRows = false,
                HeadersVisibility = DataGridHeadersVisibility.Column,
                GridLinesVisibility = DataGridGridLinesVisibility.Horizontal,
                RowHeaderWidth = 0,
                MaxHeight = 560,
                Background = Brushes.White,
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1"))
            };
            grid.Columns.Add(new DataGridTextColumn { Header = "Time", Binding = new Binding(nameof(AuditLogData.TimestampDisplay)), Width = 165 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Actor", Binding = new Binding(nameof(AuditLogData.ActorName)), Width = 150 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Role", Binding = new Binding(nameof(AuditLogData.ActorRole)), Width = 85 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Action", Binding = new Binding(nameof(AuditLogData.Action)), Width = 185 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Record", Binding = new Binding(nameof(AuditLogData.RecordDisplay)), Width = 145 });
            grid.Columns.Add(new DataGridTextColumn { Header = "Details", Binding = new Binding(nameof(AuditLogData.Details)), Width = new DataGridLength(1, DataGridLengthUnitType.Star) });
            refreshButton.Click += async (_, _) => await LoadAuditLogsAsync(grid, status, refreshButton);
            panel.Children.Add(grid);
            _ = LoadAuditLogsAsync(grid, status, refreshButton);
            return panel;
        }

        private async Task LoadAuditLogsAsync(DataGrid grid, TextBlock status, Button refreshButton)
        {
            refreshButton.IsEnabled = false;
            status.Text = "Loading audit history...";
            var result = await _apiService.GetAuditLogsAsync();
            refreshButton.IsEnabled = true;
            if (!result.Success)
            {
                status.Text = result.Message;
                grid.ItemsSource = null;
                return;
            }
            grid.ItemsSource = result.Logs;
            status.Text = $"Showing {result.Logs.Count} recent entries";
        }

        private StackPanel CreateVerificationContent()
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0) };
            panel.Children.Add(new TextBlock
            {
                Text = "Review borrower details, verify uploaded IDs, and manage account access.",
                Margin = new Thickness(0, 0, 0, 16),
                FontSize = 13,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177"))
            });
            var list = new StackPanel();
            panel.Children.Add(new ScrollViewer
            {
                Content = list,
                MaxHeight = 520,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                HorizontalScrollBarVisibility = ScrollBarVisibility.Disabled
            });
            _ = LoadVerificationProfilesAsync(list);
            return panel;
        }

        private async Task LoadVerificationProfilesAsync(StackPanel list)
        {
            list.Children.Clear();
            list.Children.Add(CreateRequestMessage("Loading verification profiles...", "#547177"));
            var result = await _apiService.GetVerificationProfilesAsync();
            list.Children.Clear();
            if (!result.Success)
            {
                list.Children.Add(CreateRequestMessage(result.Message, "#B42318"));
                return;
            }
            if (result.Profiles.Count == 0)
            {
                UpdatePendingUsersBadge(result.Profiles);
                list.Children.Add(CreateRequestMessage("No user accounts found.", "#547177"));
                return;
            }
            UpdatePendingUsersBadge(result.Profiles);
            foreach (var profile in result.Profiles)
                list.Children.Add(CreateVerificationRow(profile, list));
        }

        private void UpdatePendingUsersBadge(IReadOnlyCollection<VerificationProfileData> profiles)
        {
            var pendingCount = profiles.Count(profile => profile.VerificationStatus == "PENDING_VERIFICATION");
            PendingUsersCountText.Text = pendingCount > 99 ? "99+" : pendingCount.ToString();
            PendingUsersBadge.Visibility = pendingCount > 0 ? Visibility.Visible : Visibility.Collapsed;
            PendingUsersButtonTooltip(pendingCount);
        }

        private Border CreateVerificationRow(VerificationProfileData profile, StackPanel list)
        {
            var card = new Border
            {
                Margin = new Thickness(0, 0, 0, 10),
                Padding = new Thickness(16),
                Background = Brushes.White,
                CornerRadius = new CornerRadius(10),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")),
                BorderThickness = new Thickness(1)
            };
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition());
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(320) });
            var details = new StackPanel();
            details.Children.Add(new TextBlock { Text = profile.FullName, FontSize = 15, FontWeight = FontWeights.SemiBold, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12363D")) });
            details.Children.Add(new TextBlock { Text = $"{profile.Role} • {profile.AccountStatus} • {profile.VerificationStatus}", Margin = new Thickness(0, 5, 0, 0), FontSize = 12, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            details.Children.Add(new TextBlock { Text = $"School/Employee ID: {profile.SchoolIdNumber ?? "Not provided"}", Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            details.Children.Add(new TextBlock { Text = profile.Email, Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#789094")) });
            var academicDetails = profile.Role == "TEACHER"
                ? profile.Department
                : string.Join(" • ", new[] { profile.Course, profile.YearLevel, profile.Section }.Where(value => !string.IsNullOrWhiteSpace(value)));
            if (!string.IsNullOrWhiteSpace(academicDetails))
                details.Children.Add(new TextBlock { Text = academicDetails, Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            if (!string.IsNullOrWhiteSpace(profile.ContactNumber))
                details.Children.Add(new TextBlock { Text = $"Phone: {profile.ContactNumber}", Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            if (!string.IsNullOrWhiteSpace(profile.Address))
                details.Children.Add(new TextBlock { Text = $"Address: {profile.Address}", Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            if (profile.Role is "STUDENT" or "TEACHER" && !profile.SchoolIdImageAvailable)
                details.Children.Add(new TextBlock { Text = "School ID image unavailable. Ask the borrower to resubmit their profile.", Margin = new Thickness(0, 5, 0, 0), FontSize = 11, FontWeight = FontWeights.SemiBold, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#A6533D")), TextWrapping = TextWrapping.Wrap });
            details.Children.Add(new TextBlock { Text = $"Registered: {FormatRequestDate(profile.CreatedAt ?? "")}", Margin = new Thickness(0, 3, 0, 0), FontSize = 10, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#789094")) });
            grid.Children.Add(details);
            var actions = new WrapPanel { VerticalAlignment = VerticalAlignment.Center, HorizontalAlignment = HorizontalAlignment.Right };
            if (profile.ProfileId.HasValue && profile.SchoolIdImageAvailable)
            {
                var viewButton = CreateRequestButton("View ID", "#00899A");
                viewButton.Tag = profile.ProfileId.Value;
                viewButton.Click += ViewSchoolIdButton_Click;
                actions.Children.Add(viewButton);
            }
            if (profile.ProfileId.HasValue && (profile.Role == "STUDENT" || profile.Role == "TEACHER"))
            {
                if (profile.ProfileComplete && profile.VerificationStatus is "PENDING_VERIFICATION" or "REJECTED" or "SUSPENDED")
                    AddVerificationAction(actions, "Verify", "VERIFIED", "#18724A", profile, list);
                if (profile.VerificationStatus == "PENDING_VERIFICATION")
                    AddVerificationAction(actions, "Reject", "REJECTED", "#A6533D", profile, list);
                if (profile.VerificationStatus != "SUSPENDED")
                    AddVerificationAction(actions, "Suspend", "SUSPENDED", "#A11D1D", profile, list);
            }
            if (profile.Role == "STUDENT" || profile.Role == "TEACHER")
            {
                var deleteButton = CreateRequestButton("Delete", "#7F1D1D");
                deleteButton.Tag = new DeleteBorrowerAction(profile.UserId, list, profile.FullName);
                deleteButton.Click += DeleteBorrowerButton_Click;
                actions.Children.Add(deleteButton);
            }
            if (actions.Children.Count == 0)
                actions.Children.Add(new TextBlock { Text = "Staff account", Margin = new Thickness(8), VerticalAlignment = VerticalAlignment.Center, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            Grid.SetColumn(actions, 1);
            grid.Children.Add(actions);
            card.Child = grid;
            return card;
        }

        private void AddVerificationAction(WrapPanel actions, string label, string status, string color, VerificationProfileData profile, StackPanel list)
        {
            var button = CreateRequestButton(label, color);
            button.Tag = new VerificationAction(profile.ProfileId ?? 0, status, list);
            button.Click += ProcessVerificationAsync;
            actions.Children.Add(button);
        }

        private async void ProcessVerificationAsync(object sender, RoutedEventArgs e)
        {
            if (sender is not Button button || button.Tag is not VerificationAction action)
                return;
            button.IsEnabled = false;
            var result = await _apiService.UpdateVerificationProfileAsync(action.ProfileId, action.Status);
            if (!result.Success)
                MessageBox.Show(result.Message, "Profile Verification", MessageBoxButton.OK, MessageBoxImage.Error);
            else
                await LoadVerificationProfilesAsync(action.List);
        }

        private async void ViewSchoolIdButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is not Button button || button.Tag is not int profileId)
                return;

            button.IsEnabled = false;
            var result = await _apiService.GetSchoolIdImageAsync(profileId);
            button.IsEnabled = true;
            if (result.Image == null)
            {
                MessageBox.Show(result.Error, "School ID", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var image = new BitmapImage();
            using (var stream = new MemoryStream(result.Image))
            {
                image.BeginInit();
                image.CacheOption = BitmapCacheOption.OnLoad;
                image.StreamSource = stream;
                image.EndInit();
                image.Freeze();
            }

            var content = new StackPanel();
            content.Children.Add(CreateHeading("School ID image", "Privately loaded from the verification service."));
            var backButton = CreateRequestButton("Back to users", "#00899A");
            backButton.Margin = new Thickness(0, 18, 0, 12);
            backButton.HorizontalAlignment = HorizontalAlignment.Left;
            backButton.Click += (_, _) => ShowModuleContent("User Management", "Manage user accounts and verify uploaded school IDs.", "", UserManagementButton);
            content.Children.Add(backButton);

            var imageFrame = new Border
            {
                Padding = new Thickness(12),
                Background = Brushes.White,
                CornerRadius = new CornerRadius(10),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")),
                BorderThickness = new Thickness(1)
            };
            imageFrame.Child = new Image
            {
                Source = image,
                Stretch = System.Windows.Media.Stretch.Uniform,
                MaxHeight = 540,
                MaxWidth = 850
            };
            content.Children.Add(imageFrame);
            MainContent.Content = content;
        }

        private async void DeleteBorrowerButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is not Button button || button.Tag is not DeleteBorrowerAction action)
                return;

            var confirmation = MessageBox.Show(
                $"Permanently delete {action.FullName} and their profile, borrow requests, notifications, and uploaded ID image? This cannot be undone.",
                "Delete borrower account",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning
            );
            if (confirmation != MessageBoxResult.Yes)
                return;

            button.IsEnabled = false;
            var result = await _apiService.DeleteBorrowerAsync(action.UserId);
            if (!result.Success)
            {
                button.IsEnabled = true;
                MessageBox.Show(result.Message, "Delete account", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }
            await LoadVerificationProfilesAsync(action.List);
        }

        private StackPanel CreateBorrowRequestsContent()
        {
            var panel = new StackPanel { Margin = new Thickness(0, 24, 0, 0) };
            panel.Children.Add(new TextBlock
            {
                Text = "Pending requests are submitted by students and teachers.",
                Margin = new Thickness(0, 0, 0, 16),
                FontSize = 13,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177"))
            });
            var list = new StackPanel();
            panel.Children.Add(list);
            _ = LoadBorrowRequestsAsync(list);
            return panel;
        }

        private async Task LoadBorrowRequestsAsync(StackPanel list)
        {
            list.Children.Clear();
            list.Children.Add(new TextBlock
            {
                Text = "Loading pending requests...",
                Padding = new Thickness(20),
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177"))
            });

            var result = await _apiService.GetBorrowRequestsAsync();
            list.Children.Clear();
            if (!result.Success)
            {
                list.Children.Add(CreateRequestMessage(result.Message, "#B42318"));
                return;
            }
            var currentPendingCount = result.Requests.Count;
            PendingRequestsCountText.Text = currentPendingCount > 99 ? "99+" : currentPendingCount.ToString();
            PendingRequestsBadge.Visibility = currentPendingCount > 0 ? Visibility.Visible : Visibility.Collapsed;
            if (result.Requests.Count == 0)
            {
                list.Children.Add(CreateRequestMessage("No pending borrow requests.", "#547177"));
                return;
            }

            foreach (var request in result.Requests)
                list.Children.Add(CreateRequestRow(request, list));
        }

        private Border CreateRequestRow(BorrowRequestData request, StackPanel list)
        {
            var card = new Border
            {
                Margin = new Thickness(0, 0, 0, 10),
                Padding = new Thickness(16),
                Background = Brushes.White,
                CornerRadius = new CornerRadius(10),
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")),
                BorderThickness = new Thickness(1)
            };
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition());
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            var details = new StackPanel();
            details.Children.Add(new TextBlock { Text = request.BookTitle, FontSize = 15, FontWeight = FontWeights.SemiBold, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12363D")) });
            details.Children.Add(new TextBlock { Text = $"Requested by {request.BorrowerName} ({request.SchoolId})", Margin = new Thickness(0, 5, 0, 0), FontSize = 12, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            details.Children.Add(new TextBlock { Text = $"Call number: {request.CallNumber} • Accession: {request.AccessionNumber}", Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            if (!string.IsNullOrWhiteSpace(request.Author))
                details.Children.Add(new TextBlock { Text = $"Author: {request.Author}", Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) });
            details.Children.Add(new TextBlock { Text = FormatRequestDate(request.RequestedAt), Margin = new Thickness(0, 3, 0, 0), FontSize = 11, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#789094")) });
            grid.Children.Add(details);
            var actions = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            if (request.HasBookImage)
            {
                var photoButton = CreateRequestButton("View photo", "#00899A");
                photoButton.Tag = request.RequestId;
                photoButton.Click += ViewBorrowRequestPhoto_Click;
                actions.Children.Add(photoButton);
            }
            var approve = CreateRequestButton("Approve", "#18724A");
            approve.Tag = request.RequestId;
            approve.Click += (sender, args) => ProcessBorrowRequestAsync(sender, args, "APPROVED", list);
            actions.Children.Add(approve);
            var reject = CreateRequestButton("Reject", "#A11D1D");
            reject.Tag = request.RequestId;
            reject.Click += (sender, args) => ProcessBorrowRequestAsync(sender, args, "REJECTED", list);
            actions.Children.Add(reject);
            Grid.SetColumn(actions, 1);
            grid.Children.Add(actions);
            card.Child = grid;
            return card;
        }

        private async void ViewBorrowRequestPhoto_Click(object sender, RoutedEventArgs e)
        {
            if (sender is not Button button || button.Tag is not int requestId)
                return;
            button.IsEnabled = false;
            var result = await _apiService.GetBorrowRequestBookImageAsync(requestId);
            button.IsEnabled = true;
            if (result.Image == null)
            {
                MessageBox.Show(result.Error, "Requested book photo", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var image = new BitmapImage();
            using (var stream = new MemoryStream(result.Image))
            {
                image.BeginInit();
                image.CacheOption = BitmapCacheOption.OnLoad;
                image.StreamSource = stream;
                image.EndInit();
                image.Freeze();
            }
            var content = new StackPanel();
            content.Children.Add(CreateHeading("Requested book photo", "Submitted by the borrower for staff verification."));
            var backButton = CreateRequestButton("Back to requests", "#00899A");
            backButton.Margin = new Thickness(0, 18, 0, 12);
            backButton.HorizontalAlignment = HorizontalAlignment.Left;
            backButton.Click += (_, _) => ShowModuleContent("Borrow Requests", "Review and process pending borrow requests.", "", BorrowRequestsButton);
            content.Children.Add(backButton);
            var imageFrame = new Border { Padding = new Thickness(12), Background = Brushes.White, CornerRadius = new CornerRadius(10), BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")), BorderThickness = new Thickness(1) };
            imageFrame.Child = new Image { Source = image, Stretch = System.Windows.Media.Stretch.Uniform, MaxHeight = 540, MaxWidth = 850 };
            content.Children.Add(imageFrame);
            MainContent.Content = content;
        }

        private async void ProcessBorrowRequestAsync(object sender, RoutedEventArgs e, string status, StackPanel list)
        {
            if (sender is not Button button || button.Tag is not int requestId)
                return;
            button.IsEnabled = false;
            var result = await _apiService.UpdateBorrowRequestAsync(requestId, status);
            if (!result.Success)
                MessageBox.Show(result.Message, "Borrow Request", MessageBoxButton.OK, MessageBoxImage.Error);
            else
                await LoadBorrowRequestsAsync(list);
        }

        private static Button CreateRequestButton(string text, string color)
        {
            return new Button
            {
                Content = text,
                Height = 38,
                MinWidth = 82,
                Margin = new Thickness(6, 0, 0, 0),
                Padding = new Thickness(10, 0, 10, 0),
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(color)),
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0),
                FontSize = 12,
                FontWeight = FontWeights.SemiBold
            };
        }

        private static TextBlock CreateRequestMessage(string text, string color)
        {
            return new TextBlock
            {
                Text = text,
                Padding = new Thickness(20),
                FontSize = 13,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(color))
            };
        }

        private static string FormatRequestDate(string value)
        {
            return DateTime.TryParse(value, out var date)
                ? $"Submitted {date:MMM d, yyyy h:mm tt}"
                : "Submitted recently";
        }

        private StackPanel CreateSettingsContent()
        {
            var settings = new LibrarySettingsData();
            var form = new StackPanel
            {
                Margin = new Thickness(0, 24, 0, 0),
                MaxWidth = 760
            };

            form.Children.Add(CreateSettingsSection(
                "Borrowing policy",
                "Set the standard loan period for each member type."
            ));
            _studentLoanDaysInput = AddBookField(form, "Student loan period (days)");
            _studentLoanDaysInput.Text = settings.StudentLoanDays.ToString();
            _teacherLoanDaysInput = AddBookField(form, "Teacher loan period (days)");
            _teacherLoanDaysInput.Text = settings.TeacherLoanDays.ToString();

            form.Children.Add(CreateSettingsSection(
                "Fines and notifications",
                "Control overdue penalties and staff notification preferences."
            ));
            _dailyPenaltyInput = AddBookField(form, "Daily overdue penalty (PHP)");
            _dailyPenaltyInput.Text = settings.DailyPenalty.ToString("0.00");
            _notificationsInput = new CheckBox
            {
                Content = "Enable notifications for overdue books and pending requests",
                IsChecked = settings.NotificationsEnabled,
                Margin = new Thickness(0, 0, 0, 18),
                FontSize = 13,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#31565C") )
            };
            form.Children.Add(_notificationsInput);

            var actions = new StackPanel { Orientation = Orientation.Horizontal };
            var saveButton = CreateSettingsButton("Save changes", "#00899A");
            saveButton.Click += SaveSettingsButton_Click;
            actions.Children.Add(saveButton);
            var resetButton = CreateSettingsButton("Reset defaults", "#E7EEF2");
            resetButton.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#31565C"));
            resetButton.Click += ResetSettingsButton_Click;
            actions.Children.Add(resetButton);
            form.Children.Add(actions);
            _ = LoadSharedSettingsAsync();
            return form;
        }

        private async Task LoadSharedSettingsAsync()
        {
            var response = await _apiService.GetLibrarySettingsAsync();
            if (!response.Success)
            {
                MessageBox.Show(response.Message, "Settings", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            _studentLoanDaysInput.Text = response.Settings.StudentLoanDays.ToString();
            _teacherLoanDaysInput.Text = response.Settings.TeacherLoanDays.ToString();
            _dailyPenaltyInput.Text = response.Settings.DailyPenalty.ToString("0.00");
            _notificationsInput.IsChecked = response.Settings.NotificationsEnabled;
        }

        private static TextBlock CreateSettingsSection(string title, string description)
        {
            return new TextBlock
            {
                Text = $"{title}\n{description}",
                Margin = new Thickness(0, 0, 0, 16),
                FontSize = 14,
                LineHeight = 22,
                FontWeight = FontWeights.SemiBold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12363D"))
            };
        }

        private static Button CreateSettingsButton(string text, string background)
        {
            return new Button
            {
                Content = text,
                Height = 42,
                Padding = new Thickness(18, 0, 18, 0),
                Margin = new Thickness(0, 0, 10, 0),
                Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(background)),
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0),
                FontWeight = FontWeights.SemiBold
            };
        }

        private async void SaveSettingsButton_Click(object sender, RoutedEventArgs e)
        {
            if (!int.TryParse(_studentLoanDaysInput.Text, out var studentDays) || studentDays < 1 || studentDays > 365 ||
                !int.TryParse(_teacherLoanDaysInput.Text, out var teacherDays) || teacherDays < 1 || teacherDays > 365 ||
                !decimal.TryParse(_dailyPenaltyInput.Text, out var dailyPenalty) || dailyPenalty < 0 || dailyPenalty > 100000)
            {
                MessageBox.Show("Enter valid policy values. Loan periods must be 1-365 days and penalty cannot be negative.", "Settings", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var response = await _apiService.SaveLibrarySettingsAsync(new LibrarySettingsData
            {
                StudentLoanDays = studentDays,
                TeacherLoanDays = teacherDays,
                DailyPenalty = dailyPenalty,
                NotificationsEnabled = _notificationsInput.IsChecked == true
            });
            MessageBox.Show(response.Message, "Settings", MessageBoxButton.OK, response.Success ? MessageBoxImage.Information : MessageBoxImage.Error);
        }

        private async void ResetSettingsButton_Click(object sender, RoutedEventArgs e)
        {
            var defaults = new LibrarySettingsData();
            _studentLoanDaysInput.Text = defaults.StudentLoanDays.ToString();
            _teacherLoanDaysInput.Text = defaults.TeacherLoanDays.ToString();
            _dailyPenaltyInput.Text = defaults.DailyPenalty.ToString("0.00");
            _notificationsInput.IsChecked = defaults.NotificationsEnabled;
            SaveSettingsButton_Click(sender, e);
        }

        private StackPanel CreateManageBooksContent()
        {
            var form = new StackPanel
            {
                Margin = new Thickness(0, 24, 0, 0),
                HorizontalAlignment = HorizontalAlignment.Stretch
            };

            _booksCatalogStatus = new TextBlock { Margin = new Thickness(0, 0, 0, 8), FontWeight = FontWeights.SemiBold, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")) };
            form.Children.Add(_booksCatalogStatus);
            _booksCatalogGrid = new DataGrid
            {
                AutoGenerateColumns = false,
                IsReadOnly = true,
                CanUserAddRows = false,
                RowHeaderWidth = 0,
                RowHeight = 30,
                ColumnHeaderHeight = 32,
                FontSize = 13,
                MaxHeight = 560,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                Background = Brushes.White
            };
            _booksCatalogGrid.Columns.Add(new DataGridTextColumn { Header = "Title", Binding = new Binding(nameof(BookData.Title)), Width = new DataGridLength(2, DataGridLengthUnitType.Star) });
            _booksCatalogGrid.Columns.Add(new DataGridTextColumn { Header = "Author", Binding = new Binding(nameof(BookData.Author)), Width = new DataGridLength(1.3, DataGridLengthUnitType.Star) });
            _booksCatalogGrid.Columns.Add(new DataGridTextColumn { Header = "Category", Binding = new Binding(nameof(BookData.Category)), Width = new DataGridLength(1, DataGridLengthUnitType.Star) });
            _booksCatalogGrid.Columns.Add(new DataGridTextColumn { Header = "Accession", Binding = new Binding(nameof(BookData.AccessionNumber)), Width = 130 });
            _booksCatalogGrid.Columns.Add(new DataGridTextColumn { Header = "Available", Binding = new Binding(nameof(BookData.AvailableCopies)), Width = 80 });
            _booksCatalogGrid.Columns.Add(new DataGridTextColumn { Header = "Total", Binding = new Binding(nameof(BookData.TotalCopies)), Width = 65 });
            _booksCatalogGrid.SelectionChanged += async (_, _) => await ShowSelectedBookDetailsAsync();
            form.Children.Add(_booksCatalogGrid);

            _bookCoverImage = new Image { Width = 120, Height = 160, Stretch = Stretch.Uniform, Visibility = Visibility.Collapsed };
            _bookCoverStatus = new TextBlock { Text = "No cover photo available.", Width = 120, TextWrapping = TextWrapping.Wrap, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177")), VerticalAlignment = VerticalAlignment.Center };
            _bookDetailsContent = new TextBlock { MaxWidth = 500, TextWrapping = TextWrapping.Wrap, VerticalAlignment = VerticalAlignment.Center, FontSize = 13, Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12363D")) };
            var coverColumn = new StackPanel { Width = 145, Margin = new Thickness(0, 0, 20, 0), HorizontalAlignment = HorizontalAlignment.Center };
            coverColumn.Children.Add(_bookCoverImage);
            coverColumn.Children.Add(_bookCoverStatus);
            var detailsLayout = new StackPanel { Orientation = Orientation.Horizontal };
            detailsLayout.Children.Add(coverColumn);
            detailsLayout.Children.Add(_bookDetailsContent);
            _bookDetailsPanel = new Border
            {
                Margin = new Thickness(0, 12, 0, 0),
                Padding = new Thickness(14),
                Background = Brushes.White,
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")),
                BorderThickness = new Thickness(1),
                Child = detailsLayout,
                Visibility = Visibility.Collapsed
            };
            form.Children.Add(_bookDetailsPanel);
            _ = LoadBooksCatalogAsync();
            return form;
        }

        private async Task ShowSelectedBookDetailsAsync()
        {
            if (_booksCatalogGrid.SelectedItem is not BookData book)
            {
                _bookDetailsPanel.Visibility = Visibility.Collapsed;
                return;
            }

            _bookDetailsPanel.Visibility = Visibility.Visible;
            _bookCoverImage.Source = null;
            _bookCoverImage.Visibility = Visibility.Collapsed;
            _bookCoverStatus.Text = string.IsNullOrWhiteSpace(book.CoverImage) ? "No cover photo available." : "Loading cover photo...";
            _bookCoverStatus.Visibility = Visibility.Visible;
            _bookDetailsContent.Text = $"{book.Title}\nAuthor: {book.Author}\nCategory: {book.Category ?? "Not specified"}\nCall number: {book.CallNumber ?? "Not specified"}\nAccession number: {book.AccessionNumber}\nISBN: {book.Isbn ?? "Not specified"}\nPublication year: {book.PublicationYear?.ToString() ?? "Not specified"}\nCopies: {book.AvailableCopies} available of {book.TotalCopies}\n\n{book.Description ?? "No description available."}";

            if (string.IsNullOrWhiteSpace(book.CoverImage))
                return;

            var imageBytes = await _apiService.GetBookCoverImageAsync(book.BookId);
            if (_booksCatalogGrid.SelectedItem is not BookData selectedBook || selectedBook.BookId != book.BookId)
                return;
            if (imageBytes == null)
            {
                _bookCoverStatus.Text = "Cover photo is unavailable.";
                return;
            }

            var image = new BitmapImage();
            using (var stream = new MemoryStream(imageBytes))
            {
                image.BeginInit();
                image.CacheOption = BitmapCacheOption.OnLoad;
                image.StreamSource = stream;
                image.EndInit();
                image.Freeze();
            }
            _bookCoverImage.Source = image;
            _bookCoverImage.Visibility = Visibility.Visible;
            _bookCoverStatus.Visibility = Visibility.Collapsed;
        }

        private async Task LoadBooksCatalogAsync()
        {
            _booksCatalogStatus.Text = "Loading book catalog...";
            var result = await _apiService.GetBooksAsync();
            _booksCatalogGrid.ItemsSource = result.Success ? result.Books : null;
            _booksCatalogStatus.Text = result.Success ? $"Book catalog • {result.Books.Count} title(s)" : result.Message;
        }

        private static TextBox AddBookField(StackPanel parent, string label)
        {
            parent.Children.Add(new TextBlock
            {
                Text = label,
                Margin = new Thickness(0, 0, 0, 5),
                FontSize = 13,
                FontWeight = FontWeights.SemiBold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12363D"))
            });
            var input = new TextBox
            {
                Height = 38,
                Margin = new Thickness(0, 0, 0, 12),
                Padding = new Thickness(10, 8, 10, 8),
                FontSize = 13
            };
            parent.Children.Add(input);
            return input;
        }

        private static StackPanel CreateHeading(string title, string description)
        {
            var heading = new StackPanel();
            heading.Children.Add(new TextBlock
            {
                Text = title,
                FontSize = 30,
                FontWeight = FontWeights.SemiBold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#12363D"))
            });
            heading.Children.Add(new TextBlock
            {
                Text = description,
                Margin = new Thickness(0, 6, 0, 0),
                FontSize = 14,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177"))
            });
            return heading;
        }

        private static Border CreateMetric(string label, string value, string valueColor = "#12363D", Action<TextBlock>? registerValue = null)
        {
            var card = new Border
            {
                Margin = new Thickness(7),
                Padding = new Thickness(17),
                Background = Brushes.White,
                BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#CFE0E1")),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(10),
                MinHeight = 108
            };
            var content = new StackPanel();
            content.Children.Add(new TextBlock
            {
                Text = label,
                FontSize = 12,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#547177"))
            });
            var valueText = new TextBlock
            {
                Text = value,
                Margin = new Thickness(0, 8, 0, 0),
                FontSize = 29,
                FontWeight = FontWeights.SemiBold,
                Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(valueColor))
            };
            content.Children.Add(valueText);
            registerValue?.Invoke(valueText);
            card.Child = content;
            return card;
        }

        private void SetActiveButton(Button selectedButton)
        {
            foreach (var button in new[]
            {
                DashboardButton, BorrowRequestsButton, ActiveLoansButton,
                BookReturnsButton, OverdueBooksButton, PenaltiesButton,
                ManageBooksButton, BorrowersButton, NotificationsButton,
                ReportsButton, UserManagementButton, AuditLogsButton, SettingsButton
            })
            {
                button.Tag = null;
            }

            selectedButton.Tag = "Active";
        }

        private void DashboardButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            LoadDashboard();
        }

        private void BorrowRequestsButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Borrow Requests",
                "Review and process pending borrow requests.",
                "📝",
                BorrowRequestsButton
            );
        }

        private void ActiveLoansButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Active Loans",
                "View borrowed books and their due dates.",
                "📖",
                ActiveLoansButton
            );
        }

        private void BookReturnsButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Book Returns",
                "Process returned books and penalties.",
                "↩",
                BookReturnsButton
            );
        }

        private void OverdueBooksButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Overdue Books",
                "View books that passed their due date.",
                "⚠",
                OverdueBooksButton
            );
        }

        private void PenaltiesButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Penalties",
                "View and process unpaid penalties.",
                "₱",
                PenaltiesButton
            );
        }

        private void ManageBooksButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Manage Books",
                "View the book catalog and inspect book details.",
                "📚",
                ManageBooksButton
            );
        }

        private void BorrowersButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Borrowers",
                "View students, teachers, and histories.",
                "👥",
                BorrowersButton
            );
        }

        private void NotificationsButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Notifications",
                "View and send library notifications.",
                "🔔",
                NotificationsButton
            );
        }

        private void ReportsButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            ShowModuleContent(
                "Reports",
                "Generate borrowing and inventory reports.",
                "📊",
                ReportsButton
            );
        }

        private void UserManagementButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (_currentRole != "ADMIN")
            {
                ShowAdminRequired();
                return;
            }

            ShowModuleContent(
                "User Management",
                "Manage accounts, roles, and status.",
                "👤",
                UserManagementButton
            );
        }

        private void AuditLogsButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (_currentRole != "ADMIN")
            {
                ShowAdminRequired();
                return;
            }

            ShowModuleContent(
                "Audit Logs",
                "View administrator and librarian actions.",
                "📋",
                AuditLogsButton
            );
        }

        private void SettingsButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (_currentRole != "ADMIN")
            {
                ShowAdminRequired();
                return;
            }

            ShowModuleContent(
                "Settings",
                "Configure loan periods and penalties.",
                "⚙",
                SettingsButton
            );
        }

        private void ShowAdminRequired()
        {
            MessageBox.Show(
                "Administrator access is required.",
                "Access Denied",
                MessageBoxButton.OK,
                MessageBoxImage.Warning
            );
        }

        private void SignOutButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            var answer = MessageBox.Show(
                "Are you sure you want to sign out?",
                "Sign Out",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question
            );

            if (answer != MessageBoxResult.Yes)
                return;

            var loginWindow = new MainWindow();
            loginWindow.Show();

            Close();
        }
    }

    public class VerificationAction
    {
        public VerificationAction(int profileId, string status, StackPanel list)
        {
            ProfileId = profileId;
            Status = status;
            List = list;
        }

        public int ProfileId { get; }
        public string Status { get; }
        public StackPanel List { get; }
    }

    public class DeleteBorrowerAction
    {
        public DeleteBorrowerAction(int userId, StackPanel list, string fullName)
        {
            UserId = userId;
            List = list;
            FullName = fullName;
        }

        public int UserId { get; }
        public StackPanel List { get; }
        public string FullName { get; }
    }

}
