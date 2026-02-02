import type { Meta, StoryObj } from '@storybook/react';
import { Progress } from "@/components/ui/progress"

const meta: Meta<typeof Progress> = {
  title: 'Fluent UI/Primitives/Progress',
  component: Progress,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof Progress>;

export const Default: Story = {
    args: {
        value: 60,
        className: "w-[60%]"
    }
};
