"""
Git integrations for GitHub and GitLab.
"""
from typing import Optional, Dict, Any
import git
from pathlib import Path
import httpx
from .config import get_config, get_settings
from .logging import get_logger

logger = get_logger(__name__)


class GitIntegration:
    """Base class for Git integrations."""

    def __init__(self):
        self.config = get_config()
        self.settings = get_settings()

    def init_repo(self, workspace_path: str, remote_url: Optional[str] = None) -> git.Repo:
        """Initialize a Git repository in the workspace."""
        workspace = Path(workspace_path)

        try:
            # Check if repo already exists
            repo = git.Repo(workspace)
            logger.info("Git repo already exists", path=workspace_path)
        except git.exc.InvalidGitRepositoryError:
            # Initialize new repo
            repo = git.Repo.init(workspace)
            logger.info("Initialized new Git repo", path=workspace_path)

            # Add remote if provided
            if remote_url:
                try:
                    repo.create_remote("origin", remote_url)
                    logger.info("Added remote origin", url=remote_url)
                except git.exc.GitCommandError as e:
                    logger.warning("Failed to add remote", error=str(e))

        return repo

    def commit_changes(
        self,
        repo: git.Repo,
        message: str,
        files: Optional[list] = None
    ) -> Optional[git.Commit]:
        """Commit changes to the repository."""
        try:
            # Add files
            if files:
                repo.index.add(files)
            else:
                repo.git.add(A=True)  # Add all changes

            # Check if there are changes to commit
            if not repo.index.diff("HEAD") and not repo.untracked_files:
                logger.info("No changes to commit")
                return None

            # Commit
            commit = repo.index.commit(message)
            logger.info("Committed changes", commit_sha=commit.hexsha[:8], message=message)
            return commit

        except Exception as e:
            logger.error("Failed to commit changes", error=str(e))
            return None

    def push_changes(self, repo: git.Repo, branch: str = "main") -> bool:
        """Push changes to remote."""
        try:
            origin = repo.remote("origin")
            origin.push(branch)
            logger.info("Pushed changes to remote", branch=branch)
            return True
        except Exception as e:
            logger.error("Failed to push changes", error=str(e))
            return False


class GitHubIntegration(GitIntegration):
    """GitHub-specific integration."""

    def __init__(self):
        super().__init__()
        self.api_base = "https://api.github.com"
        self.token = getattr(self.settings, "github_token", None)

    async def create_repository(
        self,
        name: str,
        description: str,
        private: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Create a new GitHub repository."""
        if not self.token:
            logger.warning("GitHub token not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/user/repos",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={
                        "name": name,
                        "description": description,
                        "private": private,
                        "auto_init": False,
                    }
                )

                if response.status_code == 201:
                    repo_data = response.json()
                    logger.info("Created GitHub repository", name=name)
                    return repo_data
                else:
                    logger.error("Failed to create GitHub repository", status=response.status_code)
                    return None

        except Exception as e:
            logger.error("GitHub API error", error=str(e))
            return None

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Optional[Dict[str, Any]]:
        """Create a pull request."""
        if not self.token:
            logger.warning("GitHub token not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/repos/{owner}/{repo}/pulls",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={
                        "title": title,
                        "body": body,
                        "head": head,
                        "base": base,
                    }
                )

                if response.status_code == 201:
                    pr_data = response.json()
                    logger.info("Created pull request", number=pr_data["number"])
                    return pr_data
                else:
                    logger.error("Failed to create pull request", status=response.status_code)
                    return None

        except Exception as e:
            logger.error("GitHub API error", error=str(e))
            return None


class GitLabIntegration(GitIntegration):
    """GitLab-specific integration."""

    def __init__(self):
        super().__init__()
        self.api_base = "https://gitlab.com/api/v4"
        self.token = getattr(self.settings, "gitlab_token", None)

    async def create_project(
        self,
        name: str,
        description: str,
        visibility: str = "private"
    ) -> Optional[Dict[str, Any]]:
        """Create a new GitLab project."""
        if not self.token:
            logger.warning("GitLab token not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/projects",
                    headers={
                        "PRIVATE-TOKEN": self.token,
                    },
                    json={
                        "name": name,
                        "description": description,
                        "visibility": visibility,
                        "initialize_with_readme": False,
                    }
                )

                if response.status_code == 201:
                    project_data = response.json()
                    logger.info("Created GitLab project", name=name)
                    return project_data
                else:
                    logger.error("Failed to create GitLab project", status=response.status_code)
                    return None

        except Exception as e:
            logger.error("GitLab API error", error=str(e))
            return None

    async def create_merge_request(
        self,
        project_id: int,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str = "main"
    ) -> Optional[Dict[str, Any]]:
        """Create a merge request."""
        if not self.token:
            logger.warning("GitLab token not configured")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/projects/{project_id}/merge_requests",
                    headers={
                        "PRIVATE-TOKEN": self.token,
                    },
                    json={
                        "title": title,
                        "description": description,
                        "source_branch": source_branch,
                        "target_branch": target_branch,
                    }
                )

                if response.status_code == 201:
                    mr_data = response.json()
                    logger.info("Created merge request", iid=mr_data["iid"])
                    return mr_data
                else:
                    logger.error("Failed to create merge request", status=response.status_code)
                    return None

        except Exception as e:
            logger.error("GitLab API error", error=str(e))
            return None


def get_git_integration(provider: str = "github") -> Optional[GitIntegration]:
    """Get a Git integration instance."""
    config = get_config()

    if provider == "github" and config.git.github_enabled:
        return GitHubIntegration()
    elif provider == "gitlab" and config.git.gitlab_enabled:
        return GitLabIntegration()
    else:
        return GitIntegration()  # Base implementation
