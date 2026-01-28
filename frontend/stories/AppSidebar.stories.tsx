import type { Meta, StoryObj } from '@storybook/react';
import { AppSidebar } from '@/components/layout/AppSidebar';

const meta = {
  title: 'Fluent UI/Layout/AppSidebar',
  component: AppSidebar,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof AppSidebar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex h-screen bg-neutral-900">
      <AppSidebar />
      <div className="flex-1 p-8 text-white">
        <h1 className="text-2xl font-bold">Main Content Area</h1>
        <p className="mt-4 text-gray-400">The sidebar sits to the left. Try collapsing it using the brand icon.</p>
      </div>
    </div>
  ),
};
