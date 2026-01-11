package main

import (
	"fmt"
	"os"
	"strings"
	"unicode"
	"sort"
)

// TextStats holds statistics about text
type TextStats struct {
	TotalChars     int
	Letters        int
	Digits         int
	Spaces         int
	Punctuation    int
	Words          int
	Lines          int
	Sentences      int
	UniqueWords    int
	Paragraphs     int
	AvgWordLength  float64
	AvgWordsPerLine float64
}

// AnalyzeText performs comprehensive text analysis
func AnalyzeText(text string) *TextStats {
	stats := &TextStats{}

	// Count basic characters
	stats.TotalChars = len(text)
	stats.Lines = strings.Count(text, "\n") + 1
	stats.Paragraphs = strings.Count(text, "\n\n") + 1

	// Count character types
	for _, r := range text {
		if unicode.IsLetter(r) {
			stats.Letters++
		} else if unicode.IsDigit(r) {
			stats.Digits++
		} else if unicode.IsSpace(r) {
			stats.Spaces++
		} else if unicode.IsPunct(r) {
			stats.Punctuation++
		}
	}

	// Count words
	words := strings.Fields(text)
	stats.Words = len(words)

	// Count sentences
	stats.Sentences = strings.Count(text, ".") +
		strings.Count(text, "!") +
		strings.Count(text, "?")

	// Calculate unique words
	wordMap := make(map[string]bool)
	for _, word := range words {
		cleanWord := strings.ToLower(strings.TrimFunc(word, func(r rune) bool {
			return unicode.IsPunct(r) || unicode.IsSpace(r)
		}))
		if len(cleanWord) > 0 {
			wordMap[cleanWord] = true
		}
	}
	stats.UniqueWords = len(wordMap)

	// Calculate averages
	if stats.Words > 0 {
		totalLength := 0
		for _, word := range words {
			totalLength += len(word)
		}
		stats.AvgWordLength = float64(totalLength) / float64(stats.Words)
	}

	if stats.Lines > 0 {
		stats.AvgWordsPerLine = float64(stats.Words) / float64(stats.Lines)
	}

	return stats
}

// GenerateReport creates formatted report
func GenerateReport(stats *TextStats) string {
	var report strings.Builder

	report.WriteString("Text Analysis Report\n")
	report.WriteString("====================\n\n")

	report.WriteString(fmt.Sprintf("Total Characters: %d\n", stats.TotalChars))
	report.WriteString(fmt.Sprintf("Letters: %d\n", stats.Letters))
	report.WriteString(fmt.Sprintf("Digits: %d\n", stats.Digits))
	report.WriteString(fmt.Sprintf("Spaces: %d\n", stats.Spaces))
	report.WriteString(fmt.Sprintf("Punctuation: %d\n\n", stats.Punctuation))

	report.WriteString(fmt.Sprintf("Words: %d\n", stats.Words))
	report.WriteString(fmt.Sprintf("Unique Words: %d\n", stats.UniqueWords))
	report.WriteString(fmt.Sprintf("Sentences: %d\n", stats.Sentences))
	report.WriteString(fmt.Sprintf("Lines: %d\n", stats.Lines))
	report.WriteString(fmt.Sprintf("Paragraphs: %d\n\n", stats.Paragraphs))

	report.WriteString(fmt.Sprintf("Avg Word Length: %.2f\n", stats.AvgWordLength))
	report.WriteString(fmt.Sprintf("Avg Words Per Line: %.2f\n", stats.AvgWordsPerLine))

	// Calculate reading difficulty
	difficulty := CalculateReadingDifficulty(stats)
	report.WriteString(fmt.Sprintf("Reading Difficulty: %s\n", difficulty))

	return report.String()
}

// CalculateReadingDifficulty estimates text complexity
func CalculateReadingDifficulty(stats *TextStats) string {
	if stats.AvgWordLength > 6 && stats.Sentences > 0 {
		return "Advanced"
	} else if stats.AvgWordLength > 4 {
		return "Intermediate"
	}
	return "Basic"
}

// GetFrequentWords returns most common words
func GetFrequentWords(text string, limit int) []string {
	wordFreq := make(map[string]int)
	words := strings.Fields(text)

	for _, word := range words {
		cleanWord := strings.ToLower(strings.TrimFunc(word, func(r rune) bool {
			return unicode.IsPunct(r)
		}))
		if len(cleanWord) > 2 {
			wordFreq[cleanWord]++
		}
	}

	// Sort by frequency
	type kv struct {
		Key   string
		Value int
	}
	var sorted []kv
	for k, v := range wordFreq {
		sorted = append(sorted, kv{k, v})
	}

	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Value > sorted[j].Value
	})

	// Extract top N words
	result := []string{}
	for i := 0; i < limit && i < len(sorted); i++ {
		result = append(result, fmt.Sprintf("%s (%d)", sorted[i].Key, sorted[i].Value))
	}

	return result
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: text_analyzer '<text>'")
		os.Exit(1)
	}

	text := os.Args[1]

	if strings.TrimSpace(text) == "" {
		fmt.Println("Error: Input text cannot be empty")
		os.Exit(1)
	}

	// Analyze text
	stats := AnalyzeText(text)
	report := GenerateReport(stats)
	fmt.Print(report)

	// Show frequent words
	frequentWords := GetFrequentWords(text, 5)
	if len(frequentWords) > 0 {
		fmt.Println("\nMost Frequent Words (>2 chars):")
		for _, word := range frequentWords {
			fmt.Printf("  %s\n", word)
		}
	}
}
