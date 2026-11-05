using System.Globalization;
using System.IO;
using Microsoft.VisualBasic.FileIO;

namespace PCDSLibrary.Desktop.Models
{
    public sealed record BookCsvRow(int RowNumber, CreateBookRequest Request);

    public sealed class BookCsvImportResult
    {
        public List<BookCsvRow> Rows { get; } = new();
        public List<string> Issues { get; } = new();
    }

    public static class BookCsvImporter
    {
        public static BookCsvImportResult Parse(string filePath)
        {
            using var parser = new TextFieldParser(filePath)
            {
                TextFieldType = FieldType.Delimited,
                HasFieldsEnclosedInQuotes = true,
                TrimWhiteSpace = false
            };
            parser.SetDelimiters(",");

            var result = new BookCsvImportResult();
            if (parser.EndOfData)
                throw new InvalidDataException("The selected CSV file is empty.");

            var headers = parser.ReadFields();
            if (headers == null || headers.Length == 0)
                throw new InvalidDataException("The selected CSV file does not have a header row.");

            var columns = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
            for (var index = 0; index < headers.Length; index++)
            {
                var name = NormalizeHeader(headers[index]);
                if (name.Length == 0)
                    continue;
                if (!columns.TryAdd(name, index))
                    throw new InvalidDataException($"The CSV has a duplicate column: {headers[index]}.");
            }

            foreach (var (name, label) in new[]
            {
                ("title", "title"),
                ("author", "author"),
                ("accessionnumber", "accession_number")
            })
            {
                if (!columns.ContainsKey(name))
                    throw new InvalidDataException($"The CSV is missing the required '{label}' column.");
            }

            var accessionNumbers = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var isbns = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var rowNumber = 1;
            while (!parser.EndOfData)
            {
                rowNumber++;
                var fields = parser.ReadFields();
                if (fields == null || fields.All(string.IsNullOrWhiteSpace))
                    continue;

                string Read(string name)
                {
                    if (!columns.TryGetValue(name, out var index) || index >= fields.Length)
                        return "";
                    return fields[index].Trim();
                }

                var title = Read("title");
                var author = Read("author");
                var accessionNumber = Read("accessionnumber");
                if (title.Length == 0 || author.Length == 0 || accessionNumber.Length == 0)
                {
                    result.Issues.Add($"Row {rowNumber}: title, author, and accession_number are required.");
                    continue;
                }

                int? publicationYear = null;
                var yearText = Read("publicationyear");
                if (yearText.Length > 0)
                {
                    if (!int.TryParse(yearText, NumberStyles.Integer, CultureInfo.InvariantCulture, out var year) || year is < 1000 or > 9999)
                    {
                        result.Issues.Add($"Row {rowNumber}: publication_year must be a four-digit year.");
                        continue;
                    }
                    publicationYear = year;
                }

                var copies = 1;
                var copiesText = Read("totalcopies");
                if (copiesText.Length > 0 &&
                    (!int.TryParse(copiesText, NumberStyles.Integer, CultureInfo.InvariantCulture, out copies) || copies < 1))
                {
                    result.Issues.Add($"Row {rowNumber}: total_copies must be at least 1.");
                    continue;
                }

                var isbn = Read("isbn");
                if (accessionNumbers.Contains(accessionNumber) || (isbn.Length > 0 && isbns.Contains(isbn)))
                {
                    result.Issues.Add($"Row {rowNumber}: duplicate accession number or ISBN in this CSV.");
                    continue;
                }

                accessionNumbers.Add(accessionNumber);
                if (isbn.Length > 0)
                    isbns.Add(isbn);

                result.Rows.Add(new BookCsvRow(rowNumber, new CreateBookRequest
                {
                    Title = title,
                    Author = author,
                    AccessionNumber = accessionNumber,
                    CallNumber = Read("callnumber"),
                    Isbn = isbn,
                    Category = Read("category"),
                    PublicationYear = publicationYear,
                    TotalCopies = copies,
                    Description = Read("description")
                }));
            }

            return result;
        }

        private static string NormalizeHeader(string value) =>
            new(value.Where(char.IsLetterOrDigit).Select(char.ToLowerInvariant).ToArray());
    }
}
