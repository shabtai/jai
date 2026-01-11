import java.util.*;
import java.util.stream.*;
import java.util.regex.*;

/**
 * StringProcessor - Advanced string manipulation and analysis tool
 * Provides comprehensive string processing capabilities
 */
public class StringProcessor {

    private String input;
    private List<String> processedLines;
    private Map<String, Integer> statistics;

    public StringProcessor(String input) {
        this.input = input;
        this.processedLines = new ArrayList<>();
        this.statistics = new HashMap<>();
    }

    /**
     * Count occurrences of substring
     */
    public int countOccurrences(String substring) {
        if (substring.isEmpty()) return 0;
        int count = 0;
        int index = 0;
        while ((index = input.indexOf(substring, index)) != -1) {
            count++;
            index += substring.length();
        }
        return count;
    }

    /**
     * Split and process lines
     */
    public List<String> processLines() {
        return Arrays.stream(input.split("\n"))
            .map(String::trim)
            .filter(line -> !line.isEmpty())
            .collect(Collectors.toList());
    }

    /**
     * Extract words (alphanumeric sequences)
     */
    public List<String> extractWords() {
        Pattern pattern = Pattern.compile("\\b\\w+\\b");
        Matcher matcher = pattern.matcher(input);
        List<String> words = new ArrayList<>();

        while (matcher.find()) {
            words.add(matcher.group());
        }

        return words;
    }

    /**
     * Find all email addresses
     */
    public List<String> extractEmails() {
        Pattern pattern = Pattern.compile("[\\w.-]+@[\\w.-]+\\.\\w+");
        Matcher matcher = pattern.matcher(input);
        List<String> emails = new ArrayList<>();

        while (matcher.find()) {
            emails.add(matcher.group());
        }

        return emails;
    }

    /**
     * Find all URLs
     */
    public List<String> extractUrls() {
        Pattern pattern = Pattern.compile("https?://[\\w.-]+(?:\\.[\\w.-]+)*(?:/[\\w./?%&=]*)?");
        Matcher matcher = pattern.matcher(input);
        List<String> urls = new ArrayList<>();

        while (matcher.find()) {
            urls.add(matcher.group());
        }

        return urls;
    }

    /**
     * Analyze character frequency
     */
    public Map<Character, Integer> analyzeCharacterFrequency() {
        Map<Character, Integer> frequency = new LinkedHashMap<>();

        for (char c : input.toCharArray()) {
            if (Character.isLetterOrDigit(c)) {
                frequency.merge(c, 1, Integer::sum);
            }
        }

        return frequency.entrySet().stream()
            .sorted((a, b) -> b.getValue().compareTo(a.getValue()))
            .limit(20)
            .collect(Collectors.toMap(
                Map.Entry::getKey,
                Map.Entry::getValue,
                (e1, e2) -> e1,
                LinkedHashMap::new
            ));
    }

    /**
     * Find longest word
     */
    public String findLongestWord() {
        return extractWords().stream()
            .max(Comparator.comparingInt(String::length))
            .orElse("");
    }

    /**
     * Find shortest word
     */
    public String findShortestWord() {
        return extractWords().stream()
            .filter(w -> w.length() > 0)
            .min(Comparator.comparingInt(String::length))
            .orElse("");
    }

    /**
     * Generate comprehensive statistics
     */
    public Map<String, Object> generateStatistics() {
        Map<String, Object> stats = new LinkedHashMap<>();

        List<String> words = extractWords();
        List<String> lines = processLines();

        stats.put("total_characters", input.length());
        stats.put("letters", countType(Character::isLetter));
        stats.put("digits", countType(Character::isDigit));
        stats.put("spaces", countType(Character::isWhitespace));
        stats.put("punctuation", countType(c -> !Character.isLetterOrDigit(c) && !Character.isWhitespace(c)));

        stats.put("words", words.size());
        stats.put("unique_words", words.stream().distinct().count());
        stats.put("lines", lines.size());
        stats.put("paragraphs", countOccurrences("\n\n") + 1);

        if (!words.isEmpty()) {
            double avgWordLength = words.stream()
                .mapToInt(String::length)
                .average()
                .orElse(0);
            stats.put("avg_word_length", String.format("%.2f", avgWordLength));
        }

        stats.put("longest_word", findLongestWord());
        stats.put("shortest_word", findShortestWord());

        List<String> emails = extractEmails();
        if (!emails.isEmpty()) {
            stats.put("emails_found", emails.size());
        }

        List<String> urls = extractUrls();
        if (!urls.isEmpty()) {
            stats.put("urls_found", urls.size());
        }

        return stats;
    }

    /**
     * Count characters of specific type
     */
    private int countType(java.util.function.Predicate<Character> predicate) {
        int count = 0;
        for (char c : input.toCharArray()) {
            if (predicate.test(c)) {
                count++;
            }
        }
        return count;
    }

    /**
     * Replace all occurrences with regex
     */
    public String replaceWithRegex(String pattern, String replacement) {
        return input.replaceAll(pattern, replacement);
    }

    /**
     * Generate analysis report
     */
    public String generateReport() {
        StringBuilder report = new StringBuilder();

        report.append("String Analysis Report\n");
        report.append("======================\n\n");

        Map<String, Object> stats = generateStatistics();

        report.append("Basic Statistics:\n");
        report.append(String.format("  Total Characters: %s\n", stats.get("total_characters")));
        report.append(String.format("  Letters: %s\n", stats.get("letters")));
        report.append(String.format("  Digits: %s\n", stats.get("digits")));
        report.append(String.format("  Spaces: %s\n", stats.get("spaces")));
        report.append(String.format("  Punctuation: %s\n\n", stats.get("punctuation")));

        report.append("Word Statistics:\n");
        report.append(String.format("  Total Words: %s\n", stats.get("words")));
        report.append(String.format("  Unique Words: %s\n", stats.get("unique_words")));
        report.append(String.format("  Average Word Length: %s\n", stats.get("avg_word_length")));
        report.append(String.format("  Longest Word: %s\n", stats.get("longest_word")));
        report.append(String.format("  Shortest Word: %s\n\n", stats.get("shortest_word")));

        report.append("Line Statistics:\n");
        report.append(String.format("  Total Lines: %s\n", stats.get("lines")));
        report.append(String.format("  Paragraphs: %s\n\n", stats.get("paragraphs")));

        if (stats.containsKey("emails_found")) {
            report.append(String.format("Emails Found: %s\n", stats.get("emails_found")));
        }

        if (stats.containsKey("urls_found")) {
            report.append(String.format("URLs Found: %s\n", stats.get("urls_found")));
        }

        Map<Character, Integer> charFreq = analyzeCharacterFrequency();
        if (!charFreq.isEmpty()) {
            report.append("\nTop Characters:\n");
            charFreq.entrySet().stream()
                .limit(10)
                .forEach(e -> report.append(String.format("  '%c': %d\n", e.getKey(), e.getValue())));
        }

        return report.toString();
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java StringProcessor '<text>'");
            System.exit(1);
        }

        String input = args[0];

        try {
            StringProcessor processor = new StringProcessor(input);
            String report = processor.generateReport();
            System.out.println(report);
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }
}
