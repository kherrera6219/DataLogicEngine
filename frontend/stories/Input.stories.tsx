import type { Meta, StoryObj } from '@storybook/react';
import { Input } from '@/components/ui/input';

const meta = {
  title: 'Fluent UI/Primitives/Input',
  component: Input,
  tags: ['autodocs'],
  argTypes: {
    type: { control: 'select', options: ['text', 'password', 'email', 'number', 'file'] },
    disabled: { control: 'boolean' },
  },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: 'Type something...',
  },
};

export const WithValue: Story = {
  args: {
    defaultValue: 'Pre-filled text',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    placeholder: 'Disabled input',
  },
};

export const File: Story = {
  args: {
    type: 'file',
  },
};

export const Password: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter secure password',
  },
};
