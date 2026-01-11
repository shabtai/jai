#!/usr/bin/env ruby
# frozen_string_literal: true

require 'date'
require 'time'

# LogParser analyzes log files and extracts statistics
class LogParser
  LOG_PATTERNS = {
    apache: /^(\S+) \S+ \S+ \[(.*?)\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+)/,
    syslog: /^(\S+ \S+ \S+) (\S+) (\S+)\[(\d+)\]: (.*)$/,
    generic: /^\[(.*?)\] (\S+): (.*)$/,
    timestamp: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
  }

  def initialize(log_content)
    @log_content = log_content
    @lines = log_content.split("\n").reject(&:empty?)
    @stats = {
      total_lines: 0,
      parsed_lines: 0,
      error_lines: 0,
      entries: [],
      timestamps: [],
      methods: Hash.new(0),
      status_codes: Hash.new(0),
      hosts: Hash.new(0),
      errors: []
    }
  end

  def parse
    @lines.each_with_index do |line, index|
      case detect_format(line)
      when :apache
        parse_apache(line)
      when :syslog
        parse_syslog(line)
      when :generic
        parse_generic(line)
      else
        @stats[:error_lines] += 1
      end
      @stats[:total_lines] += 1
    end

    @stats[:parsed_lines] = @stats[:total_lines] - @stats[:error_lines]
    self
  end

  private

  def detect_format(line)
    return :apache if line.match?(LOG_PATTERNS[:apache])
    return :syslog if line.match?(LOG_PATTERNS[:syslog])
    return :generic if line.match?(LOG_PATTERNS[:generic])
    :unknown
  end

  def parse_apache(line)
    match = line.match(LOG_PATTERNS[:apache])
    return unless match

    entry = {
      host: match[1],
      timestamp: match[2],
      method: match[3],
      path: match[4],
      protocol: match[5],
      status: match[6].to_i,
      bytes: match[7].to_i
    }

    @stats[:entries] << entry
    @stats[:hosts][entry[:host]] += 1
    @stats[:methods][entry[:method]] += 1
    @stats[:status_codes][entry[:status]] += 1
    @stats[:timestamps] << entry[:timestamp]
  end

  def parse_syslog(line)
    match = line.match(LOG_PATTERNS[:syslog])
    return unless match

    entry = {
      timestamp: match[1],
      host: match[2],
      process: match[3],
      pid: match[4].to_i,
      message: match[5]
    }

    @stats[:entries] << entry
    @stats[:hosts][entry[:host]] += 1
    @stats[:timestamps] << entry[:timestamp]
  end

  def parse_generic(line)
    match = line.match(LOG_PATTERNS[:generic])
    return unless match

    entry = {
      timestamp: match[1],
      level: match[2],
      message: match[3]
    }

    @stats[:entries] << entry
    @stats[:timestamps] << entry[:timestamp]
  end

  def report
    lines = []
    lines << "Log Analysis Report"
    lines << "==================="
    lines << ""
    lines << "Summary:"
    lines << "  Total Lines: #{@stats[:total_lines]}"
    lines << "  Parsed Lines: #{@stats[:parsed_lines]}"
    lines << "  Error Lines: #{@stats[:error_lines]}"
    lines << "  Unique Entries: #{@stats[:entries].length}"
    lines << ""

    unless @stats[:methods].empty?
      lines << "HTTP Methods:"
      @stats[:methods].each do |method, count|
        lines << "  #{method}: #{count}"
      end
      lines << ""
    end

    unless @stats[:status_codes].empty?
      lines << "HTTP Status Codes:"
      @stats[:status_codes].sort.each do |code, count|
        lines << "  #{code}: #{count}"
      end
      lines << ""
    end

    unless @stats[:hosts].empty?
      lines << "Top Hosts (by request count):"
      @stats[:hosts].sort_by { |_h, c| -c }.first(10).each do |host, count|
        lines << "  #{host}: #{count}"
      end
      lines << ""
    end

    if @stats[:entries].any? && @stats[:entries].first.is_a?(Hash) && @stats[:entries].first[:bytes]
      total_bytes = @stats[:entries].map { |e| e[:bytes] || 0 }.sum
      avg_bytes = total_bytes / [@stats[:entries].length, 1].max
      lines << "Bandwidth:"
      lines << "  Total Bytes: #{total_bytes}"
      lines << "  Average Bytes per Request: #{avg_bytes}"
      lines << ""
    end

    lines << "Timestamp Range:"
    lines << "  First: #{@stats[:timestamps].first || 'N/A'}"
    lines << "  Last: #{@stats[:timestamps].last || 'N/A'}"

    lines.join("\n")
  end

  def stats
    @stats
  end
end

def main
  if ARGV.length < 1
    puts "Usage: log_parser.rb '<log_content>'"
    exit 1
  end

  log_content = ARGV[0]

  begin
    parser = LogParser.new(log_content)
    parser.parse
    puts parser.report
  rescue StandardError => e
    puts "Error parsing logs: #{e.message}"
    exit 1
  end
end

main if __FILE__ == $PROGRAM_NAME
