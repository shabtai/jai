#!/usr/bin/env php
<?php
/**
 * DataValidator - Comprehensive data validation and type checking tool
 * Validates various data types, checks constraints, and generates reports
 */

class DataValidator
{
    private $data;
    private $errors = [];
    private $warnings = [];
    private $stats = [];

    public function __construct($jsonData)
    {
        $this->data = json_decode($jsonData, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            $this->errors[] = 'JSON Error: ' . json_last_error_msg();
        }
    }

    /**
     * Validate email format
     */
    public function validateEmail($email)
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $this->errors[] = "Invalid email: $email";
            return false;
        }
        return true;
    }

    /**
     * Validate URL format
     */
    public function validateUrl($url)
    {
        if (!filter_var($url, FILTER_VALIDATE_URL)) {
            $this->errors[] = "Invalid URL: $url";
            return false;
        }
        return true;
    }

    /**
     * Validate IP address
     */
    public function validateIp($ip)
    {
        if (!filter_var($ip, FILTER_VALIDATE_IP)) {
            $this->errors[] = "Invalid IP address: $ip";
            return false;
        }
        return true;
    }

    /**
     * Validate data types recursively
     */
    public function validateTypes($data, $path = '')
    {
        if (is_array($data)) {
            foreach ($data as $key => $value) {
                $newPath = $path ? "$path.$key" : $key;
                $this->validateTypes($value, $newPath);
            }
        } elseif (is_object($data)) {
            foreach ($data as $key => $value) {
                $newPath = $path ? "$path->$key" : $key;
                $this->validateTypes($value, $newPath);
            }
        } elseif (is_null($data)) {
            $this->warnings[] = "Null value at: $path";
        }
    }

    /**
     * Check string length constraints
     */
    public function validateStringLength($string, $minLength, $maxLength, $fieldName)
    {
        $length = strlen($string);
        if ($length < $minLength) {
            $this->errors[] = "$fieldName is too short (min: $minLength, got: $length)";
            return false;
        }
        if ($length > $maxLength) {
            $this->errors[] = "$fieldName is too long (max: $maxLength, got: $length)";
            return false;
        }
        return true;
    }

    /**
     * Check numeric constraints
     */
    public function validateNumericRange($value, $min, $max, $fieldName)
    {
        if ($value < $min || $value > $max) {
            $this->errors[] = "$fieldName out of range [$min, $max], got: $value";
            return false;
        }
        return true;
    }

    /**
     * Validate required fields
     */
    public function validateRequired($array, $requiredFields)
    {
        foreach ($requiredFields as $field) {
            if (!isset($array[$field]) || empty($array[$field])) {
                $this->errors[] = "Required field missing: $field";
            }
        }
    }

    /**
     * Analyze data structure
     */
    public function analyzeStructure()
    {
        if (!is_array($this->data)) {
            return ['error' => 'Data is not an array'];
        }

        return [
            'type' => gettype($this->data),
            'size' => count($this->data),
            'depth' => $this->calculateDepth($this->data),
            'keys' => array_keys($this->data),
            'memory_usage' => strlen(json_encode($this->data)) . ' bytes'
        ];
    }

    /**
     * Calculate data structure depth
     */
    private function calculateDepth($data, $depth = 0)
    {
        if (!is_array($data)) {
            return $depth;
        }

        $maxDepth = $depth;
        foreach ($data as $value) {
            if (is_array($value)) {
                $currentDepth = $this->calculateDepth($value, $depth + 1);
                $maxDepth = max($maxDepth, $currentDepth);
            }
        }

        return $maxDepth;
    }

    /**
     * Sanitize input data
     */
    public function sanitize($string)
    {
        if (!is_string($string)) {
            return $string;
        }

        $string = trim($string);
        $string = stripslashes($string);
        $string = htmlspecialchars($string, ENT_QUOTES, 'UTF-8');

        return $string;
    }

    /**
     * Generate validation report
     */
    public function generateReport()
    {
        $report = [];
        $report[] = "Data Validation Report";
        $report[] = "======================";
        $report[] = "";

        // Summary
        $report[] = "Validation Summary:";
        $report[] = "  Errors: " . count($this->errors);
        $report[] = "  Warnings: " . count($this->warnings);
        $report[] = "";

        // Errors
        if (count($this->errors) > 0) {
            $report[] = "Errors:";
            foreach ($this->errors as $error) {
                $report[] = "  - $error";
            }
            $report[] = "";
        }

        // Warnings
        if (count($this->warnings) > 0) {
            $report[] = "Warnings:";
            foreach ($this->warnings as $warning) {
                $report[] = "  - $warning";
            }
            $report[] = "";
        }

        // Data structure analysis
        $analysis = $this->analyzeStructure();
        if (!isset($analysis['error'])) {
            $report[] = "Data Structure:";
            $report[] = "  Type: " . $analysis['type'];
            $report[] = "  Size: " . $analysis['size'];
            $report[] = "  Depth: " . $analysis['depth'];
            $report[] = "  Memory Usage: " . $analysis['memory_usage'];
            $report[] = "";
        }

        // Validation status
        $report[] = "Status: " . (count($this->errors) === 0 ? "VALID ✓" : "INVALID ✗");

        return implode("\n", $report);
    }

    /**
     * Validate complete dataset
     */
    public function validate()
    {
        if (!is_array($this->data)) {
            $this->errors[] = "Data must be an array";
            return false;
        }

        $this->validateTypes($this->data);
        return count($this->errors) === 0;
    }

    public function getErrors()
    {
        return $this->errors;
    }

    public function getWarnings()
    {
        return $this->warnings;
    }
}

function main()
{
    if (count($GLOBALS['argv']) < 2) {
        echo "Usage: php data_validator.php '<json_data>'\n";
        exit(1);
    }

    $jsonData = $GLOBALS['argv'][1];

    try {
        $validator = new DataValidator($jsonData);
        $validator->validate();
        echo $validator->generateReport();
        echo "\n";

        if (count($validator->getErrors()) > 0) {
            exit(1);
        }
    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
        exit(1);
    }
}

main();
?>
