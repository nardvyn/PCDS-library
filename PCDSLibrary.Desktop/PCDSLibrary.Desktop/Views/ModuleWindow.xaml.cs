using System;
using System.Windows;

namespace PCDSLibrary.Desktop.Views
{
    public partial class ModuleWindow : Window
    {
        private readonly Action? _refreshFunction;

        public ModuleWindow(
            string title,
            string description,
            string icon,
            Action? refreshFunction = null)
        {
            InitializeComponent();

            Title = $"PCDS Library - {title}";
            ModuleTitleText.Text = title;
            ModuleDescriptionText.Text = description;
            ModuleIconText.Text = icon;
            EmptyMessageText.Text = $"{title} Module";

            _refreshFunction = refreshFunction;
        }

        private void BackButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            Close();
        }

        private void RefreshButton_Click(
            object sender,
            RoutedEventArgs e)
        {
            _refreshFunction?.Invoke();

            MessageBox.Show(
                "Data refreshed.",
                "PCDS Library",
                MessageBoxButton.OK,
                MessageBoxImage.Information
            );
        }
    }
}
