import type { Meta, StoryObj } from '@storybook/react';
import { Select, SelectItem } from '@/components/ui/select';

const meta = {
  title: 'Fluent UI/Primitives/Select',
  component: Select,
  tags: ['autodocs'],
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Select className="w-[180px]" defaultValue="apple">
      <SelectItem value="apple">Apple</SelectItem>
      <SelectItem value="banana">Banana</SelectItem>
      <SelectItem value="blueberry">Blueberry</SelectItem>
      <SelectItem value="grapes">Grapes</SelectItem>
    </Select>
  ),
};

export const Disabled: Story = {
  render: () => (
    <Select className="w-[180px]" disabled>
      <SelectItem value="apple">Apple</SelectItem>
    </Select>
  ),
};
