#!/usr/bin/perl
use strict;
use warnings;
use Carp;

=head1 NAME
regex_tester.pl - Advanced regular expression testing and pattern matching tool

=head1 SYNOPSIS
  regex_tester.pl '<text>' '<pattern>'

=head1 DESCRIPTION
Comprehensive regex testing tool that validates patterns, finds matches,
extracts groups, and provides detailed analysis.
=cut

package RegexTester;

sub new {
    my ($class, $text, $pattern) = @_;
    my $self = {
        text => $text,
        pattern => $pattern,
        matches => [],
        errors => [],
        stats => {
            total_matches => 0,
            pattern_length => 0,
            text_length => 0,
            groups => 0,
        }
    };
    bless $self, $class;
    return $self;
}

sub validate_pattern {
    my ($self) = @_;

    eval {
        qr/$self->{pattern}/;
    };

    if ($@) {
        push @{$self->{errors}}, "Invalid regex: $@";
        return 0;
    }

    $self->{stats}{pattern_length} = length($self->{pattern});
    $self->{stats}{text_length} = length($self->{text});

    return 1;
}

sub find_matches {
    my ($self) = @_;

    return unless $self->validate_pattern();

    my $pattern = $self->{pattern};
    my @matches;

    while ($self->{text} =~ /($pattern)/g) {
        push @matches, {
            match => $1,
            position => $-[0],
            end_position => $+[0],
            length => length($1)
        };
    }

    $self->{matches} = \@matches;
    $self->{stats}{total_matches} = scalar(@matches);

    return $self;
}

sub find_with_groups {
    my ($self) = @_;

    return unless $self->validate_pattern();

    my $pattern = $self->{pattern};
    my @grouped_matches;

    while ($self->{text} =~ /($pattern)/g) {
        my %groups = ();
        $groups{0} = $1;

        for (my $i = 1; $i <= 9; $i++) {
            if (defined ${$i}) {
                $groups{$i} = ${$i};
            }
        }

        push @grouped_matches, \%groups;
    }

    return \@grouped_matches;
}

sub extract_unique {
    my ($self) = @_;

    return [] unless @{$self->{matches}};

    my %unique;
    foreach my $match (@{$self->{matches}}) {
        $unique{$match->{match}}++;
    }

    return [keys %unique];
}

sub analyze_pattern {
    my ($self) = @_;

    return unless $self->validate_pattern();

    my $pattern = $self->{pattern};
    my $analysis = {
        is_greedy => ($pattern =~ /\*|\+(?!\?)/) ? 1 : 0,
        has_groups => ($pattern =~ /\(/) ? 1 : 0,
        has_classes => ($pattern =~ /\[/) ? 1 : 0,
        has_anchors => ($pattern =~ /[\^$]/) ? 1 : 0,
        has_alternation => ($pattern =~ /\|/) ? 1 : 0,
        complexity => length($pattern)
    };

    return $analysis;
}

sub split_by_pattern {
    my ($self) = @_;

    return unless $self->validate_pattern();

    my $pattern = $self->{pattern};
    my @parts = split /$pattern/, $self->{text};

    return \@parts;
}

sub replace_pattern {
    my ($self, $replacement) = @_;

    return unless $self->validate_pattern();

    my $pattern = $self->{pattern};
    my $modified = $self->{text};
    my $count = ($modified =~ s/$pattern/$replacement/g);

    return {
        original => $self->{text},
        modified => $modified,
        replacements => $count
    };
}

sub report {
    my ($self) = @_;

    my @lines;
    push @lines, "Regex Analysis Report";
    push @lines, "====================";
    push @lines, "";

    if (@{$self->{errors}}) {
        push @lines, "Errors:";
        push @lines, "  $_" foreach @{$self->{errors}};
        return join("\n", @lines);
    }

    push @lines, sprintf("Pattern: %s", $self->{pattern});
    push @lines, sprintf("Text Length: %d characters", $self->{stats}{text_length});
    push @lines, sprintf("Pattern Length: %d characters", $self->{stats}{pattern_length});
    push @lines, "";

    my $analysis = $self->analyze_pattern();
    push @lines, "Pattern Analysis:";
    push @lines, sprintf("  Greedy: %s", $analysis->{is_greedy} ? "Yes" : "No");
    push @lines, sprintf("  Has Groups: %s", $analysis->{has_groups} ? "Yes" : "No");
    push @lines, sprintf("  Has Character Classes: %s", $analysis->{has_classes} ? "Yes" : "No");
    push @lines, sprintf("  Has Anchors: %s", $analysis->{has_anchors} ? "Yes" : "No");
    push @lines, sprintf("  Has Alternation: %s", $analysis->{has_alternation} ? "Yes" : "No");
    push @lines, sprintf("  Complexity Score: %d", $analysis->{complexity});
    push @lines, "";

    push @lines, sprintf("Matches Found: %d", $self->{stats}{total_matches});

    if (@{$self->{matches}} > 0) {
        my $unique = $self->extract_unique();
        push @lines, sprintf("Unique Matches: %d", scalar(@$unique));

        my %freq;
        foreach my $match (@{$self->{matches}}) {
            $freq{$match->{match}}++;
        }

        push @lines, "";
        push @lines, "Top Matches:";
        my @sorted = sort { $freq{$b} <=> $freq{$a} } keys %freq;
        for (my $i = 0; $i < 5 && $i < @sorted; $i++) {
            push @lines, sprintf("  %s: %d times", $sorted[$i], $freq{$sorted[$i]});
        }
    }

    return join("\n", @lines);
}

package main;

sub main {
    if (@ARGV < 2) {
        print "Usage: regex_tester.pl '<text>' '<pattern>'\n";
        exit 1;
    }

    my ($text, $pattern) = @ARGV;

    my $tester = RegexTester->new($text, $pattern);
    $tester->find_matches();

    print $tester->report();
    print "\n";
}

main() unless caller();
