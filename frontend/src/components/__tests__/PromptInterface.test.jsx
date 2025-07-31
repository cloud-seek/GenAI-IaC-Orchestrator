import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PromptInterface from '../PromptInterface';

// Mock del componente TerraformWorkflow
jest.mock('../TerraformWorkflow', () => {
  return function MockTerraformWorkflow({ selectedProject, prompt, onWorkflowComplete }) {
    return (
      <div data-testid="terraform-workflow">
        Terraform Workflow Mock
        <button onClick={onWorkflowComplete}>Complete Workflow</button>
      </div>
    );
  };
});

// Mock de fetch para simular llamadas a la API
global.fetch = jest.fn();

describe('PromptInterface', () => {
  const mockProjects = [
    {
      id: 1,
      name: 'Project A',
      cloud_provider: 'aws',
      llm_api_key: 'test-key-a',
    },
    {
      id: 2,
      name: 'Project B',
      cloud_provider: 'gcp',
      llm_api_key: 'test-key-b',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockProjects),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
  });

  test('renders prompt interface with project selector and textarea', async () => {
    render(<PromptInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('Selecciona un proyecto')).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText(/describe tu infraestructura/i)).toBeInTheDocument();
  });

  test('allows user to select a project and type in textarea', async () => {
    render(<PromptInterface />);
    
    await waitFor(() => {
      fireEvent.mouseDown(screen.getByText('Selecciona un proyecto'));
    });
    fireEvent.click(await screen.findByText('Project A (aws)'));

    const textarea = screen.getByPlaceholderText(/describe tu infraestructura/i);
    fireEvent.change(textarea, { target: { value: 'Crear una instancia EC2' } });
    
    expect(textarea.value).toBe('Crear una instancia EC2');
  });

  test('submits prompt and shows TerraformWorkflow', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockProjects),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        prompt_id: 'new-prompt-123',
        analysis: 'Analysis result',
        terraform_code: 'resource "aws_instance" "test" {}',
      }),
    });

    render(<PromptInterface />);

    await waitFor(() => {
      fireEvent.mouseDown(screen.getByText('Selecciona un proyecto'));
    });
    fireEvent.click(await screen.findByText('Project A (aws)'));

    const textarea = screen.getByPlaceholderText(/describe tu infraestructura/i);
    fireEvent.change(textarea, { target: { value: 'Crear una instancia EC2' } });

    fireEvent.click(screen.getByText('Enviar Prompt'));

    await waitFor(() => {
      expect(screen.getByTestId('terraform-workflow')).toBeInTheDocument();
    });
  });

  test('hides TerraformWorkflow after workflow completion', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockProjects),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        prompt_id: 'new-prompt-123',
        analysis: 'Analysis result',
        terraform_code: 'resource "aws_instance" "test" {}',
      }),
    });

    render(<PromptInterface />);

    await waitFor(() => {
      fireEvent.mouseDown(screen.getByText('Selecciona un proyecto'));
    });
    fireEvent.click(await screen.findByText('Project A (aws)'));

    const textarea = screen.getByPlaceholderText(/describe tu infraestructura/i);
    fireEvent.change(textarea, { target: { value: 'Crear una instancia EC2' } });

    fireEvent.click(screen.getByText('Enviar Prompt'));

    await waitFor(() => {
      expect(screen.getByTestId('terraform-workflow')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Complete Workflow'));

    await waitFor(() => {
      expect(screen.queryByTestId('terraform-workflow')).not.toBeInTheDocument();
    });
  });
});


