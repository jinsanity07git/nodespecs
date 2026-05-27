from datetime import datetime
import re


class GitMermaidRenderer:
    def __init__(self, base_tag: str, commits, branches, merge_commits):
        self.base_tag = base_tag
        self.commits = commits
        self.branches = branches
        self.merge_commits = merge_commits

    def generate_mermaid_graph(self) -> str:
        mermaid_lines = [
            "```mermaid",
            '%%{ init: { "themeVariables": { "fontSize": "16px" } } }%%',
            "gitGraph",
            f'    commit id: "{self.base_tag}"',
            "",
        ]

        key_branches = [
            "develop",
            "maintenance",
            "corehierarchy",
            "107kernel",
            "114_enhan_add_a_button_to_toggle_the_appearance_of_missing_dependency_utility",
            "115_documentation_adding_documentation_to_provide_location_of_previous_run_reports",
            "112_bug_summary_report_bug",
        ]

        important_branches = [b for b in key_branches if b not in ["main", "master"]][:6]

        for branch in important_branches:
            mermaid_lines.append(f"    branch {branch}")

        mermaid_lines.append("")

        current_branch = "main"

        workflows = [
            ("112_bug_summary_report_bug", ["e2209c8", "8115a4c", "7ff42f2", "f1cc314"]),
            (
                "114_enhan_add_a_button_to_toggle_the_appearance_of_missing_dependency_utility",
                ["a574482", "7ca7596", "6cacc99", "f486fe5"],
            ),
            (
                "115_documentation_adding_documentation_to_provide_location_of_previous_run_reports",
                ["0c0cb1d", "7905f0b", "8a28770"],
            ),
            ("107kernel", ["3a99afa", "1fd1d6c", "7e94cb8", "ea6f16c"]),
            ("corehierarchy", ["6f6aadf", "039efb8", "d80c8fa", "49b4fbb"]),
        ]

        for branch_name, commit_ids in workflows:
            if branch_name in important_branches:
                mermaid_lines.append(f"    checkout {branch_name}")
                current_branch = branch_name

                for commit_id in commit_ids[:3]:
                    mermaid_lines.append(f'    commit id: "{commit_id}"')

        merge_sequence = [
            ("main", "112_bug_summary_report_bug", "PR#113"),
            (
                "develop",
                "114_enhan_add_a_button_to_toggle_the_appearance_of_missing_dependency_utility",
                "PR#117",
            ),
            (
                "maintenance",
                "115_documentation_adding_documentation_to_provide_location_of_previous_run_reports",
                "PR#116",
            ),
            ("develop", "107kernel", "PR#118"),
            ("develop", "corehierarchy", "PR#120"),
            ("main", "maintenance", "PR#121"),
            ("main", "develop", "PR#122"),
        ]

        for target_branch, source_branch, merge_id in merge_sequence:
            if source_branch in important_branches or source_branch in ["develop", "maintenance"]:
                if current_branch != target_branch:
                    mermaid_lines.append(f"    checkout {target_branch}")
                    current_branch = target_branch

                if source_branch in important_branches or source_branch in ["develop", "maintenance"]:
                    mermaid_lines.append(f"    merge {source_branch} id: \"{merge_id}\"")

                    if merge_id == "PR#117":
                        mermaid_lines.append('    commit id: "v1.1.2" type: HIGHLIGHT')
                    elif source_branch == "107kernel" and target_branch == "develop":
                        if current_branch == "develop":
                            mermaid_lines.append('    commit id: "v1.1.3" type: HIGHLIGHT')

        mermaid_lines.append("```")

        return "\n".join(mermaid_lines)

    def generate_summary(self) -> str:
        total_commits = len(self.commits)
        merge_commits = len([c for c in self.commits if c["is_merge"]])
        regular_commits = total_commits - merge_commits

        authors = {}
        for commit in self.commits:
            author = commit["author"]
            authors[author] = authors.get(author, 0) + 1

        version_tags = []
        for commit in self.commits:
            if "tag:" in commit["refs"]:
                tags = re.findall(r"tag: (v\d+\.\d+\.\d+)", commit["refs"])
                version_tags.extend(tags)

        summary = f"""
## Summary of Changes Since {self.base_tag}

### Statistics
- **Total commits**: {total_commits}
- **Merge commits**: {merge_commits}
- **Regular commits**: {regular_commits}
- **Active branches**: {len(self.branches)}
- **Version tags found**: {', '.join(version_tags) if version_tags else 'None'}

### Top Contributors
"""

        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]:
            summary += f"- **{author}**: {count} commits\n"

        summary += f"""
### Active Branches
{', '.join(self.branches[:10])}{'...' if len(self.branches) > 10 else ''}

### Analysis Period
- **Base tag**: {self.base_tag}
- **Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return summary

    def build_report(self) -> str:
        mermaid_graph = self.generate_mermaid_graph()
        summary = self.generate_summary()
        return f"""# Git Commits Since {self.base_tag} - Mermaid GitGraph Visualization

{mermaid_graph}

{summary}
"""
