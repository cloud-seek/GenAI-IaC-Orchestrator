import pytest
from src.models.project import Project

def test_create_project():
    project = Project(
        name="test-project",
        description="A test project",
        cloud_provider="aws",
        llm_provider="gemini",
        llm_api_key="test-api-key",
        system_prompt="You are a helpful assistant."
    )
    assert project.name == "test-project"
    assert project.cloud_provider == "aws"
    assert project.llm_api_key == "test-api-key"

def test_project_to_dict():
    project = Project(
        name="test-project-dict",
        description="Another test project",
        cloud_provider="gcp",
        llm_provider="openai",
        llm_api_key="another-test-key"
    )
    project_dict = project.to_dict()
    assert project_dict["name"] == "test-project-dict"
    assert project_dict["cloud_provider"] == "gcp"
    assert "llm_api_key" not in project_dict # API key should not be in dict for security


