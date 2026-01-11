#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <cmath>
#include <sstream>
#include <iomanip>

using namespace std;

/**
 * NumberAnalyzer - Comprehensive number analysis and statistics tool
 */
class NumberAnalyzer {
private:
    vector<double> numbers;
    string errors;

public:
    NumberAnalyzer() {}

    /**
     * Parse comma-separated numbers
     */
    bool parse(const string& input) {
        stringstream ss(input);
        string number;

        while (getline(ss, number, ',')) {
            // Trim whitespace
            size_t start = number.find_first_not_of(" \t\r\n");
            size_t end = number.find_last_not_of(" \t\r\n");

            if (start != string::npos) {
                number = number.substr(start, end - start + 1);
            }

            try {
                double num = stod(number);
                numbers.push_back(num);
            } catch (const invalid_argument&) {
                errors += "Invalid number: " + number + "\n";
            } catch (const out_of_range&) {
                errors += "Number out of range: " + number + "\n";
            }
        }

        return !numbers.empty();
    }

    /**
     * Calculate sum of all numbers
     */
    double calculateSum() {
        double sum = 0.0;
        for (double num : numbers) {
            sum += num;
        }
        return sum;
    }

    /**
     * Calculate average
     */
    double calculateAverage() {
        if (numbers.empty()) return 0.0;
        return calculateSum() / numbers.size();
    }

    /**
     * Calculate median
     */
    double calculateMedian() {
        if (numbers.empty()) return 0.0;

        vector<double> sorted = numbers;
        sort(sorted.begin(), sorted.end());

        size_t size = sorted.size();
        if (size % 2 == 0) {
            return (sorted[size / 2 - 1] + sorted[size / 2]) / 2.0;
        } else {
            return sorted[size / 2];
        }
    }

    /**
     * Calculate standard deviation
     */
    double calculateStdDev() {
        if (numbers.empty()) return 0.0;

        double avg = calculateAverage();
        double sumSquareDiff = 0.0;

        for (double num : numbers) {
            double diff = num - avg;
            sumSquareDiff += diff * diff;
        }

        return sqrt(sumSquareDiff / numbers.size());
    }

    /**
     * Find mode (most frequent number)
     */
    double findMode() {
        if (numbers.empty()) return 0.0;

        vector<double> sorted = numbers;
        sort(sorted.begin(), sorted.end());

        double mode = sorted[0];
        int maxCount = 1;
        int currentCount = 1;

        for (size_t i = 1; i < sorted.size(); i++) {
            if (sorted[i] == sorted[i - 1]) {
                currentCount++;
                if (currentCount > maxCount) {
                    maxCount = currentCount;
                    mode = sorted[i];
                }
            } else {
                currentCount = 1;
            }
        }

        return mode;
    }

    /**
     * Calculate quartiles
     */
    vector<double> calculateQuartiles() {
        if (numbers.size() < 4) {
            return {0.0, 0.0, 0.0};
        }

        vector<double> sorted = numbers;
        sort(sorted.begin(), sorted.end());

        size_t size = sorted.size();
        size_t q1_idx = size / 4;
        size_t q2_idx = size / 2;
        size_t q3_idx = (3 * size) / 4;

        return {sorted[q1_idx], sorted[q2_idx], sorted[q3_idx]};
    }

    /**
     * Generate comprehensive report
     */
    string generateReport() {
        stringstream report;

        report << "Number Analysis Report\n";
        report << "======================\n\n";

        if (!errors.empty()) {
            report << "Warnings/Errors:\n";
            report << errors << "\n";
        }

        if (numbers.empty()) {
            report << "Error: No valid numbers parsed\n";
            return report.str();
        }

        // Basic statistics
        report << fixed << setprecision(4);

        report << "Basic Statistics:\n";
        report << "  Count: " << numbers.size() << "\n";
        report << "  Sum: " << calculateSum() << "\n";
        report << "  Average: " << calculateAverage() << "\n";
        report << "  Median: " << calculateMedian() << "\n";
        report << "  Mode: " << findMode() << "\n\n";

        // Range statistics
        double minVal = *min_element(numbers.begin(), numbers.end());
        double maxVal = *max_element(numbers.begin(), numbers.end());

        report << "Range Statistics:\n";
        report << "  Minimum: " << minVal << "\n";
        report << "  Maximum: " << maxVal << "\n";
        report << "  Range: " << (maxVal - minVal) << "\n\n";

        // Dispersion statistics
        report << "Dispersion Statistics:\n";
        report << "  Standard Deviation: " << calculateStdDev() << "\n";
        report << "  Variance: " << (calculateStdDev() * calculateStdDev()) << "\n\n";

        // Quartiles
        vector<double> quartiles = calculateQuartiles();
        report << "Quartile Analysis:\n";
        report << "  Q1 (25th percentile): " << quartiles[0] << "\n";
        report << "  Q2 (50th percentile): " << quartiles[1] << "\n";
        report << "  Q3 (75th percentile): " << quartiles[2] << "\n";
        report << "  IQR: " << (quartiles[2] - quartiles[0]) << "\n\n";

        // Positive/Negative analysis
        int positiveCount = 0;
        int negativeCount = 0;
        int zeroCount = 0;

        for (double num : numbers) {
            if (num > 0) positiveCount++;
            else if (num < 0) negativeCount++;
            else zeroCount++;
        }

        report << "Sign Analysis:\n";
        report << "  Positive: " << positiveCount << "\n";
        report << "  Negative: " << negativeCount << "\n";
        report << "  Zero: " << zeroCount << "\n";

        return report.str();
    }

    string getErrors() const {
        return errors;
    }

    size_t getCount() const {
        return numbers.size();
    }
};

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "Usage: number_analyzer '<comma-separated-numbers>'\n";
        return 1;
    }

    string input = argv[1];

    NumberAnalyzer analyzer;

    if (!analyzer.parse(input)) {
        cerr << "Error parsing input: " << analyzer.getErrors();
        return 1;
    }

    cout << analyzer.generateReport();

    return 0;
}
