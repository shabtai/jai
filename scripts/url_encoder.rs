use std::env;
use std::process;

/// URLEncoder provides URL encoding/decoding functionality
struct URLEncoder {
    input: String,
}

impl URLEncoder {
    fn new(input: String) -> Self {
        URLEncoder { input }
    }

    /// Encode string to URL-safe format
    fn encode(&self) -> String {
        self.input
            .chars()
            .map(|c| match c {
                'A'..='Z' | 'a'..='z' | '0'..='9' | '-' | '_' | '.' | '~' => c.to_string(),
                ' ' => "+".to_string(),
                c => format!("%{:02X}", c as u8),
            })
            .collect()
    }

    /// Decode URL-encoded string
    fn decode(&self) -> Result<String, String> {
        let mut result = String::new();
        let mut chars = self.input.chars().peekable();

        while let Some(c) = chars.next() {
            match c {
                '+' => result.push(' '),
                '%' => {
                    // Get next two characters for hex code
                    let hex: String = (0..2)
                        .filter_map(|_| chars.next())
                        .collect();

                    if hex.len() != 2 {
                        return Err("Invalid percent encoding".to_string());
                    }

                    match u8::from_str_radix(&hex, 16) {
                        Ok(byte) => result.push(byte as char),
                        Err(_) => return Err(format!("Invalid hex sequence: %{}", hex)),
                    }
                }
                c => result.push(c),
            }
        }

        Ok(result)
    }

    /// Analyze URL components
    fn analyze(&self) -> URLAnalysis {
        let mut analysis = URLAnalysis {
            total_length: self.input.len(),
            encoded_length: 0,
            special_chars: 0,
            domains: 0,
            paths: 0,
            queries: 0,
        };

        analysis.encoded_length = self.encode().len();

        for c in self.input.chars() {
            if !matches!(c, 'A'..='Z' | 'a'..='z' | '0'..='9' | '-' | '_' | '.' | '~' | '/' | '?' | '&' | '=' | ':') {
                analysis.special_chars += 1;
            }
        }

        analysis.domains = self.input.matches("://").count();
        analysis.paths = self.input.matches('/').count();
        analysis.queries = self.input.matches('?').count();

        analysis
    }

    /// Extract URL components
    fn extract_components(&self) -> Vec<String> {
        let mut components = Vec::new();

        if let Some(protocol_end) = self.input.find("://") {
            let protocol = &self.input[..protocol_end];
            components.push(format!("Protocol: {}", protocol));

            let rest = &self.input[protocol_end + 3..];

            if let Some(slash_pos) = rest.find('/') {
                let domain = &rest[..slash_pos];
                components.push(format!("Domain: {}", domain));

                let path_and_query = &rest[slash_pos..];
                if let Some(query_pos) = path_and_query.find('?') {
                    components.push(format!("Path: {}", &path_and_query[..query_pos]));
                    components.push(format!("Query: {}", &path_and_query[query_pos + 1..]));
                } else {
                    components.push(format!("Path: {}", path_and_query));
                }
            } else {
                components.push(format!("Domain: {}", rest));
            }
        } else {
            components.push("URL: Not a valid URL format".to_string());
        }

        components
    }
}

/// URLAnalysis contains URL statistics
#[derive(Debug)]
struct URLAnalysis {
    total_length: usize,
    encoded_length: usize,
    special_chars: usize,
    domains: usize,
    paths: usize,
    queries: usize,
}

impl URLAnalysis {
    fn report(&self) -> String {
        format!(
            "URL Analysis Report\n\
             ====================\n\
             Original Length: {}\n\
             Encoded Length: {}\n\
             Expansion Ratio: {:.2}%\n\
             Special Characters: {}\n\
             Domains Found: {}\n\
             Paths Found: {}\n\
             Queries Found: {}\n",
            self.total_length,
            self.encoded_length,
            ((self.encoded_length as f64 - self.total_length as f64) / self.total_length as f64) * 100.0,
            self.special_chars,
            self.domains,
            self.paths,
            self.queries
        )
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: url_encoder '<url_or_text>' [encode|decode|analyze]");
        process.exit(1);
    }

    let input = &args[1];
    let operation = if args.len() > 2 { &args[2] } else { "encode" };

    let encoder = URLEncoder::new(input.to_string());

    match operation {
        "encode" => {
            let encoded = encoder.encode();
            println!("Encoded: {}", encoded);
        }
        "decode" => {
            match encoder.decode() {
                Ok(decoded) => println!("Decoded: {}", decoded),
                Err(e) => {
                    eprintln!("Error: {}", e);
                    process::exit(1);
                }
            }
        }
        "analyze" => {
            let analysis = encoder.analyze();
            println!("{}", analysis.report());

            let components = encoder.extract_components();
            println!("\nURL Components:");
            for component in components {
                println!("  {}", component);
            }
        }
        _ => {
            eprintln!("Unknown operation: {}. Use 'encode', 'decode', or 'analyze'", operation);
            process::exit(1);
        }
    }
}
