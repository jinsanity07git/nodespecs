#!/usr/bin/env python3
"""
Git Mermaid Graph Generator

This script generates a mermaid gitGraph visualization from git commits since a specified tag.
It analyzes the git repository structure, commit history, and branch relationships to create
a comprehensive visualization.

Usage:
    python git_mermaid_generator.py --tag v1.1.1 --exclude-branches "refs/stash,origin/HEAD"
    python git_mermaid_generator.py --repo-dir "C:\Projects\tdm23_sr" --tag v1.0.0
    python git_mermaid_generator.py  # Uses defaults: tag=v1.1.1, current directory
"""

import argparse

from .collector import GitCollector
from .renderer import GitMermaidRenderer


def main():
    """Main function to run the script with command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate mermaid gitGraph visualization from git commits since a specified tag"
    )
    parser.add_argument(
        "--tag", default="v1.1.1", help="Git tag to use as starting point (default: v1.1.1)"
    )
    parser.add_argument(
        "--exclude-branches", help="Comma-separated list of branch patterns to exclude"
    )
    parser.add_argument(
        "--output", help="Output filename (default: git_commits_since_<tag>.md)"
    )
    parser.add_argument(
        "--repo-dir", help="Path to git repository directory (default: current directory)"
    )

    args = parser.parse_args()

    # Parse excluded branches
    exclude_branches = []
    if args.exclude_branches:
        exclude_branches = [b.strip() for b in args.exclude_branches.split(",")]

    # Add default exclusions
    exclude_branches.extend(["refs/stash", "origin/HEAD"])

    try:
        collector = GitCollector(
            base_tag=args.tag,
            exclude_branches=exclude_branches,
            repo_dir=args.repo_dir,
        )

        if not collector.verify_git_repository():
            raise ValueError(f"Directory '{collector.repo_dir}' is not a valid git repository")

        if not collector.verify_tag_exists():
            raise ValueError(f"Tag '{collector.base_tag}' does not exist in the repository")

        collector.branches = collector.get_all_branches()
        collector.commits = collector.get_commits_since_tag()
        collector.merge_commits = collector.get_merge_commits()

        renderer = GitMermaidRenderer(
            base_tag=collector.base_tag,
            commits=collector.commits,
            branches=collector.branches,
            merge_commits=collector.merge_commits,
        )

        content = renderer.build_report()
        filename = args.output or f"git_commits_since_{collector.base_tag.replace('.', '_')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Mermaid gitGraph visualization saved to: {filename}")

        # Print some basic stats
        print(f"\nAnalysis Summary:")
        print(f"- Repository: {collector.repo_dir}")
        print(f"- Base tag: {args.tag}")
        print(f"- Total commits analyzed: {len(collector.commits)}")
        print(f"- Active branches: {len(collector.branches)}")
        print(f"- Excluded branch patterns: {', '.join(exclude_branches)}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
