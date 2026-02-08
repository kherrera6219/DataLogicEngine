import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

const meta = {
  title: 'Fluent UI/Primitives/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Standard Button',
    variant: 'default',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Ghost Action',
    variant: 'ghost',
  },
};

export const WithIcon: Story = {
  render: (args) => (
    <Button {...args}>
      <Plus className="mr-2 h-4 w-4" /> New Item
    </Button>
  ),
  args: {
    variant: 'default',
  },
};

export const FluentShadow: Story = {
  args: {
    children: 'High Elevation',
    className: 'shadow-lg shadow-blue-900/20 bg-blue-600 hover:bg-blue-700',
  },
};
