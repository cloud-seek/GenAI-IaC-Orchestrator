import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TerraformWorkflow from '../TerraformWorkflow';

// Mock de fetch para simular llamadas a la API
global.fetch = jest.fn();

describe('TerraformWorkflow', () => {
  const mockProject = {
    id: 1,
    name: 'test-project',
    git_repo_url: 'https://github.com/test/repo.git',
  };

  const mockPrompt = {
    id: 'prompt-123',
    terraform_code: 'resource "aws_instance" "test" {}',
    user_prompt: 'create an ec2 instance',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders initial processing state', () => {
    render(<TerraformWorkflow selectedProject={mockProject} prompt={mockPrompt} />);
    expect(screen.getByText('Procesando')).toBeInTheDocument();
    expect(screen.getByText('Generando código Terraform con IA')).toBeInTheDocument();
  });

  test('transitions to plan state on successful plan generation', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        plan_id: 'plan-456',
        has_changes: true,
        plan_output: 'Terraform plan output details',
      }),
    });

    render(<TerraformWorkflow selectedProject={mockProject} prompt={mockPrompt} />);

    await waitFor(() => {
      expect(screen.getByText('Plan Generado')).toBeInTheDocument();
      expect(screen.getByText('Revisión del plan de ejecución')).toBeInTheDocument();
      expect(screen.getByText('Cambios detectados')).toBeInTheDocument();
    });
  });

  test('shows error state on failed plan generation', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({
        success: false,
        error: 'Failed to generate plan',
      }),
    });

    render(<TerraformWorkflow selectedProject={mockProject} prompt={mockPrompt} />);

    await waitFor(() => {
      expect(screen.getByText('Failed to generate plan')).toBeInTheDocument();
      expect(screen.getByText('error')).toBeInTheDocument();
    });
  });

  test('approves plan and transitions to approval state', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        plan_id: 'plan-456',
        has_changes: true,
        plan_output: 'Terraform plan output details',
      }),
    }).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
      }),
    });

    render(<TerraformWorkflow selectedProject={mockProject} prompt={mockPrompt} />);

    await waitFor(() => {
      expect(screen.getByText('Plan Generado')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Aprobar Plan'));

    await waitFor(() => {
      expect(screen.getByText('Plan Aprobado')).toBeInTheDocument();
      expect(screen.getByText('El plan ha sido aprobado y está listo para aplicarse')).toBeInTheDocument();
    });
  });

  test('applies plan and transitions to complete state', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        plan_id: 'plan-456',
        has_changes: true,
        plan_output: 'Terraform plan output details',
      }),
    }).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
      }),
    }).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        output: 'Apply successful output',
      }),
    });

    render(<TerraformWorkflow selectedProject={mockProject} prompt={mockPrompt} />);

    await waitFor(() => {
      expect(screen.getByText('Plan Generado')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Aprobar Plan'));

    await waitFor(() => {
      expect(screen.getByText('Plan Aprobado')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Aplicar Cambios'));

    await waitFor(() => {
      expect(screen.getByText('Cambios Aplicados Exitosamente')).toBeInTheDocument();
      expect(screen.getByText('Apply successful output')).toBeInTheDocument();
    });
  });
});

  test('syncs with Git if git_repo_url is present', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        plan_id: 'plan-456',
        has_changes: true,
        plan_output: 'Terraform plan output details',
      }),
    }).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
      }),
    }).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        output: 'Apply successful output',
      }),
    }).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}), // Mock for git sync
    });

    render(<TerraformWorkflow selectedProject={mockProject} prompt={mockPrompt} />);

    await waitFor(() => {
      expect(screen.getByText('Plan Generado')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Aprobar Plan'));

    await waitFor(() => {
      expect(screen.getByText('Plan Aprobado')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Aplicar Cambios'));

    await waitFor(() => {
      expect(screen.getByText('Cambios Aplicados Exitosamente')).toBeInTheDocument();
      expect(screen.getByText('Cambios sincronizados con Git')).toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalledWith('/api/git/sync-terraform', expect.any(Object));
  });
});
});

